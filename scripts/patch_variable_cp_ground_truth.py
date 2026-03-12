#!/usr/bin/env python3
"""
Patch Tier 3 ground truth: recalculate BRY-AV/BRY-RV with ideal-gas NASA
polynomials and fix abs_tolerance for dimensionless quantities.

Usage:
    python scripts/patch_variable_cp_ground_truth.py --dry-run
    python scripts/patch_variable_cp_ground_truth.py --backup
    python scripts/patch_variable_cp_ground_truth.py
"""

import argparse
import json
import os
import shutil
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generation.cycle_state_generator import (
    CYCLE_GENERATORS,
    generate_brayton_actual_variable,
    generate_brayton_regenerative_variable,
)
from generation.question_generator import _extract_tier3_steps
from generation.templates.tier3_cycles import TIER3_TEMPLATES

DEFAULT_QUESTIONS = "data/tier3_cycles/questions.jsonl"

# Step IDs whose abs_tolerance should be tightened for dimensionless quantities
DIMENSIONLESS_STEPS = {"eta_th", "eta_combined", "eta_II", "COP_R", "COP_Carnot"}
NEW_DIMENSIONLESS_ABS_TOL = 0.02

# Cycle types to recalculate
RECALC_CYCLES = {"BRY-AV", "BRY-RV"}


def recalculate_expected(question: dict) -> dict:
    """Recalculate expected values for a BRY-AV or BRY-RV question."""
    cycle_type = question["cycle_type"]
    given = question["given"]

    # Build params (exclude 'fluid' key)
    params = {k: v for k, v in given.items() if k != "fluid"}

    # Generate new cycle
    generator = CYCLE_GENERATORS[cycle_type]
    result = generator(params)

    # Find matching template by cycle_type and depth
    depth = question["depth"]
    template = None
    for tmpl in TIER3_TEMPLATES:
        if tmpl.cycle_type == cycle_type and tmpl.depth == depth:
            template = tmpl
            break

    if template is None:
        raise ValueError(f"No template found for {cycle_type} depth {depth}")

    # Extract step values using the same mapping as question generation
    step_values = _extract_tier3_steps(template, result)
    return step_values


def patch_questions(questions_path: str, dry_run: bool, backup: bool):
    """Patch ground truth values and tolerances."""
    # Load questions
    with open(questions_path) as f:
        lines = f.readlines()

    questions = [json.loads(line.strip()) for line in lines if line.strip()]
    print(f"Loaded {len(questions)} questions from {questions_path}")

    # === Operation A: Recalculate BRY-AV/BRY-RV ground truth ===
    print(f"\n{'='*60}")
    print("Operation A: Recalculate BRY-AV/BRY-RV ground truth")
    print(f"{'='*60}")

    recalc_count = 0
    for q in questions:
        if q["cycle_type"] not in RECALC_CYCLES:
            continue

        recalc_count += 1
        qid = q["id"]
        new_values = recalculate_expected(q)

        print(f"\n  {qid} ({q['cycle_type']} depth {q['depth']}):")
        print(f"  {'Step':<20} {'Old':>14} {'New':>14} {'Delta':>10}")
        print(f"  {'-'*20} {'-'*14} {'-'*14} {'-'*10}")

        for step_id, spec in q["expected"].items():
            old_val = spec["value"]
            new_val = new_values.get(step_id)
            if new_val is not None:
                delta = new_val - old_val
                pct = abs(delta / old_val * 100) if old_val != 0 else 0
                marker = " ***" if pct > 1.0 else ""
                print(f"  {step_id:<20} {old_val:>14.4f} {new_val:>14.4f} {delta:>+10.4f}{marker}")
                if not dry_run:
                    spec["value"] = new_val
            else:
                print(f"  {step_id:<20} {old_val:>14.4f} {'MISSING':>14}")

    print(f"\n  Recalculated: {recalc_count} questions")

    # === Operation B: Fix abs_tolerance for dimensionless quantities ===
    print(f"\n{'='*60}")
    print("Operation B: Fix abs_tolerance for dimensionless quantities")
    print(f"{'='*60}")

    tol_fixes = 0
    for q in questions:
        for step_id, spec in q["expected"].items():
            if step_id in DIMENSIONLESS_STEPS:
                old_tol = spec.get("abs_tolerance", 0.5)
                if old_tol != NEW_DIMENSIONLESS_ABS_TOL:
                    tol_fixes += 1
                    if not dry_run:
                        spec["abs_tolerance"] = NEW_DIMENSIONLESS_ABS_TOL
                    if tol_fixes <= 5:  # Print first few
                        print(f"  {q['id']} {step_id}: {old_tol} -> {NEW_DIMENSIONLESS_ABS_TOL}")

    print(f"  Fixed abs_tolerance: {tol_fixes} step entries across all questions")

    # Write
    if dry_run:
        print(f"\n[DRY RUN] No files modified.")
        return

    if backup:
        backup_path = questions_path + f".bak.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(questions_path, backup_path)
        print(f"\nBackup saved to {backup_path}")

    with open(questions_path, "w") as f:
        for q in questions:
            f.write(json.dumps(q, ensure_ascii=False) + "\n")
    print(f"Wrote {len(questions)} questions to {questions_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Patch Tier 3 ground truth: ideal-gas air + dimensionless tolerances"
    )
    parser.add_argument(
        "--questions", default=DEFAULT_QUESTIONS,
        help=f"Path to questions JSONL (default: {DEFAULT_QUESTIONS})",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show changes without writing files",
    )
    parser.add_argument(
        "--backup", action="store_true",
        help="Create a backup before patching",
    )
    args = parser.parse_args()

    patch_questions(args.questions, args.dry_run, args.backup)
    print("\nDone.")


if __name__ == "__main__":
    main()
