#!/usr/bin/env python3
"""
CLI script to generate ThermoQA Tier 2 component analysis questions.

Usage:
    python scripts/generate_tier2.py
    python scripts/generate_tier2.py --output data/tier2_components/ --count 100 --seed 42
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generation.question_generator import generate_tier2_questions


def main():
    parser = argparse.ArgumentParser(
        description="Generate ThermoQA Tier 2 component analysis questions"
    )
    parser.add_argument(
        "--output", default="data/tier2_components/",
        help="Output directory (default: data/tier2_components/)"
    )
    parser.add_argument(
        "--count", type=int, default=100,
        help="Target question count (default: 100)"
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Random seed for reproducibility (default: 42)"
    )
    args = parser.parse_args()

    print(f"Generating Tier 2 questions (target: {args.count}, seed: {args.seed})")
    print(f"Output: {args.output}")
    print()

    questions, warnings, metadata = generate_tier2_questions(
        output_dir=args.output,
        total_target=args.count,
        seed=args.seed,
    )

    # Print summary
    print("=" * 60)
    print(f"GENERATION COMPLETE: {len(questions)} questions")
    print("=" * 60)
    print()

    print("Component distribution:")
    for comp, count in sorted(metadata["component_distribution"].items()):
        print(f"  {comp:25s} {count:3d}")
    print()

    print("Depth distribution:")
    for depth, count in sorted(metadata["depth_distribution"].items()):
        print(f"  {depth:10s} {count:3d}")
    print()

    print("Fluid distribution:")
    for fluid, count in sorted(metadata["fluid_distribution"].items()):
        print(f"  {fluid:10s} {count:3d}")
    print()

    print("Difficulty distribution:")
    for diff, count in sorted(metadata["difficulty_distribution"].items()):
        print(f"  {diff:15s} {count:3d}")
    print()

    if warnings:
        print(f"Warnings ({len(warnings)}):")
        for w in warnings[:20]:
            print(f"  - {w}")
        if len(warnings) > 20:
            print(f"  ... and {len(warnings) - 20} more")
        print()

    validated_count = sum(1 for q in questions if q["metadata"]["validated"])
    print(f"Validated: {validated_count}/{len(questions)}")
    print()

    print(f"Output files:")
    print(f"  {args.output}questions.jsonl")
    print(f"  {args.output}metadata.json")


if __name__ == "__main__":
    main()
