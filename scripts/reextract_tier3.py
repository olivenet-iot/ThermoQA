#!/usr/bin/env python3
"""
Re-extract and re-score existing Tier 3 model responses using the LLM-based extractor.

Re-processes responses.jsonl files without re-running models.

Usage:
    python scripts/reextract_tier3.py --provider google --dry-run
    python scripts/reextract_tier3.py --provider google
    python scripts/reextract_tier3.py --all --dry-run
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evaluation.llm_extractor import LLMExtractor
from evaluation.scorer import build_summary_from_entries, load_questions, score_tier3_question


DEFAULT_QUESTIONS = "data/tier3_cycles/questions.jsonl"
DEFAULT_RESULTS_DIR = "results_tier3"


def _build_tier3_summary(entries, questions, provider_name, model_name,
                         errors=0):
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
    extractor: LLMExtractor,
    dry_run: bool,
):
    """Re-extract and re-score a single provider's Tier 3 responses."""
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

    # Score and compare
    old_scores = []
    new_scores = []
    deltas = []

    for i, entry in enumerate(entries):
        q = questions_by_id.get(entry["id"])
        old_score = entry.get("question_score", 0.0)
        old_scores.append(old_score)

        if q is None:
            new_scores.append(old_score)
            deltas.append(0.0)
            continue

        step_ids = [s["id"] for s in q["steps"]]
        response_text = entry.get("raw_response", entry.get("response_text", ""))

        print(f"  Extracting {i + 1}/{len(entries)} ({entry['id']})...", end="\r")
        new_extracted = extractor.extract_tier3(response_text, step_ids, q["question"])

        result = score_tier3_question(q, new_extracted)
        new_score = result.weighted_score
        new_scores.append(new_score)
        deltas.append(new_score - old_score)

        if not dry_run:
            # Update entry with new extraction
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
            entry["extracted"] = {k: v for k, v in new_extracted.items()}
            entry["scores"] = scores
            entry["steps"] = steps
            entry["question_score"] = new_score

        if i < len(entries) - 1:
            time.sleep(0.5)

    print()

    # Print comparison table
    print(f"\n  {'ID':<20} {'Old':>6} {'New':>6} {'Delta':>7}")
    print(f"  {'-'*20} {'-'*6} {'-'*6} {'-'*7}")
    changed = 0
    for entry, old_s, new_s, delta in zip(entries, old_scores, new_scores, deltas):
        marker = ""
        if abs(delta) > 0.001:
            marker = " +" if delta > 0 else " -"
            changed += 1
        print(f"  {entry['id']:<20} {old_s:>5.1%} {new_s:>5.1%} {delta:>+6.1%}{marker}")

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
    summary_path = os.path.join(results_dir, provider, "summary.json")
    old_summary = {}
    if os.path.isfile(summary_path):
        with open(summary_path) as f:
            old_summary = json.load(f)

    model_name = old_summary.get("model", entries[0].get("model", "unknown") if entries else "unknown")
    errors = old_summary.get("errors", 0)

    summary = _build_tier3_summary(entries, questions, provider, model_name, errors=errors)
    summary["reextracted_at"] = datetime.now(timezone.utc).isoformat()
    summary["generated_at"] = old_summary.get("generated_at", summary["generated_at"])

    # Preserve batch_id if it exists
    if "batch_id" in old_summary:
        summary["batch_id"] = old_summary["batch_id"]

    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"  Wrote summary to {summary_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Re-extract and re-score Tier 3 model responses using LLM-based extractor"
    )
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--provider", help="Single provider to re-extract (e.g., google)")
    target.add_argument("--all", action="store_true", help="Re-extract all providers in results_tier3/")

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
    print(f"Loaded {len(questions)} Tier 3 questions from {args.questions}")

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
