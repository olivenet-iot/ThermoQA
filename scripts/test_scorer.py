#!/usr/bin/env python3
"""
Test the extractor + scorer pipeline with synthetic LLM responses.

Usage: python scripts/test_scorer.py
"""

import sys
import os

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evaluation.extractor import extract_properties
from evaluation.scorer import (
    check_numeric,
    check_phase,
    load_questions,
    score_question,
    score_dataset,
)

QUESTIONS_PATH = "data/tier1_properties/questions.jsonl"

# Map property keys to common symbols for building synthetic responses
_KEY_SYMBOLS = {
    "h_kJ_kg": ("h", "kJ/kg"),
    "h_f_kJ_kg": ("h_f", "kJ/kg"),
    "h_g_kJ_kg": ("h_g", "kJ/kg"),
    "s_kJ_kgK": ("s", "kJ/(kg*K)"),
    "s_f_kJ_kgK": ("s_f", "kJ/(kg*K)"),
    "s_g_kJ_kgK": ("s_g", "kJ/(kg*K)"),
    "v_m3_kg": ("v", "m3/kg"),
    "v_f_m3_kg": ("v_f", "m3/kg"),
    "v_g_m3_kg": ("v_g", "m3/kg"),
    "u_kJ_kg": ("u", "kJ/kg"),
    "rho_kg_m3": ("rho", "kg/m3"),
    "T_C": ("T", "C"),
    "T_sat_C": ("T_sat", "C"),
    "P_kPa": ("P", "kPa"),
    "P_sat_kPa": ("P_sat", "kPa"),
    "x": ("x", ""),
}

_PHASE_NAMES = {
    "subcooled_liquid": "subcooled liquid",
    "superheated_vapor": "superheated vapor",
    "wet_steam": "two-phase mixture",
    "supercritical": "supercritical fluid",
    "saturated_liquid": "saturated liquid",
    "saturated_vapor": "saturated vapor",
}

_WRONG_PHASE = {
    "subcooled_liquid": "superheated vapor",
    "superheated_vapor": "subcooled liquid",
    "wet_steam": "superheated vapor",
    "supercritical": "subcooled liquid",
    "saturated_liquid": "superheated vapor",
    "saturated_vapor": "subcooled liquid",
}


def make_perfect_response(question: dict) -> str:
    """Generate a response with exact expected values."""
    lines = []
    for key, spec in question["expected"].items():
        if spec.get("type") == "exact_match":
            phase = spec["value"]
            lines.append(f"The phase is {_PHASE_NAMES.get(phase, phase)}.")
        else:
            sym, unit = _KEY_SYMBOLS.get(key, (key, ""))
            val = spec["value"]
            lines.append(f"{sym} = {val} {unit}".strip())
    return "\n".join(lines)


def make_wrong_response(question: dict, factor: float = 1.15) -> str:
    """Generate a response with all values off by the given factor, wrong phase."""
    lines = []
    for key, spec in question["expected"].items():
        if spec.get("type") == "exact_match":
            wrong = _WRONG_PHASE.get(spec["value"], "unknown")
            lines.append(f"The phase is {wrong}.")
        else:
            sym, unit = _KEY_SYMBOLS.get(key, (key, ""))
            val = spec["value"] * factor
            lines.append(f"{sym} = {val:.4f} {unit}".strip())
    return "\n".join(lines)


def make_scaled_response(question: dict, error_frac: float) -> str:
    """Generate a response with values off by error_frac (e.g., 0.019 = 1.9%)."""
    lines = []
    for key, spec in question["expected"].items():
        if spec.get("type") == "exact_match":
            phase = spec["value"]
            lines.append(f"The phase is {_PHASE_NAMES.get(phase, phase)}.")
        else:
            sym, unit = _KEY_SYMBOLS.get(key, (key, ""))
            val = spec["value"] * (1.0 + error_frac)
            lines.append(f"{sym} = {val:.6f} {unit}".strip())
    return "\n".join(lines)


# ---- Test functions ----

passed_tests = 0
failed_tests = 0


def run_test(name: str, func):
    global passed_tests, failed_tests
    try:
        func()
        print(f"  PASS: {name}")
        passed_tests += 1
    except AssertionError as e:
        print(f"  FAIL: {name} -- {e}")
        failed_tests += 1


