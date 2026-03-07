#!/usr/bin/env python3
"""
Re-extract and re-score existing model responses using the LLM-based extractor.

Re-processes responses.jsonl files without re-running models.

Usage:
    python scripts/reextract.py --provider google --dry-run
    python scripts/reextract.py --provider google
    python scripts/reextract.py --all --dry-run
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evaluation.llm_extractor import LLMExtractor
from evaluation.scorer import load_questions, score_dataset, score_question


DEFAULT_QUESTIONS = "data/tier1_properties/questions.jsonl"
DEFAULT_RESULTS_DIR = "results"


def find_providers(results_dir: str) -> list[str]:
    """Find all provider directories that contain responses.jsonl."""
    providers = []
    if not os.path.isdir(results_dir):
        return providers
    for name in sorted(os.listdir(results_dir)):
        path = os.path.join(results_dir, name, "responses.jsonl")
        if os.path.isfile(path):
            providers.append(name)
    return providers


def process_provider(
    provider: str,
    results_dir: str,
    questions_by_id: dict,
    questions: list[dict],
    extractor: LLMExtractor,
    dry_run: bool,
):
    """Re-extract and re-score a single provider's responses."""
    responses_path = os.path.join(results_dir, provider, "responses.jsonl")
    if not os.path.isfile(responses_path):
        print(f"  No responses.jsonl found for {provider}, skipping.")
        return

    # Load entries
    entries = []
    with open(responses_path) as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    print(f"  Loaded {len(entries)} responses from {responses_path}")

    # Build items for LLM extraction
    items = []
    for entry in entries:
        q = questions_by_id.get(entry["id"])
        if q is None:
            items.append({
                "response_text": "",
                "expected_keys": [],
                "question_text": "",
            })
            continue
        expected_keys = list(q["expected"].keys())
        # Use raw_response for extraction (includes thinking for context)
        response_text = entry.get("raw_response", entry.get("response_text", ""))
        items.append({
            "response_text": response_text,
            "expected_keys": expected_keys,
            "question_text": q["question"],
        })

    # Run LLM extraction
    new_extractions = extractor.extract_batch(items)

    # Score and compare
    old_scores = []
    new_scores = []
    deltas = []

    for entry, new_extracted in zip(entries, new_extractions):
        q = questions_by_id.get(entry["id"])
        old_score = entry.get("question_score", 0.0)
        old_scores.append(old_score)

        if q is None:
            new_scores.append(old_score)
            deltas.append(0.0)
            continue

        qr = score_question(q, new_extracted)
        new_score = qr.score
        new_scores.append(new_score)
        deltas.append(new_score - old_score)

        if not dry_run:
            # Build scores list matching batch script format
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
            entry["extracted"] = {k: v for k, v in new_extracted.items()}
            entry["scores"] = scores
            entry["question_score"] = qr.score

    # Print comparison table
    print(f"\n  {'ID':<12} {'Old':>6} {'New':>6} {'Delta':>7}")
    print(f"  {'-'*12} {'-'*6} {'-'*6} {'-'*7}")
    changed = 0
    for entry, old_s, new_s, delta in zip(entries, old_scores, new_scores, deltas):
        marker = ""
        if abs(delta) > 0.001:
            marker = " +" if delta > 0 else " -"
            changed += 1
        print(f"  {entry['id']:<12} {old_s:>5.1%} {new_s:>5.1%} {delta:>+6.1%}{marker}")

    old_acc = sum(old_scores) / len(old_scores) if old_scores else 0
    new_acc = sum(new_scores) / len(new_scores) if new_scores else 0
    print(f"\n  Aggregate: {old_acc:.1%} -> {new_acc:.1%} (delta: {new_acc - old_acc:+.1%})")
    print(f"  Changed: {changed}/{len(entries)} questions")

    if dry_run:
        print(f"  [DRY RUN] No files modified.")
        return

    # Write updated responses.jsonl
    with open(responses_path, "w") as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"  Wrote {len(entries)} entries to {responses_path}")

    # Rebuild summary.json
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

    # Read existing summary for provider/model/batch_id fields
    summary_path = os.path.join(results_dir, provider, "summary.json")
    old_summary = {}
    if os.path.isfile(summary_path):
        with open(summary_path) as f:
            old_summary = json.load(f)

    summary = {
        "provider": old_summary.get("provider", provider),
        "model": old_summary.get("model", entries[0].get("model", "unknown") if entries else "unknown"),
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
        "errors": old_summary.get("errors", 0),
        "timing": old_summary.get("timing", {
            "mean_latency_s": round(sum(latencies) / len(latencies), 2) if latencies else 0,
            "min_latency_s": round(min(latencies), 2) if latencies else 0,
            "max_latency_s": round(max(latencies), 2) if latencies else 0,
        }),
        "tokens": {
            "total_input": sum(input_tokens_list) if input_tokens_list else None,
            "total_output": sum(output_tokens_list) if output_tokens_list else None,
            "mean_input": round(sum(input_tokens_list) / len(input_tokens_list), 1) if input_tokens_list else None,
            "mean_output": round(sum(output_tokens_list) / len(output_tokens_list), 1) if output_tokens_list else None,
        },
        "reextracted_at": datetime.now(timezone.utc).isoformat(),
        "generated_at": old_summary.get("generated_at", datetime.now(timezone.utc).isoformat()),
    }

    # Preserve batch_id if it exists
    if "batch_id" in old_summary:
        summary["batch_id"] = old_summary["batch_id"]

    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"  Wrote summary to {summary_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Re-extract and re-score model responses using LLM-based extractor"
    )
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--provider", help="Single provider to re-extract (e.g., google)")
    target.add_argument("--all", action="store_true", help="Re-extract all providers in results/")

    parser.add_argument(
        "--questions", default=DEFAULT_QUESTIONS,
        help=f"Path to questions JSONL (default: {DEFAULT_QUESTIONS})",
    )
    parser.add_argument(
        "--results-dir", default=DEFAULT_RESULTS_DIR,
        help=f"Results root directory (default: {DEFAULT_RESULTS_DIR})",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Compare old vs new scores without writing files",
    )
    args = parser.parse_args()

    # Determine providers
    if args.all:
        providers = find_providers(args.results_dir)
        if not providers:
            print(f"No providers found in {args.results_dir}/")
            sys.exit(1)
        print(f"Found providers: {', '.join(providers)}")
    else:
        providers = [args.provider]

    # Load questions
    questions = load_questions(args.questions)
    questions_by_id = {q["id"]: q for q in questions}
    print(f"Loaded {len(questions)} questions from {args.questions}")

    # Create extractor
    extractor = LLMExtractor()

    for provider in providers:
        print(f"\n{'='*50}")
        print(f"Processing: {provider}")
        print(f"{'='*50}")
        process_provider(
            provider, args.results_dir, questions_by_id, questions, extractor, args.dry_run
        )

    print("\nDone.")


if __name__ == "__main__":
    main()
