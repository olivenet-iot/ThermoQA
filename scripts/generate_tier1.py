#!/usr/bin/env python3
"""
CLI script to generate ThermoQA Tier 1 property lookup questions.

Usage:
    python scripts/generate_tier1.py
    python scripts/generate_tier1.py --output data/tier1_properties/ --count 110 --seed 42
"""

import argparse
import os
import sys

# Ensure project root is on path when running as script
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generation.question_generator import generate_tier1_questions


def main():
    parser = argparse.ArgumentParser(
        description="Generate ThermoQA Tier 1 property lookup questions"
    )
    parser.add_argument(
        "--output", default="data/tier1_properties/",
        help="Output directory (default: data/tier1_properties/)"
    )
    parser.add_argument(
        "--count", type=int, default=110,
        help="Target question count (default: 110)"
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Random seed for reproducibility (default: 42)"
    )
    args = parser.parse_args()

    print(f"Generating Tier 1 questions (target: {args.count}, seed: {args.seed})")
    print(f"Output: {args.output}")
    print()

    questions, warnings, metadata = generate_tier1_questions(
        output_dir=args.output,
        total_target=args.count,
        seed=args.seed,
    )

    # Print summary
    print("=" * 60)
    print(f"GENERATION COMPLETE: {len(questions)} questions")
    print("=" * 60)
    print()

    print("Category distribution:")
    for cat, count in sorted(metadata["category_distribution"].items()):
        print(f"  {cat:25s} {count:3d}")
    print()

    print("Difficulty distribution:")
    for diff, count in sorted(metadata["difficulty_distribution"].items()):
        print(f"  {diff:15s} {count:3d}")
    print()

    if warnings:
        print(f"Warnings ({len(warnings)}):")
        for w in warnings:
            print(f"  - {w}")
        print()

    # Spot check
    verified_count = sum(1 for q in questions if q["metadata"]["verified"])
    print(f"Cross-verified: {verified_count}/{len(questions)}")
    print()

    print(f"Output files:")
    print(f"  {args.output}questions.jsonl")
    print(f"  {args.output}metadata.json")

    if len(questions) < args.count:
        print(f"\nNote: generated {len(questions)} questions (target was {args.count})")
        sys.exit(1)


if __name__ == "__main__":
    main()