def test_perfect_scores():
    """Perfect responses should score 100% on all questions."""
    questions = load_questions(QUESTIONS_PATH)
    responses = {q["id"]: make_perfect_response(q) for q in questions}
    results = score_dataset(questions, responses)
    assert results.property_accuracy == 1.0, (
        f"Expected 100% property accuracy, got {results.property_accuracy:.1%}"
    )
    assert results.mean_question_score == 1.0, (
        f"Expected 100% mean question score, got {results.mean_question_score:.1%}"
    )


def test_wrong_scores():
    """15% off values should fail most properties; wrong phase always fails."""
    questions = load_questions(QUESTIONS_PATH)
    responses = {q["id"]: make_wrong_response(q, factor=1.15) for q in questions}
    results = score_dataset(questions, responses)
    # Many small values (v~0.001) pass via abs_tolerance, so threshold is ~25%
    # Key check: score is far below passing (50%)
    assert results.mean_question_score < 0.35, (
        f"Expected low score with 15% error, got {results.mean_question_score:.1%}"
    )


def test_boundary_pass():
    """Values at 1.9% error should pass (within 2% tolerance)."""
    questions = load_questions(QUESTIONS_PATH)
    # Pick a numeric-heavy question (not phase-only)
    q = next(q for q in questions if q["category"] == "superheated_vapor")
    response = make_scaled_response(q, 0.019)
    expected_keys = list(q["expected"].keys())
    extracted = extract_properties(response, expected_keys)
    qr = score_question(q, extracted)
    for pr in qr.property_results:
        if pr.prop_key != "phase_name":
            assert pr.passed, (
                f"{pr.prop_key}: expected pass at 1.9% error, "
                f"got {pr.error_pct:.2f}% error, passed={pr.passed}"
            )


def test_boundary_fail():
    """Values at 2.5% error should fail for properties with values far from zero."""
    questions = load_questions(QUESTIONS_PATH)
    q = next(q for q in questions if q["category"] == "superheated_vapor")
    response = make_scaled_response(q, 0.025)
    expected_keys = list(q["expected"].keys())
    extracted = extract_properties(response, expected_keys)
    qr = score_question(q, extracted)
    for pr in qr.property_results:
        if pr.prop_key == "phase_name":
            continue
        exp_val = q["expected"][pr.prop_key]["value"]
        abs_tol = q["expected"][pr.prop_key].get("abs_tolerance", 0.5)
        # Only check failure for values where 2.5% exceeds the abs_tolerance
        if abs(exp_val * 0.025) > abs_tol:
            assert not pr.passed, (
                f"{pr.prop_key}: expected fail at 2.5% error "
                f"(val={exp_val}, abs_tol={abs_tol}), but passed"
            )


def test_missing_responses():
    """Empty responses should score 0% with all 'missing'."""
    questions = load_questions(QUESTIONS_PATH)
    q = questions[0]
    expected_keys = list(q["expected"].keys())
    extracted = extract_properties("", expected_keys)
    qr = score_question(q, extracted)
    assert qr.score == 0.0, f"Expected 0% score for empty response, got {qr.score:.1%}"
    for pr in qr.property_results:
        assert pr.error_type == "missing", (
            f"{pr.prop_key}: expected 'missing', got '{pr.error_type}'"
        )


def test_unit_autoconversion():
    """Enthalpy in J/kg (x1000) should be auto-converted to kJ/kg."""
    questions = load_questions(QUESTIONS_PATH)
    q = next(q for q in questions if "h_kJ_kg" in q["expected"])
    h_expected = q["expected"]["h_kJ_kg"]["value"]
    h_joules = h_expected * 1000  # J/kg instead of kJ/kg
    response = f"h = {h_joules} J/kg"
    extracted = extract_properties(response, ["h_kJ_kg"])
    assert extracted["h_kJ_kg"] is not None, "Failed to extract h"
    passed, err = check_numeric(h_expected, extracted["h_kJ_kg"], 2.0, 0.5)
    assert passed, (
        f"Auto-conversion failed: expected ~{h_expected}, got {extracted['h_kJ_kg']}, err={err:.2f}%"
    )


