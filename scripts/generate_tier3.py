#!/usr/bin/env python3
"""
Generate ThermoQA Tier 3 cycle analysis questions.

Usage:
    python scripts/generate_tier3.py                    # generate all ~95
    python scripts/generate_tier3.py --cycle RNK-A      # specific cycle
    python scripts/generate_tier3.py --validate-only     # validate existing
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generation.question_generator import generate_tier3_questions

DEFAULT_OUTPUT = "data/tier3_cycles"


def validate_questions(path: str):
    """Run validation checks on generated questions."""
    with open(path) as f:
        questions = [json.loads(line) for line in f if line.strip()]

    print(f"Validating {len(questions)} questions from {path}...")
    errors = []
    ids = set()

    for q in questions:
        qid = q["id"]

        # Duplicate ID check
        if qid in ids:
            errors.append(f"{qid}: duplicate ID")
        ids.add(qid)

        expected = q.get("expected", {})

        # Energy balance for power cycles
        if q.get("cycle_type", "").startswith(("RNK", "BRY")):
            w_net = expected.get("w_net", {}).get("value")
            q_in = expected.get("q_in", {}).get("value")
            eta_th = expected.get("eta_th", {}).get("value")
            if w_net is not None and q_in is not None and eta_th is not None:
                if q_in > 0:
                    calc_eta = w_net / q_in
                    if abs(calc_eta - eta_th) > 0.001:
                        errors.append(f"{qid}: eta_th mismatch: {eta_th:.4f} vs w_net/q_in={calc_eta:.4f}")

        # s_gen >= 0 check
        for key, spec in expected.items():
            if key.startswith("s_gen_"):
                val = spec.get("value", 0)
                if val < -0.001:
                    errors.append(f"{qid}: {key} = {val:.6f} < 0 (second law violation)")

        # VCR x4 in (0,1)
        if q.get("cycle_type") == "VCR-A":
            x4 = expected.get("x4", {}).get("value")
            if x4 is not None and (x4 <= 0 or x4 >= 1):
                errors.append(f"{qid}: x4 = {x4:.4f} outside (0,1)")

        # Efficiency ranges
        eta_th = expected.get("eta_th", {}).get("value")
        if eta_th is not None and (eta_th < 0.05 or eta_th > 0.60):
            errors.append(f"{qid}: eta_th = {eta_th:.4f} outside (0.05, 0.60)")

        cop = expected.get("COP_R", {}).get("value")
        if cop is not None and (cop < 1.0 or cop > 12):
            errors.append(f"{qid}: COP_R = {cop:.4f} outside (1.0, 12)")

    if errors:
        print(f"\n{len(errors)} VALIDATION ERRORS:")
        for e in errors:
            print(f"  {e}")
    else:
        print("All validation checks passed.")

    return errors


def main():
    parser = argparse.ArgumentParser(description="Generate ThermoQA Tier 3 questions")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help=f"Output directory (default: {DEFAULT_OUTPUT})")
    parser.add_argument("--cycle", default=None, help="Only generate for specific cycle type (e.g. RNK-A)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    parser.add_argument("--validate-only", action="store_true", help="Validate existing questions only")
    args = parser.parse_args()

    if args.validate_only:
        qpath = os.path.join(args.output, "questions.jsonl")
        if not os.path.exists(qpath):
            print(f"No questions found at {qpath}")
            sys.exit(1)
        errors = validate_questions(qpath)
        sys.exit(1 if errors else 0)

    print("Generating Tier 3 cycle analysis questions...")
    if args.cycle:
        print(f"  Filtering to cycle: {args.cycle}")

    questions, warnings, metadata = generate_tier3_questions(
        args.output, seed=args.seed, cycle_filter=args.cycle
    )

    print(f"\n=== Generation Complete ===")
    print(f"  Total questions: {metadata['total_questions']}")
    print(f"  Output: {args.output}/questions.jsonl")

    print(f"\n  By cycle type:")
    for ct, n in sorted(metadata.get("cycle_distribution", {}).items()):
        print(f"    {ct}: {n}")

    print(f"\n  By depth:")
    for d, n in sorted(metadata.get("depth_distribution", {}).items()):
        print(f"    {d}: {n}")

    print(f"\n  By fluid:")
    for f, n in sorted(metadata.get("fluid_distribution", {}).items()):
        print(f"    {f}: {n}")

    if warnings:
        print(f"\n  Warnings ({len(warnings)}):")
        for w in warnings[:20]:
            print(f"    {w}")
        if len(warnings) > 20:
            print(f"    ... and {len(warnings) - 20} more")

    # Run validation
    qpath = os.path.join(args.output, "questions.jsonl")
    print()
    validate_questions(qpath)


if __name__ == "__main__":
    main()
