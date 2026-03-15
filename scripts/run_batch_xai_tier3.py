#!/usr/bin/env python3
"""
xAI Batch API evaluation for ThermoQA Tier 3.

Uses the xAI REST-based batch API (not file-upload like OpenAI).

Usage:
    python scripts/run_batch_xai_tier3.py --submit [--ids ID1 ID2 ...]
    python scripts/run_batch_xai_tier3.py --status
    python scripts/run_batch_xai_tier3.py --collect
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone

import requests as http_requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evaluation.extractor import extract_tier3_properties, strip_thinking_tags
from evaluation.runner import SYSTEM_PROMPT
from evaluation.scorer import build_summary_from_entries, load_questions, score_tier3_question

DEFAULT_QUESTIONS = "data/tier3_cycles/questions.jsonl"
DEFAULT_OUTPUT_DIR = "results_tier3/xai"
BATCH_ID_FILE = "batch_id.txt"
MODEL = "grok-4.20-beta-0309-reasoning"
BASE_URL = "https://api.x.ai/v1"
CHUNK_SIZE = 50


def _get_api_key() -> str:
    key = os.environ.get("XAI_API_KEY")
    if not key:
        print("Error: XAI_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)
    return key


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {_get_api_key()}",
        "Content-Type": "application/json",
    }


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
    """Create a batch, add requests in chunks, and save the batch ID."""
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

    # Create the batch
    resp = http_requests.post(
        f"{BASE_URL}/batches",
        headers=_headers(),
        json={"name": "thermoqa_tier3"},
    )
    resp.raise_for_status()
    batch = resp.json()
    batch_id = batch["batch_id"]
    print(f"Created batch: {batch_id}")

    # Add requests in chunks
    for i in range(0, len(questions), CHUNK_SIZE):
        chunk = questions[i : i + CHUNK_SIZE]
        batch_requests = []
        for q in chunk:
            batch_requests.append({
                "batch_request_id": q["id"],
                "batch_request": {
                    "chat_get_completion": {
                        "model": model,
                        "max_completion_tokens": 65536,
                        "messages": [
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": q["question"]},
                        ],
                    }
                },
            })

        resp = http_requests.post(
            f"{BASE_URL}/batches/{batch_id}/requests",
            headers=_headers(),
            json={"requests": batch_requests},
        )
        resp.raise_for_status()
        print(f"  Added requests {i + 1}-{i + len(chunk)} / {len(questions)}")

    os.makedirs(output_dir, exist_ok=True)
    batch_id_path = os.path.join(output_dir, BATCH_ID_FILE)
    with open(batch_id_path, "w") as f:
        f.write(batch_id)

    print(f"Batch submitted successfully!")
    print(f"  Batch ID: {batch_id}")
    print(f"  Total requests: {len(questions)}")
    print(f"  Batch ID saved to {batch_id_path}")


def status(output_dir: str):
    """Check the status of a submitted batch."""
    batch_id = _read_batch_id(output_dir)
    resp = http_requests.get(
        f"{BASE_URL}/batches/{batch_id}",
        headers=_headers(),
    )
    resp.raise_for_status()
    batch = resp.json()

    print(f"Batch ID: {batch['batch_id']}")
    state = batch.get("state", {})
    for key in ("num_requests", "num_pending", "num_success", "num_error"):
        if key in state:
            print(f"  {key}: {state[key]}")
    if batch.get("created_at"):
        print(f"Created at: {batch['created_at']}")


def collect(questions_path: str, output_dir: str, model: str):
    """Collect results from a completed batch, score, and write outputs."""
    batch_id = _read_batch_id(output_dir)
    questions = load_questions(questions_path)
    questions_by_id = {q["id"]: q for q in questions}

    # Check batch status
    resp = http_requests.get(
        f"{BASE_URL}/batches/{batch_id}",
        headers=_headers(),
    )
    resp.raise_for_status()
    batch = resp.json()
    state = batch.get("state", {})
    num_pending = state.get("num_pending", -1)
    if num_pending > 0:
        print(f"Batch is not yet complete ({num_pending} pending)")
        for key in ("num_requests", "num_pending", "num_success", "num_error"):
            if key in state:
                print(f"  {key}: {state[key]}")
        sys.exit(1)

    # Paginated result retrieval
    print(f"Collecting results for batch {batch_id}...")
    all_results = []
    pagination_token = None
    while True:
        params = {"page_size": 100}
        if pagination_token:
            params["pagination_token"] = pagination_token
        resp = http_requests.get(
            f"{BASE_URL}/batches/{batch_id}/results",
            headers=_headers(),
            params=params,
        )
        resp.raise_for_status()
        page = resp.json()
        results = page.get("results", [])
        all_results.extend(results)
        pagination_token = page.get("pagination_token")
        if not pagination_token:
            break
        print(f"  Fetched {len(all_results)} results so far...")

    print(f"Retrieved {len(all_results)} results")

    entries = []
    errors = 0

    for result in all_results:
        qid = result.get("batch_request_id", "")
        q = questions_by_id.get(qid)
        if q is None:
            print(f"  WARNING: Unknown question ID in batch result: {qid}")
            continue

        step_ids = [s["id"] for s in q["steps"]]
        batch_response = result.get("batch_response", {})
        completion = batch_response.get("chat_get_completion", {})

        if completion.get("choices"):
            choice = completion["choices"][0]
            message = choice.get("message", {})
            text = message.get("content", "") or ""
            thinking_text = message.get("reasoning_content") or None

            raw = (thinking_text + "\n" + text) if thinking_text else text

            clean_text = strip_thinking_tags(text)
            extraction_text = clean_text if clean_text.strip() else (thinking_text or "")
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

            usage = completion.get("usage", {})
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
                "input_tokens": usage.get("prompt_tokens"),
                "output_tokens": usage.get("completion_tokens"),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        else:
            errors += 1
            error_info = result.get("error", batch_response.get("error", {}))
            error_msg = error_info.get("message", str(error_info)) if error_info else "Unknown error"
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
        "xai", model, errors=errors, batch_id=batch_id,
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
        description="ThermoQA Tier 3 xAI Batch Evaluation (REST-based batch API)"
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--submit", action="store_true", help="Submit batch to xAI Batch API")
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
        help=f"xAI model to use (default: {MODEL})",
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
