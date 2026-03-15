#!/usr/bin/env python3
"""
Aggregate multi-run evaluation results for consistency analysis.

Usage:
    python scripts/aggregate_runs.py --provider anthropic --tier 3
    python scripts/aggregate_runs.py --all --tier 3
"""

import argparse
import glob
import json
import math
import os
import sys


def aggregate_provider(provider_dir: str) -> dict | None:
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

    def mean_std(values):
        if not values:
            return 0.0, 0.0
        m = sum(values) / len(values)
        if len(values) < 2:
            return m, 0.0
        variance = sum((v - m) ** 2 for v in values) / (len(values) - 1)
        return m, math.sqrt(variance)

    # Overall score
    scores = [s["overall_score"] for s in summaries]
    overall_mean, overall_std = mean_std(scores)

    # Per-cycle type
    all_cycle_types = set()
    for s in summaries:
        all_cycle_types.update(s.get("by_cycle_type", {}).keys())
    by_cycle_type = {}
    for ct in sorted(all_cycle_types):
        vals = [s.get("by_cycle_type", {}).get(ct, {}).get("score", 0) for s in summaries]
        m, sd = mean_std(vals)
        by_cycle_type[ct] = {"mean": round(m, 4), "std": round(sd, 4), "n_runs": n}

    # Per-depth
    all_depths = set()
    for s in summaries:
        all_depths.update(s.get("by_depth", {}).keys())
    by_depth = {}
    for d in sorted(all_depths):
        vals = [s.get("by_depth", {}).get(d, {}).get("score", 0) for s in summaries]
        m, sd = mean_std(vals)
        by_depth[d] = {"mean": round(m, 4), "std": round(sd, 4), "n_runs": n}

    # Per-fluid
    all_fluids = set()
    for s in summaries:
        all_fluids.update(s.get("by_fluid", {}).keys())
    by_fluid = {}
    for fl in sorted(all_fluids):
        vals = [s.get("by_fluid", {}).get(fl, {}).get("score", 0) for s in summaries]
        m, sd = mean_std(vals)
        by_fluid[fl] = {"mean": round(m, 4), "std": round(sd, 4), "n_runs": n}

    return {
        "provider": summaries[0].get("provider", ""),
        "model": summaries[0].get("model", ""),
        "n_runs": n,
        "run_paths": [os.path.dirname(p) for p in paths],
        "overall": {"mean": round(overall_mean, 4), "std": round(overall_std, 4)},
        "by_cycle_type": by_cycle_type,
        "by_depth": by_depth,
        "by_fluid": by_fluid,
    }


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

        result = aggregate_provider(provider_dir)
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
