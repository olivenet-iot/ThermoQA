#!/usr/bin/env python3
"""
Aggregate multi-run evaluation results for consistency analysis.

Usage:
    python scripts/aggregate_runs.py --provider anthropic --tier 1
    python scripts/aggregate_runs.py --all --tier 2
    python scripts/aggregate_runs.py --all --tier 3
"""

import argparse
import glob
import json
import math
import os
import sys


def _mean_std(values):
    if not values:
        return 0.0, 0.0
    m = sum(values) / len(values)
    if len(values) < 2:
        return m, 0.0
    variance = sum((v - m) ** 2 for v in values) / (len(values) - 1)
    return m, math.sqrt(variance)


def _aggregate_breakdown(summaries, key):
    """Aggregate a breakdown dict (by_cycle_type, by_component, per_category, etc.)."""
    all_keys = set()
    for s in summaries:
        all_keys.update(s.get(key, {}).keys())
    result = {}
    for k in sorted(all_keys):
        # Try 'score' first (T2/T3), then 'mean_score' (T1 per_category)
        vals = []
        for s in summaries:
            entry = s.get(key, {}).get(k, {})
            v = entry.get("score", entry.get("mean_score", entry.get("mean_question_score", 0)))
            vals.append(v)
        m, sd = _mean_std(vals)
        result[k] = {"mean": round(m, 4), "std": round(sd, 4), "n_runs": len(summaries)}
    return result


def aggregate_provider(provider_dir: str, tier: int) -> dict | None:
    """Aggregate run*/summary.json files in a provider directory."""
    pattern = os.path.join(provider_dir, "run*", "summary.json")
    paths = sorted(glob.glob(pattern))
    if not paths:
        return None

    summaries = []
    for p in paths:
        with open(p) as f:
            summaries.append(json.load(f))

    n = len(summaries)

    # Overall score — T1 uses mean_question_score, T2/T3 use overall_score
    scores = [s.get("overall_score", s.get("mean_question_score", 0)) for s in summaries]
    overall_mean, overall_std = _mean_std(scores)

    # Property accuracy
    prop_accs = [s.get("property_accuracy", 0) for s in summaries]
    prop_mean, prop_std = _mean_std(prop_accs)

    result = {
        "provider": summaries[0].get("provider", ""),
        "model": summaries[0].get("model", ""),
        "tier": tier,
        "n_runs": n,
        "run_paths": [os.path.dirname(p) for p in paths],
        "overall": {"mean": round(overall_mean, 4), "std": round(overall_std, 4)},
        "property_accuracy": {"mean": round(prop_mean, 4), "std": round(prop_std, 4)},
    }

    if tier == 1:
        result["by_category"] = _aggregate_breakdown(summaries, "per_category")
        result["by_difficulty"] = _aggregate_breakdown(summaries, "per_difficulty")
    elif tier == 2:
        result["by_component"] = _aggregate_breakdown(summaries, "by_component")
        result["by_depth"] = _aggregate_breakdown(summaries, "by_depth")
        result["by_fluid"] = _aggregate_breakdown(summaries, "by_fluid")
    elif tier == 3:
        result["by_cycle_type"] = _aggregate_breakdown(summaries, "by_cycle_type")
        result["by_depth"] = _aggregate_breakdown(summaries, "by_depth")
        result["by_fluid"] = _aggregate_breakdown(summaries, "by_fluid")

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Aggregate multi-run evaluation results"
    )
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--provider", help="Single provider to aggregate")
    target.add_argument("--all", action="store_true", help="Aggregate all providers")
    parser.add_argument(
        "--tier", type=int, required=True, choices=[1, 2, 3],
        help="Tier number (determines results directory)",
    )
    args = parser.parse_args()

    tier_dirs = {1: "results", 2: "results_tier2", 3: "results_tier3"}
    results_dir = tier_dirs[args.tier]

    if not os.path.isdir(results_dir):
        print(f"Results directory not found: {results_dir}")
        sys.exit(1)

    if args.all:
        providers = sorted(
            name for name in os.listdir(results_dir)
            if os.path.isdir(os.path.join(results_dir, name))
        )
    else:
        providers = [args.provider]

    for provider in providers:
        provider_dir = os.path.join(results_dir, provider)
        if not os.path.isdir(provider_dir):
            print(f"Provider directory not found: {provider_dir}")
            continue

        result = aggregate_provider(provider_dir, args.tier)
        if result is None:
            print(f"{provider}: no run*/summary.json found, skipping")
            continue

        output_path = os.path.join(provider_dir, "aggregate.json")
        with open(output_path, "w") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"{provider}: {result['n_runs']} runs, overall {result['overall']['mean']:.1%} +/- {result['overall']['std']:.1%}")
        print(f"  Wrote {output_path}")

    print("\nDone.")


if __name__ == "__main__":
    main()