def test_quality_percentage():
    """x = 85% should be auto-converted to 0.85."""
    extracted = extract_properties("quality = 85%", ["x"])
    assert extracted["x"] is not None, "Failed to extract x"
    passed, err = check_numeric(0.85, extracted["x"], 2.0, 0.03)
    assert passed, f"Quality percentage conversion failed: got {extracted['x']}"


def test_phase_aliases():
    """Phase aliases should match case-insensitively."""
    # "superheated steam" is an alias for "superheated_vapor"
    extracted = extract_properties(
        "The phase is superheated steam.", ["phase_name"]
    )
    assert extracted["phase_name"] == "superheated_vapor", (
        f"Expected 'superheated_vapor', got '{extracted['phase_name']}'"
    )
    # "two-phase mixture" is an alias for "wet_steam"
    extracted2 = extract_properties(
        "This is a Two-Phase Mixture.", ["phase_name"]
    )
    assert extracted2["phase_name"] == "wet_steam", (
        f"Expected 'wet_steam', got '{extracted2['phase_name']}'"
    )


def test_prose_format():
    """Prose-style responses should be correctly extracted."""
    response = (
        "The specific enthalpy is approximately 1286.7 kJ/kg. "
        "The specific entropy is 3.1448 kJ/(kg*K). "
        "The specific volume is 0.001351 m3/kg."
    )
    extracted = extract_properties(
        response, ["h_kJ_kg", "s_kJ_kgK", "v_m3_kg"]
    )
    assert extracted["h_kJ_kg"] is not None, "Failed to extract h from prose"
    assert extracted["s_kJ_kgK"] is not None, "Failed to extract s from prose"
    assert extracted["v_m3_kg"] is not None, "Failed to extract v from prose"
    p1, _ = check_numeric(1286.7, extracted["h_kJ_kg"], 2.0, 0.5)
    p2, _ = check_numeric(3.1448, extracted["s_kJ_kgK"], 2.0, 0.5)
    p3, _ = check_numeric(0.001351, extracted["v_m3_kg"], 2.0, 0.5)
    assert p1, f"h mismatch: {extracted['h_kJ_kg']}"
    assert p2, f"s mismatch: {extracted['s_kJ_kgK']}"
    assert p3, f"v mismatch: {extracted['v_m3_kg']}"


def test_mixed_correct_wrong():
    """First property correct, rest wrong -> fractional score."""
    questions = load_questions(QUESTIONS_PATH)
    # Find a question with at least 3 numeric properties (no phase)
    q = next(
        q for q in questions
        if len(q["expected"]) >= 3
        and all(s.get("type") != "exact_match" for s in q["expected"].values())
    )
    keys = list(q["expected"].keys())
    lines = []
    for i, key in enumerate(keys):
        sym, unit = _KEY_SYMBOLS.get(key, (key, ""))
        spec = q["expected"][key]
        if i == 0:
            # Correct value
            lines.append(f"{sym} = {spec['value']} {unit}".strip())
        else:
            # Massively off — add 1000 to guarantee failure regardless of abs_tolerance
            lines.append(f"{sym} = {spec['value'] + 1000} {unit}".strip())
    response = "\n".join(lines)
    expected_keys = list(q["expected"].keys())
    extracted = extract_properties(response, expected_keys)
    qr = score_question(q, extracted)
    assert qr.n_correct == 1, f"Expected 1 correct, got {qr.n_correct}"
    expected_score = 1.0 / len(keys)
    assert abs(qr.score - expected_score) < 0.01, (
        f"Expected score ~{expected_score:.2f}, got {qr.score:.2f}"
    )


def main():
    print("ThermoQA Scorer Test Suite")
    print("=" * 40)

    run_test("test_perfect_scores", test_perfect_scores)
    run_test("test_wrong_scores", test_wrong_scores)
    run_test("test_boundary_pass", test_boundary_pass)
    run_test("test_boundary_fail", test_boundary_fail)
    run_test("test_missing_responses", test_missing_responses)
    run_test("test_unit_autoconversion", test_unit_autoconversion)
    run_test("test_quality_percentage", test_quality_percentage)
    run_test("test_phase_aliases", test_phase_aliases)
    run_test("test_prose_format", test_prose_format)
    run_test("test_mixed_correct_wrong", test_mixed_correct_wrong)

    print("=" * 40)
    print(f"Results: {passed_tests} passed, {failed_tests} failed out of {passed_tests + failed_tests}")

    return 0 if failed_tests == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
