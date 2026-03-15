#!/usr/bin/env python3
"""
Re-score existing Tier 3 responses against patched ground truth.

Uses existing extracted values — no API calls. Only scores change.

Usage:
    python scripts/rescore_tier3.py --all --dry-run
    python scripts/rescore_tier3.py --all
    python scripts/rescore_tier3.py --provider anthropic --dry-run
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evaluation.scorer import (
    build_summary_from_entries,
    check_numeric,
    load_questions,
    score_tier3_question,
)

DEFAULT_QUESTIONS = "data/tier3_cycles/questions.jsonl"
DEFAULT_RESULTS_DIR = "results_tier3"


def _build_tier3_summary(entries, questions, provider_name, model_name, errors=0):
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
    by_ideal_vs_actual = {
        "ideal": {"count": 0, "total_score": 0.0},
        "actual": {"count": 0, "total_score": 0.0},
    }
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

    latencies = [e.get("latency_s", 0) for e in entries]
    input_toks = [e["input_tokens"] for e in entries if e.get("input_tokens") is not None]
    output_toks = [e["output_tokens"] for e in entries if e.get("output_tokens") is not None]

    return {
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
            "mean_latency_s": round(sum(latencies) / len(latencies), 2) if latencies else 0,
            "min_latency_s": round(min(latencies), 2) if latencies else 0,
            "max_latency_s": round(max(latencies), 2) if latencies else 0,
        },
        "tokens": {
            "total_input": sum(input_toks) if input_toks else None,
            "total_output": sum(output_toks) if output_toks else None,
            "mean_input": round(sum(input_toks) / len(input_toks), 1) if input_toks else None,
            "mean_output": round(sum(output_toks) / len(output_toks), 1) if output_toks else None,
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


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
    dry_run: bool,
    run_num: int | None = None,
):
    """Re-score a single provider's responses using existing extracted values."""
    provider_path = os.path.join(results_dir, provider)
    if run_num is not None:
        provider_path = os.path.join(provider_path, f"run{run_num}")
    responses_path = os.path.join(provider_path, "responses.jsonl")
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
    print(f"  Loaded {len(entries)} responses")

    old_scores = []
    new_scores = []

    for entry in entries:
        q = questions_by_id.get(entry["id"])
        old_score = entry.get("question_score", 0.0)
        old_scores.append(old_score)

        if q is None:
            new_scores.append(old_score)
            continue

        # Use existing extracted values — no re-extraction
        extracted = entry.get("extracted", {})

        # Re-score against (potentially updated) ground truth
        result = score_tier3_question(q, extracted)
        new_score = result.weighted_score
        new_scores.append(new_score)

        if not dry_run:
            # Update scores and steps in-place
            scores = []
            steps = []
            for sr in result.step_results:
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
            entry["scores"] = scores
            entry["steps"] = steps
            entry["question_score"] = new_score

    # Print comparison
    print(f"\n  {'ID':<25} {'Old':>6} {'New':>6} {'Delta':>7}")
    print(f"  {'-'*25} {'-'*6} {'-'*6} {'-'*7}")
    changed = 0
    for entry, old_s, new_s in zip(entries, old_scores, new_scores):
        delta = new_s - old_s
        marker = ""
        if abs(delta) > 0.001:
            marker = " +" if delta > 0 else " -"
            changed += 1
        print(f"  {entry['id']:<25} {old_s:>5.1%} {new_s:>5.1%} {delta:>+6.1%}{marker}")

    old_avg = sum(old_scores) / len(old_scores) if old_scores else 0
    new_avg = sum(new_scores) / len(new_scores) if new_scores else 0
    print(f"\n  Aggregate: {old_avg:.1%} -> {new_avg:.1%} (delta: {new_avg - old_avg:+.1%})")
    print(f"  Changed: {changed}/{len(entries)} questions")

    if dry_run:
        print(f"  [DRY RUN] No files modified.")
        return

    # Write updated responses
    with open(responses_path, "w") as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"  Wrote {len(entries)} entries to {responses_path}")

    # Rebuild summary.json
    summary_path = os.path.join(provider_path, "summary.json")
    old_summary = {}
    if os.path.isfile(summary_path):
        with open(summary_path) as f:
            old_summary = json.load(f)

    model_name = old_summary.get(
        "model", entries[0].get("model", "unknown") if entries else "unknown"
    )
    errors = old_summary.get("errors", 0)

    summary = _build_tier3_summary(entries, questions, provider, model_name, errors=errors)
    summary["rescored_at"] = datetime.now(timezone.utc).isoformat()
    summary["generated_at"] = old_summary.get("generated_at", summary["generated_at"])

    if "batch_id" in old_summary:
        summary["batch_id"] = old_summary["batch_id"]
    if "reextracted_at" in old_summary:
        summary["reextracted_at"] = old_summary["reextracted_at"]

    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"  Wrote summary to {summary_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Re-score Tier 3 responses against patched ground truth (no API calls)"
    )
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--provider", help="Single provider to re-score")
    target.add_argument("--all", action="store_true", help="Re-score all providers")

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
    parser.add_argument(
        "--run", type=int, default=None,
        help="Run number for multi-run analysis (e.g., --run 1 saves to provider/run1/)",
    )
    args = parser.parse_args()

    if args.all:
        providers = find_providers(args.results_dir)
        if not providers:
            print(f"No providers found in {args.results_dir}/")
            sys.exit(1)
        print(f"Found providers: {', '.join(providers)}")
    else:
        providers = [args.provider]

    questions = load_questions(args.questions)
    questions_by_id = {q["id"]: q for q in questions}
    print(f"Loaded {len(questions)} questions from {args.questions}")

    for provider in providers:
        print(f"\n{'='*55}")
        print(f"Re-scoring: {provider}")
        print(f"{'='*55}")
        process_provider(provider, args.results_dir, questions_by_id, questions, args.dry_run,
                         run_num=args.run)

    print("\nDone.")


if __name__ == "__main__":
    main()
