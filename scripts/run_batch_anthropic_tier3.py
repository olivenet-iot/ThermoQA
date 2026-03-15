#!/usr/bin/env python3
"""
Anthropic Message Batches API evaluation for ThermoQA Tier 3.

50% cost reduction vs. sequential API calls, with parallel processing.

Usage:
    python scripts/run_batch_anthropic_tier3.py --submit
    python scripts/run_batch_anthropic_tier3.py --status
    python scripts/run_batch_anthropic_tier3.py --collect
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone

# Ensure project root is on path when running as script
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evaluation.extractor import extract_tier3_properties, strip_thinking_tags
from evaluation.runner import SYSTEM_PROMPT
from evaluation.scorer import build_summary_from_entries, load_questions, score_tier3_question

DEFAULT_QUESTIONS = "data/tier3_cycles/questions.jsonl"
DEFAULT_OUTPUT_DIR = "results_tier3/anthropic"
BATCH_ID_FILE = "batch_id.txt"
MODEL = "claude-opus-4-6"


def _build_tier3_summary(entries, questions, provider_name, model_name,
                         errors=0, batch_id=None):
    """Build Tier 3 summary dict from scored entries."""
    stats = build_summary_from_entries(entries, questions)
    questions_by_id = {q["id"]: q for q in questions}

    by_depth = {}
    by_fluid = {}
    for entry in entries:
        q = questions_by_id.get(entry["id"], {})
        depth = q.get("depth", entry.get("depth", "?"))
        fluid = q.get("fluid", entry.get("fluid", "?"))
        score = entry.get("question_score", 0.0)
        for key, group in [(depth, by_depth), (fluid, by_fluid)]:
            if key not in group:
                group[key] = {"count": 0, "total_score": 0.0}
            group[key]["count"] += 1
            group[key]["total_score"] += score
    for group in [by_depth, by_fluid]:
        for d in group.values():
            d["score"] = round(d["total_score"] / d["count"], 4) if d["count"] else 0
            del d["total_score"]

    # Ideal vs actual cycle breakdown
    IDEAL_CYCLES = {"RNK-I", "BRY-I"}
    by_ideal_vs_actual = {"ideal": {"count": 0, "total_score": 0.0}, "actual": {"count": 0, "total_score": 0.0}}
    for entry in entries:
        q = questions_by_id.get(entry["id"], {})
        ct = q.get("cycle_type", entry.get("cycle_type", ""))
        score = entry.get("question_score", 0.0)
        group_key = "ideal" if ct in IDEAL_CYCLES else "actual"
        by_ideal_vs_actual[group_key]["count"] += 1
        by_ideal_vs_actual[group_key]["total_score"] += score
    for d in by_ideal_vs_actual.values():
        d["score"] = round(d["total_score"] / d["count"], 4) if d["count"] else 0
        del d["total_score"]

    input_toks = [e["input_tokens"] for e in entries if e.get("input_tokens") is not None]
    output_toks = [e["output_tokens"] for e in entries if e.get("output_tokens") is not None]

    summary = {
        "provider": provider_name,
        "model": model_name,
        "tier": 3,
        "overall_score": round(stats["mean_question_score"], 4),
        "total_questions": stats["total_questions"],
        "total_responses": len(entries),
        "total_properties": stats["total_properties"],
        "total_correct_properties": stats["total_correct_properties"],
        "property_accuracy": round(stats["property_accuracy"], 4),
        "by_cycle_type": {
            cat: {"score": round(d.get("mean_score", 0), 4), "count": d["n_questions"]}
            for cat, d in stats["per_category"].items()
        },
        "by_depth": by_depth,
        "by_fluid": by_fluid,
        "by_ideal_vs_actual": by_ideal_vs_actual,
        "by_step_type": {
            k: {"score": round(d.get("accuracy", 0), 4)}
            for k, d in stats.get("per_property_key", {}).items()
        },
        "errors": errors,
        "timing": {
            "mean_latency_s": 0,
            "min_latency_s": 0,
            "max_latency_s": 0,
            "note": "Batch API - no per-request latency available",
        },
        "tokens": {
            "total_input": sum(input_toks) if input_toks else None,
            "total_output": sum(output_toks) if output_toks else None,
            "mean_input": round(sum(input_toks) / len(input_toks), 1) if input_toks else None,
            "mean_output": round(sum(output_toks) / len(output_toks), 1) if output_toks else None,
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    if batch_id:
        summary["batch_id"] = batch_id
    return summary


def submit(questions_path: str, output_dir: str, model: str, ids: list[str] | None = None):
    """Build and submit a batch of requests to the Anthropic Batches API."""
    import anthropic

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

        step_ids = [s["id"] for s in q["steps"]]

        if result.result.type == "succeeded":
            message = result.result.message

            # Extract thinking and text blocks
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

            # Fallback: if text is empty but thinking exists, use thinking
            extraction_text = text if text.strip() else (thinking_text or "")
            extracted = extract_tier3_properties(extraction_text, step_ids)
            t3_result = score_tier3_question(q, extracted)

            scores = []
            steps = []
            for sr in t3_result.step_results:
                scores.append({
                    "key": sr.step_id,
                    "expected": sr.expected,
                    "extracted": sr.extracted,
                    "passed": sr.passed,
                    "error_pct": sr.error_pct,
                    "error_type": sr.error_type,
                })
                steps.append({
                    "id": sr.step_id,
                    "expected": sr.expected,
                    "extracted": sr.extracted,
                    "weight": sr.weight,
                    "passed": sr.passed,
                    "error_pct": sr.error_pct,
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
                "question_score": t3_result.weighted_score,
                "steps": steps,
                "cycle_type": q.get("cycle_type", ""),
                "depth": q.get("depth", ""),
                "fluid": q.get("fluid", ""),
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
                "steps": [],
                "cycle_type": q.get("cycle_type", ""),
                "depth": q.get("depth", ""),
                "fluid": q.get("fluid", ""),
                "model": model,
                "latency_s": 0.0,
                "input_tokens": None,
                "output_tokens": None,
                "error": error_msg,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        entries.append(entry)

    # Merge with existing responses
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

    for entry in entries:
        all_entries[entry["id"]] = entry
    print(f"Merged: {len(entries)} new/updated + {len(all_entries) - len(entries)} unchanged = {len(all_entries)} total")

    with open(responses_path, "w") as f:
        for entry in all_entries.values():
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"Wrote {len(all_entries)} responses to {responses_path}")

    # Build summary
    summary = _build_tier3_summary(
        list(all_entries.values()), questions,
        "anthropic", model, errors=errors, batch_id=batch_id,
    )

    summary_path = os.path.join(output_dir, "summary.json")
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"Wrote summary to {summary_path}")
    print()
    print(f"=== Results ===")
    print(f"  Questions:    {summary['total_questions']}")
    print(f"  Responses:    {summary['total_responses']}")
    print(f"  Errors:       {summary['errors']}")
    print(f"  Overall:      {summary['overall_score']:.1%}")
    if summary["tokens"]["total_input"]:
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
        description="ThermoQA Tier 3 Anthropic Batch Evaluation (50% cost reduction)"
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
    parser.add_argument(
        "--ids", nargs="+",
        help="Only submit these question IDs (for re-running specific questions)",
    )
    parser.add_argument(
        "--run", type=int, default=None,
        help="Run number for multi-run analysis (e.g., --run 1 saves to provider/run1/)",
    )
    args = parser.parse_args()

    output_dir = args.output
    if args.run is not None:
        output_dir = os.path.join(output_dir, f"run{args.run}")

    if args.submit:
        submit(args.questions, output_dir, args.model, args.ids)
    elif args.status:
        status(output_dir)
    elif args.collect:
        collect(args.questions, output_dir, args.model)


if __name__ == "__main__":
    main()
