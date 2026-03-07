#!/usr/bin/env python3
"""
OpenAI Batch API evaluation for ThermoQA.

50% cost reduction vs. sequential API calls, with parallel processing.

Usage:
    python scripts/run_batch_openai.py --submit
    python scripts/run_batch_openai.py --status
    python scripts/run_batch_openai.py --collect
"""

import argparse
import json
import os
import sys
import tempfile
from datetime import datetime, timezone

# Ensure project root is on path when running as script
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evaluation.extractor import extract_properties, strip_thinking_tags
from evaluation.runner import SYSTEM_PROMPT
from evaluation.scorer import load_questions, score_dataset, score_question

DEFAULT_QUESTIONS = "data/tier1_properties/questions.jsonl"
DEFAULT_OUTPUT_DIR = "results/openai"
BATCH_ID_FILE = "batch_id.txt"
MODEL = "gpt-5.4"


def submit(questions_path: str, output_dir: str, model: str, ids: list[str] | None = None):
    """Build and submit a batch of requests to the OpenAI Batch API."""
    from openai import OpenAI

    questions = load_questions(questions_path)
    print(f"Loaded {len(questions)} questions from {questions_path}")

    if ids:
        all_ids = {q["id"] for q in questions}
        unknown = set(ids) - all_ids
        if unknown:
            print(f"ERROR: Unknown question IDs: {', '.join(sorted(unknown))}", file=sys.stderr)
            sys.exit(1)
        ids_set = set(ids)
        questions = [q for q in questions if q["id"] in ids_set]
        print(f"Filtered to {len(questions)} questions: {', '.join(ids)}")

    # Write JSONL batch input to a temp file
    batch_input_path = os.path.join(tempfile.gettempdir(), "thermoqa_openai_batch.jsonl")
    with open(batch_input_path, "w") as f:
        for q in questions:
            request = {
                "custom_id": q["id"],
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {
                    "model": model,
                    "max_completion_tokens": 64000,
                    "reasoning": {"effort": "high"},
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": q["question"]},
                    ],
                },
            }
            f.write(json.dumps(request, ensure_ascii=False) + "\n")

    print(f"Wrote {len(questions)} requests to {batch_input_path}")

    client = OpenAI()

    # Upload batch input file
    with open(batch_input_path, "rb") as f:
        uploaded = client.files.create(file=f, purpose="batch")
    print(f"Uploaded input file: {uploaded.id}")

    # Create batch
    batch = client.batches.create(
        input_file_id=uploaded.id,
        endpoint="/v1/chat/completions",
        completion_window="24h",
    )

    os.makedirs(output_dir, exist_ok=True)
    batch_id_path = os.path.join(output_dir, BATCH_ID_FILE)
    with open(batch_id_path, "w") as f:
        f.write(batch.id)

    print(f"Batch submitted successfully!")
    print(f"  Batch ID: {batch.id}")
    print(f"  Status:   {batch.status}")
    counts = batch.request_counts
    print(f"  Requests: total={counts.total}, "
          f"completed={counts.completed}, failed={counts.failed}")
    print(f"  Batch ID saved to {batch_id_path}")


def status(output_dir: str):
    """Check the status of a submitted batch."""
    from openai import OpenAI

    batch_id = _read_batch_id(output_dir)
    client = OpenAI()
    batch = client.batches.retrieve(batch_id)

    print(f"Batch ID: {batch.id}")
    print(f"Status:   {batch.status}")
    counts = batch.request_counts
    print(f"Requests: total={counts.total}, "
          f"completed={counts.completed}, failed={counts.failed}")
    if batch.completed_at:
        print(f"Completed at: {datetime.fromtimestamp(batch.completed_at, tz=timezone.utc).isoformat()}")
    if batch.failed_at:
        print(f"Failed at:    {datetime.fromtimestamp(batch.failed_at, tz=timezone.utc).isoformat()}")


