#!/usr/bin/env python3
"""
Anthropic Message Batches API evaluation for ThermoQA.

50% cost reduction vs. sequential API calls, with parallel processing.

Usage:
    python scripts/run_batch_anthropic.py --submit
    python scripts/run_batch_anthropic.py --status
    python scripts/run_batch_anthropic.py --collect
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone

# Ensure project root is on path when running as script
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evaluation.extractor import extract_properties, strip_thinking_tags
from evaluation.runner import SYSTEM_PROMPT
from evaluation.scorer import load_questions, score_dataset, score_question

DEFAULT_QUESTIONS = "data/tier1_properties/questions.jsonl"
DEFAULT_OUTPUT_DIR = "results/anthropic"
BATCH_ID_FILE = "batch_id.txt"
MODEL = "claude-opus-4-6"


def submit(questions_path: str, output_dir: str, model: str):
    """Build and submit a batch of requests to the Anthropic Batches API."""
    import anthropic

    questions = load_questions(questions_path)
    print(f"Loaded {len(questions)} questions from {questions_path}")

    requests = []
    for q in questions:
        requests.append({
            "custom_id": q["id"],
            "params": {
                "model": model,
                "max_tokens": 64000,
                "thinking": {"type": "adaptive"},
                "system": SYSTEM_PROMPT,
                "messages": [{"role": "user", "content": q["question"]}],
            },
        })

    client = anthropic.Anthropic()
    print(f"Submitting batch of {len(requests)} requests (model: {model})...")
    batch = client.messages.batches.create(requests=requests)

    os.makedirs(output_dir, exist_ok=True)
    batch_id_path = os.path.join(output_dir, BATCH_ID_FILE)
    with open(batch_id_path, "w") as f:
        f.write(batch.id)

    print(f"Batch submitted successfully!")
    print(f"  Batch ID: {batch.id}")
    print(f"  Status:   {batch.processing_status}")
    counts = batch.request_counts
    print(f"  Requests: processing={counts.processing}, "
          f"succeeded={counts.succeeded}, errored={counts.errored}, "
          f"expired={counts.expired}, canceled={counts.canceled}")
    print(f"  Batch ID saved to {batch_id_path}")


def status(output_dir: str):
    """Check the status of a submitted batch."""
    import anthropic

    batch_id = _read_batch_id(output_dir)
    client = anthropic.Anthropic()
    batch = client.messages.batches.retrieve(batch_id)

    print(f"Batch ID: {batch.id}")
    print(f"Status:   {batch.processing_status}")
    counts = batch.request_counts
    print(f"Requests: processing={counts.processing}, "
          f"succeeded={counts.succeeded}, errored={counts.errored}, "
          f"expired={counts.expired}, canceled={counts.canceled}")
    if batch.ended_at:
        print(f"Ended at: {batch.ended_at}")


def collect(questions_path: str, output_dir: str, model: str):
    """Collect results from a completed batch, score, and write outputs."""
    import anthropic

    batch_id = _read_batch_id(output_dir)
    questions = load_questions(questions_path)
    questions_by_id = {q["id"]: q for q in questions}

    client = anthropic.Anthropic()

    # Verify batch is done
    batch = client.messages.batches.retrieve(batch_id)
    if batch.processing_status != "ended":
        print(f"Batch is not yet complete (status: {batch.processing_status})")
        counts = batch.request_counts
        print(f"  processing={counts.processing}, succeeded={counts.succeeded}, "
              f"errored={counts.errored}")
        sys.exit(1)

    print(f"Collecting results for batch {batch_id}...")
    entries = []
    errors = 0

    for result in client.messages.batches.results(batch_id):
        qid = result.custom_id
        q = questions_by_id.get(qid)
        if q is None:
            print(f"  WARNING: Unknown question ID in batch result: {qid}")
            continue

        expected_keys = list(q["expected"].keys())

        if result.result.type == "succeeded":
            message = result.result.message

            # Extract thinking and text blocks (same as AnthropicProvider._call_api)
            text_parts = []
            thinking_parts = []
            for block in message.content:
                if block.type == "thinking":
                    thinking_parts.append(block.thinking)
                elif block.type == "text":
                    text_parts.append(block.text)

            text = "\n".join(text_parts)
            thinking_text = "\n".join(thinking_parts) if thinking_parts else None
            raw = (thinking_text + "\n" + text) if thinking_text else text

            # Fallback: if text is empty but thinking exists, use thinking for extraction
            extraction_text = text if text.strip() else (thinking_text or "")
            extracted = extract_properties(extraction_text, expected_keys)
            qr = score_question(q, extracted)

            scores = []
            for pr in qr.property_results:
                scores.append({
                    "key": pr.prop_key,
                    "expected": pr.expected,
                    "extracted": pr.extracted,
                    "passed": pr.passed,
                    "error_pct": pr.error_pct,
                    "error_type": pr.error_type,
                })

            usage = message.usage
            entry = {
                "id": qid,
                "question": q["question"],
                "raw_response": raw,
                "response_text": text,
                "thinking_text": thinking_text,
                "extracted": {k: v for k, v in extracted.items()},
                "scores": scores,
                "question_score": qr.score,
                "model": model,
                "latency_s": 0.0,
                "input_tokens": getattr(usage, "input_tokens", None),
                "output_tokens": getattr(usage, "output_tokens", None),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        else:
            # errored / expired / canceled
            errors += 1
            error_msg = f"Batch result type: {result.result.type}"
            if hasattr(result.result, "error") and result.result.error:
                error_msg += f" - {result.result.error.message}"
            print(f"  ERROR {qid}: {error_msg}")

            entry = {
                "id": qid,
                "question": q["question"],
                "raw_response": "",
                "response_text": "",
                "thinking_text": None,
                "extracted": {},
                "scores": [],
                "question_score": 0.0,
                "model": model,
                "latency_s": 0.0,
                "input_tokens": None,
                "output_tokens": None,
                "error": error_msg,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        entries.append(entry)

    # Write responses
    responses_path = os.path.join(output_dir, "responses.jsonl")
    with open(responses_path, "w") as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"Wrote {len(entries)} responses to {responses_path}")

    # Build summary (replicating _build_summary logic without provider object)
    responses_for_scoring = {}
    latencies = []
    input_tokens_list = []
    output_tokens_list = []

    for entry in entries:
        responses_for_scoring[entry["id"]] = entry.get("response_text", "")
        latencies.append(entry.get("latency_s", 0))
        if entry.get("input_tokens") is not None:
            input_tokens_list.append(entry["input_tokens"])
        if entry.get("output_tokens") is not None:
            output_tokens_list.append(entry["output_tokens"])

    ds = score_dataset(questions, responses_for_scoring)

    summary = {
        "provider": "anthropic",
        "model": model,
        "batch_id": batch_id,
        "total_questions": ds.total_questions,
        "total_responses": len(entries),
        "total_properties": ds.total_properties,
        "total_correct_properties": ds.total_correct_properties,
        "property_accuracy": round(ds.property_accuracy, 4),
        "mean_question_score": round(ds.mean_question_score, 4),
        "per_category": {
            cat: {k: round(v, 4) if isinstance(v, float) else v for k, v in d.items()}
            for cat, d in ds.per_category.items()
        },
        "per_difficulty": {
            diff: {k: round(v, 4) if isinstance(v, float) else v for k, v in d.items()}
            for diff, d in ds.per_difficulty.items()
        },
        "errors": errors,
        "timing": {
            "mean_latency_s": 0,
            "min_latency_s": 0,
            "max_latency_s": 0,
            "note": "Batch API — no per-request latency available",
        },
        "tokens": {
            "total_input": sum(input_tokens_list) if input_tokens_list else None,
            "total_output": sum(output_tokens_list) if output_tokens_list else None,
            "mean_input": round(sum(input_tokens_list) / len(input_tokens_list), 1) if input_tokens_list else None,
            "mean_output": round(sum(output_tokens_list) / len(output_tokens_list), 1) if output_tokens_list else None,
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    summary_path = os.path.join(output_dir, "summary.json")
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"Wrote summary to {summary_path}")
    print()
    print(f"=== Results ===")
    print(f"  Questions:    {summary['total_questions']}")
    print(f"  Responses:    {summary['total_responses']}")
    print(f"  Errors:       {summary['errors']}")
    print(f"  Property acc: {summary['property_accuracy']:.1%}")
    print(f"  Mean score:   {summary['mean_question_score']:.1%}")
    if input_tokens_list:
        print(f"  Total tokens: {summary['tokens']['total_input']} in / "
              f"{summary['tokens']['total_output']} out")


def _read_batch_id(output_dir: str) -> str:
    """Read saved batch ID from file."""
    path = os.path.join(output_dir, BATCH_ID_FILE)
    if not os.path.exists(path):
        print(f"Error: No batch ID found at {path}", file=sys.stderr)
        print("Run --submit first.", file=sys.stderr)
        sys.exit(1)
    with open(path) as f:
        batch_id = f.read().strip()
    if not batch_id:
        print(f"Error: Empty batch ID in {path}", file=sys.stderr)
        sys.exit(1)
    return batch_id


def main():
    parser = argparse.ArgumentParser(
        description="ThermoQA Anthropic Batch Evaluation (50% cost reduction)"
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--submit", action="store_true", help="Submit batch to Anthropic API")
    mode.add_argument("--status", action="store_true", help="Check batch processing status")
    mode.add_argument("--collect", action="store_true", help="Collect results from completed batch")

    parser.add_argument(
        "--questions", default=DEFAULT_QUESTIONS,
        help=f"Path to questions JSONL (default: {DEFAULT_QUESTIONS})",
    )
    parser.add_argument(
        "--output", default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--model", default=MODEL,
        help=f"Anthropic model to use (default: {MODEL})",
    )
    args = parser.parse_args()

    if args.submit:
        submit(args.questions, args.output, args.model)
    elif args.status:
        status(args.output)
    elif args.collect:
        collect(args.questions, args.output, args.model)


if __name__ == "__main__":
    main()
