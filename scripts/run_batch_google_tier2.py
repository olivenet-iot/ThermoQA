#!/usr/bin/env python3
"""
Google Gemini Batch API evaluation for ThermoQA Tier 2.

50% cost reduction vs. sequential API calls, with parallel processing.

Usage:
    python scripts/run_batch_google_tier2.py --submit
    python scripts/run_batch_google_tier2.py --status
    python scripts/run_batch_google_tier2.py --collect
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone

# Ensure project root is on path when running as script
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evaluation.extractor import extract_tier2_properties, strip_thinking_tags
from evaluation.runner import SYSTEM_PROMPT
from evaluation.scorer import build_summary_from_entries, load_questions, score_tier2_question

DEFAULT_QUESTIONS = "data/tier2_components/questions.jsonl"
DEFAULT_OUTPUT_DIR = "results_tier2/google"
BATCH_ID_FILE = "batch_job_name.txt"
MODEL = "gemini-3.1-pro-preview"


def _build_tier2_summary(entries, questions, provider_name, model_name,
                         errors=0, batch_id=None):
    """Build Tier 2 summary dict from scored entries."""
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

    input_toks = [e["input_tokens"] for e in entries if e.get("input_tokens") is not None]
    output_toks = [e["output_tokens"] for e in entries if e.get("output_tokens") is not None]

    summary = {
        "provider": provider_name,
        "model": model_name,
        "tier": 2,
        "overall_score": round(stats["mean_question_score"], 4),
        "total_questions": stats["total_questions"],
        "total_responses": len(entries),
        "total_properties": stats["total_properties"],
        "total_correct_properties": stats["total_correct_properties"],
        "property_accuracy": round(stats["property_accuracy"], 4),
        "by_component": {
            cat: {"score": round(d.get("mean_score", 0), 4), "count": d["n_questions"]}
            for cat, d in stats["per_category"].items()
        },
        "by_depth": by_depth,
        "by_fluid": by_fluid,
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
    """Build and submit a batch of requests to the Google Gemini Batch API."""
    from google import genai
    from google.genai.types import CreateBatchJobConfig

    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("Error: GOOGLE_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)

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

    # Build JSONL batch input file
    os.makedirs(output_dir, exist_ok=True)
    batch_input_path = os.path.join(output_dir, "batch_input.jsonl")
    with open(batch_input_path, "w") as f:
        for q in questions:
            request = {
                "key": q["id"],
                "request": {
                    "model": f"models/{model}",
                    "contents": [
                        {"role": "user", "parts": [{"text": q["question"]}]},
                    ],
                    "systemInstruction": {
                        "parts": [{"text": SYSTEM_PROMPT}],
                    },
                    "generationConfig": {
                        "thinking_config": {"thinking_level": "HIGH"},
                    },
                },
            }
            f.write(json.dumps(request, ensure_ascii=False) + "\n")

    print(f"Wrote {len(questions)} requests to {batch_input_path}")

    client = genai.Client(api_key=api_key)

    # Upload batch input file
    uploaded_file = client.files.upload(file=batch_input_path)
    print(f"Uploaded input file: {uploaded_file.name}")

    # Create batch job
    batch_job = client.batches.create(
        model=f"models/{model}",
        src=uploaded_file.name,
        config=CreateBatchJobConfig(display_name="thermoqa-tier2"),
    )

    batch_id_path = os.path.join(output_dir, BATCH_ID_FILE)
    with open(batch_id_path, "w") as f:
        f.write(batch_job.name)

    print(f"Batch submitted successfully!")
    print(f"  Job name: {batch_job.name}")
    print(f"  State:    {batch_job.state}")
    if batch_job.completion_stats:
        stats = batch_job.completion_stats
        print(f"  Stats:    success={getattr(stats, 'success_count', 0)}, "
              f"failed={getattr(stats, 'failure_count', 0)}")
    print(f"  Job name saved to {batch_id_path}")


def status(output_dir: str):
    """Check the status of a submitted batch."""
    from google import genai

    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("Error: GOOGLE_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)

    job_name = _read_batch_id(output_dir)
    client = genai.Client(api_key=api_key)
    batch_job = client.batches.get(name=job_name)

    print(f"Job name: {batch_job.name}")
    print(f"State:    {batch_job.state}")
    if batch_job.completion_stats:
        stats = batch_job.completion_stats
        print(f"Stats:    success={getattr(stats, 'success_count', 0)}, "
              f"failed={getattr(stats, 'failure_count', 0)}")


def collect(questions_path: str, output_dir: str, model: str):
    """Collect results from a completed batch, score, and write outputs."""
    from google import genai

    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("Error: GOOGLE_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)

    job_name = _read_batch_id(output_dir)
    questions = load_questions(questions_path)
    questions_by_id = {q["id"]: q for q in questions}

    client = genai.Client(api_key=api_key)

    # Verify batch is done
    batch_job = client.batches.get(name=job_name)
    terminal_states = {"JOB_STATE_SUCCEEDED", "JOB_STATE_PARTIALLY_SUCCEEDED"}
    state_str = str(batch_job.state)
    # Handle enum values — may be the enum name or its string representation
    if state_str not in terminal_states and not any(s in state_str for s in terminal_states):
        print(f"Batch is not yet complete (state: {batch_job.state})")
        if batch_job.completion_stats:
            stats = batch_job.completion_stats
            print(f"  success={getattr(stats, 'success_count', 0)}, "
                  f"failed={getattr(stats, 'failure_count', 0)}")
        sys.exit(1)

    # Download results
    print(f"Collecting results for batch {job_name}...")
    dest_file = batch_job.dest.file_name
    result_bytes = client.files.download(file=dest_file)
    output_text = result_bytes.decode("utf-8") if isinstance(result_bytes, bytes) else str(result_bytes)
    output_lines = output_text.strip().split("\n")

    entries = []
    errors = 0

    for line in output_lines:
        if not line.strip():
            continue
        result = json.loads(line)
        qid = result.get("key")
        q = questions_by_id.get(qid)
        if q is None:
            print(f"  WARNING: Unknown question ID in batch result: {qid}")
            continue

        step_ids = [s["id"] for s in q["steps"]]
        response = result.get("response")

        if response and not result.get("error"):
            # Extract thinking and answer parts from response candidates
            thinking_parts = []
            answer_parts = []
            candidates = response.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                for part in parts:
                    part_text = part.get("text", "")
                    if not part_text:
                        continue
                    if part.get("thought"):
                        thinking_parts.append(part_text)
                    else:
                        answer_parts.append(part_text)

            thinking_text = "\n".join(thinking_parts) if thinking_parts else None
            text = "\n".join(answer_parts) if answer_parts else ""
            text = strip_thinking_tags(text)
            raw = "\n".join(thinking_parts + answer_parts) if (thinking_parts or answer_parts) else text

            # Fallback: if text is empty but thinking exists, use thinking
            extraction_text = text if text.strip() else (thinking_text or "")
            extracted = extract_tier2_properties(extraction_text, step_ids)
            t2_result = score_tier2_question(q, extracted)

            scores = []
            steps = []
            for sr in t2_result.step_results:
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

            usage = response.get("usageMetadata", {})
            entry = {
                "id": qid,
                "question": q["question"],
                "raw_response": raw,
                "response_text": text,
                "thinking_text": thinking_text,
                "extracted": {k: v for k, v in extracted.items()},
                "scores": scores,
                "question_score": t2_result.weighted_score,
                "steps": steps,
                "component": q.get("component", ""),
                "depth": q.get("depth", ""),
                "fluid": q.get("fluid", ""),
                "model": model,
                "latency_s": 0.0,
                "input_tokens": usage.get("promptTokenCount"),
                "output_tokens": usage.get("candidatesTokenCount"),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        else:
            # Error response
            errors += 1
            error_obj = result.get("error", {})
            error_msg = error_obj.get("message", str(error_obj)) if error_obj else "Unknown error"
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
                "component": q.get("component", ""),
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
    summary = _build_tier2_summary(
        list(all_entries.values()), questions,
        "google", model, errors=errors, batch_id=job_name,
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
    """Read saved batch job name from file."""
    path = os.path.join(output_dir, BATCH_ID_FILE)
    if not os.path.exists(path):
        print(f"Error: No batch job name found at {path}", file=sys.stderr)
        print("Run --submit first.", file=sys.stderr)
        sys.exit(1)
    with open(path) as f:
        job_name = f.read().strip()
    if not job_name:
        print(f"Error: Empty batch job name in {path}", file=sys.stderr)
        sys.exit(1)
    return job_name


def main():
    parser = argparse.ArgumentParser(
        description="ThermoQA Tier 2 Google Gemini Batch Evaluation (50% cost reduction)"
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--submit", action="store_true", help="Submit batch to Google Gemini Batch API")
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
        help=f"Google Gemini model to use (default: {MODEL})",
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