def collect(questions_path: str, output_dir: str, model: str):
    """Collect results from a completed batch, score, and write outputs."""
    from openai import OpenAI

    batch_id = _read_batch_id(output_dir)
    questions = load_questions(questions_path)
    questions_by_id = {q["id"]: q for q in questions}

    client = OpenAI()

    # Verify batch is done
    batch = client.batches.retrieve(batch_id)
    if batch.status != "completed":
        print(f"Batch is not yet complete (status: {batch.status})")
        counts = batch.request_counts
        print(f"  total={counts.total}, completed={counts.completed}, failed={counts.failed}")
        sys.exit(1)

    if not batch.output_file_id:
        print("Error: Batch completed but no output file available.", file=sys.stderr)
        sys.exit(1)

    # Download output file
    print(f"Collecting results for batch {batch_id}...")
    output_content = client.files.content(batch.output_file_id)
    output_lines = output_content.text.strip().split("\n")

    entries = []
    errors = 0

    for line in output_lines:
        if not line.strip():
            continue
        result = json.loads(line)
        qid = result["custom_id"]
        q = questions_by_id.get(qid)
        if q is None:
            print(f"  WARNING: Unknown question ID in batch result: {qid}")
            continue

        expected_keys = list(q["expected"].keys())
        response = result.get("response", {})
        body = response.get("body", {})

        if response.get("status_code") == 200 and body.get("choices"):
            choice = body["choices"][0]
            message = choice.get("message", {})
            text = message.get("content", "") or ""
            thinking_text = message.get("reasoning_content") or None

            raw = (thinking_text + "\n" + text) if thinking_text else text

            # Strip thinking tags from the text portion for extraction
            clean_text = strip_thinking_tags(text)
            extraction_text = clean_text if clean_text.strip() else (thinking_text or "")
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

            usage = body.get("usage", {})
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
                "input_tokens": usage.get("prompt_tokens"),
                "output_tokens": usage.get("completion_tokens"),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        else:
            # Error response
            errors += 1
            error_msg = f"HTTP {response.get('status_code', 'unknown')}"
            if body.get("error"):
                error_msg += f" - {body['error'].get('message', str(body['error']))}"
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

    # Merge with existing responses (preserves old entries not in this batch)
    responses_path = os.path.join(output_dir, "responses.jsonl")
    all_entries = {}
    if os.path.exists(responses_path):
        with open(responses_path) as f:
            for line in f:
                line = line.strip()
                if line:
                    existing = json.loads(line)
                    all_entries[existing["id"]] = existing
        print(f"Loaded {len(all_entries)} existing responses from {responses_path}")

    # New entries overwrite existing ones by ID
    for entry in entries:
        all_entries[entry["id"]] = entry
    print(f"Merged: {len(entries)} new/updated + {len(all_entries) - len(entries)} unchanged = {len(all_entries)} total")

    with open(responses_path, "w") as f:
        for entry in all_entries.values():
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"Wrote {len(all_entries)} responses to {responses_path}")

    # Build summary over ALL entries (not just new batch)
    responses_for_scoring = {}
    input_tokens_list = []
    output_tokens_list = []

    for entry in all_entries.values():
        responses_for_scoring[entry["id"]] = entry.get("response_text", "")
        if entry.get("input_tokens") is not None:
            input_tokens_list.append(entry["input_tokens"])
        if entry.get("output_tokens") is not None:
            output_tokens_list.append(entry["output_tokens"])

    ds = score_dataset(questions, responses_for_scoring)

    summary = {
        "provider": "openai",
        "model": model,
        "batch_id": batch_id,
        "total_questions": ds.total_questions,
        "total_responses": len(all_entries),
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
        description="ThermoQA OpenAI Batch Evaluation (50% cost reduction)"
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--submit", action="store_true", help="Submit batch to OpenAI Batch API")
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
        help=f"OpenAI model to use (default: {MODEL})",
    )
    parser.add_argument(
        "--ids", nargs="+",
        help="Only submit these question IDs (for re-running specific questions)",
    )
    args = parser.parse_args()

    if args.submit:
        submit(args.questions, args.output, args.model, args.ids)
    elif args.status:
        status(args.output)
    elif args.collect:
        collect(args.questions, args.output, args.model)


if __name__ == "__main__":
    main()
