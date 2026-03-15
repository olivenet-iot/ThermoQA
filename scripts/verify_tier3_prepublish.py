#!/usr/bin/env python3
"""
ThermoQA Tier 3 — Pre-Publish Verification Script

Loads questions.jsonl and all 5 provider results, runs 14 checks,
prints a summary table with status + notes per check.

Usage:
    python scripts/verify_tier3_prepublish.py
"""

import json
import math
import sys
from collections import Counter
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
QUESTIONS_PATH = ROOT / "data" / "tier3_cycles" / "questions.jsonl"
RESULTS_DIR = ROOT / "results_tier3"
PROVIDERS = ["anthropic", "deepseek", "google", "minimax", "openai"]

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_questions():
    with open(QUESTIONS_PATH) as f:
        return [json.loads(line) for line in f if line.strip()]


def load_responses(provider):
    path = RESULTS_DIR / provider / "responses.jsonl"
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def load_summary(provider):
    path = RESULTS_DIR / provider / "summary.json"
    with open(path) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Check 1: Energy balance closure
# ---------------------------------------------------------------------------

def check_energy_balance(questions):
    """For each question, verify q_in - w_net - q_out ≈ 0 (power cycles)
    or q_L + w_comp - q_H ≈ 0 (VCR)."""
    issues = []
    checked = 0

    for q in questions:
        exp = q["expected"]
        ct = q["cycle_type"]
        qid = q["id"]

        if ct.startswith("VCR"):
            # VCR: q_L + w_comp = q_H
            q_L = exp.get("q_L", {}).get("value")
            w_comp = exp.get("w_comp", {}).get("value")
            q_H = exp.get("q_H", {}).get("value")
            if q_L is not None and w_comp is not None and q_H is not None:
                balance = q_L + w_comp - q_H
                checked += 1
                if abs(balance) > 0.5:
                    issues.append(f"{qid}: q_L+w_comp-q_H = {balance:.4f}")

        elif ct.startswith("CCGT"):
            # CCGT: more complex — check energy_balance_error keys
            for k in ["energy_balance_error_gas", "energy_balance_error_steam",
                       "energy_balance_error"]:
                val = exp.get(k, {}).get("value")
                if val is not None:
                    checked += 1
                    if abs(val) > 0.01:
                        issues.append(f"{qid}: {k} = {val:.6f}")

        else:
            # Power cycles (RNK, BRY): q_in = w_net + q_out
            # q_out not always stored; check via energy_balance_error if present
            ebe = exp.get("energy_balance_error", {}).get("value")
            if ebe is not None:
                checked += 1
                if abs(ebe) > 0.01:
                    issues.append(f"{qid}: energy_balance_error = {ebe:.6f}")
            else:
                # Derive: for RNK/BRY, q_in - w_net = q_out (rejected heat)
                q_in = exp.get("q_in", exp.get("q_combustion", {})).get("value")
                w_net = exp.get("w_net", {}).get("value")
                eta = exp.get("eta_th", {}).get("value")
                if q_in is not None and w_net is not None and eta is not None:
                    # eta_th = w_net / q_in
                    expected_eta = w_net / q_in if q_in != 0 else 0
                    checked += 1
                    if abs(expected_eta - eta) / max(abs(eta), 1e-10) > 0.001:
                        issues.append(f"{qid}: eta_th mismatch: w_net/q_in={expected_eta:.6f} vs eta_th={eta:.6f}")

    ok = len(issues) == 0
    notes = f"Checked {checked} balances"
    if issues:
        notes += f"; {len(issues)} failures: " + "; ".join(issues[:5])
        if len(issues) > 5:
            notes += f" (+{len(issues)-5} more)"
    return ok, notes


# ---------------------------------------------------------------------------
# Check 2: Second law — s_gen >= 0
# ---------------------------------------------------------------------------

def check_second_law(questions):
    """Verify all s_gen_* values >= -1e-6."""
    issues = []
    checked = 0

    for q in questions:
        exp = q["expected"]
        for k, v in exp.items():
            if k.startswith("s_gen") and isinstance(v, dict):
                val = v.get("value")
                if val is not None:
                    checked += 1
                    if val < -1e-6:
                        issues.append(f"{q['id']}: {k} = {val:.6f}")

    ok = len(issues) == 0
    notes = f"Checked {checked} s_gen values"
    if issues:
        notes += f"; {len(issues)} violations: " + "; ".join(issues[:5])
    return ok, notes


# ---------------------------------------------------------------------------
# Check 3: Efficiency ranges
# ---------------------------------------------------------------------------

def check_efficiency_ranges(questions):
    """Check eta_th in (0,1), COP_R in (0,20), eta_combined in (0,1)."""
    issues = []
    checked = 0

    for q in questions:
        exp = q["expected"]
        qid = q["id"]

        for key, lo, hi, label in [
            ("eta_th", 0, 1, "eta_th"),
            ("eta_combined", 0, 1, "eta_combined"),
            ("COP_R", 0, 20, "COP_R"),
            ("eta_II", 0, 1, "eta_II"),
        ]:
            val_d = exp.get(key)
            if val_d and isinstance(val_d, dict):
                val = val_d.get("value")
                if val is not None:
                    checked += 1
                    if not (lo < val < hi):
                        issues.append(f"{qid}: {label} = {val:.4f} not in ({lo},{hi})")

    ok = len(issues) == 0
    notes = f"Checked {checked} efficiency values"
    if issues:
        notes += f"; {len(issues)} out of range: " + "; ".join(issues[:5])
    return ok, notes


# ---------------------------------------------------------------------------
# Check 4: VCR x4 in (0, 1)
# ---------------------------------------------------------------------------

def check_vcr_x4(questions):
    """For VCR cycles, verify 0 < x4 < 1."""
    issues = []
    checked = 0

    for q in questions:
        if not q["cycle_type"].startswith("VCR"):
            continue
        x4_d = q["expected"].get("x4")
        if x4_d and isinstance(x4_d, dict):
            val = x4_d.get("value")
            if val is not None:
                checked += 1
                if not (0 < val < 1):
                    issues.append(f"{q['id']}: x4 = {val:.4f}")

    ok = len(issues) == 0
    notes = f"Checked {checked} VCR x4 values"
    if issues:
        notes += f"; {len(issues)} out of range: " + "; ".join(issues[:5])
    return ok, notes


# ---------------------------------------------------------------------------
# Check 5: No negative work/heat
# ---------------------------------------------------------------------------

def check_no_negative_work_heat(questions):
    """Verify w_net > 0, q_in > 0, w_turb > 0, w_comp > 0, etc."""
    issues = []
    checked = 0

    positive_keys_power = ["w_net", "q_in", "w_turb", "w_pump", "w_comp",
                           "w_HPT", "w_LPT", "w_gas_turb", "w_steam_turb",
                           "q_combustion", "W_dot_net", "W_net_combined"]
    positive_keys_vcr = ["w_comp", "q_L", "q_H", "W_dot_comp", "Q_dot_L", "COP_R"]

    for q in questions:
        exp = q["expected"]
        qid = q["id"]
        keys = positive_keys_vcr if q["cycle_type"].startswith("VCR") else positive_keys_power

        for k in keys:
            val_d = exp.get(k)
            if val_d and isinstance(val_d, dict):
                val = val_d.get("value")
                if val is not None:
                    checked += 1
                    if val < 0:
                        issues.append(f"{qid}: {k} = {val:.4f}")

    ok = len(issues) == 0
    notes = f"Checked {checked} work/heat values"
    if issues:
        notes += f"; {len(issues)} negative: " + "; ".join(issues[:5])
    return ok, notes


# ---------------------------------------------------------------------------
# Check 6: CCGT HRSG constraints
# ---------------------------------------------------------------------------

def check_ccgt_hrsg(questions):
    """Check m_dot_steam > 0 and T8 < T4 - 10 for CCGT cycles."""
    issues = []
    checked = 0

    for q in questions:
        if q["cycle_type"] != "CCGT":
            continue
        exp = q["expected"]
        qid = q["id"]

        m_dot = exp.get("m_dot_steam", {}).get("value")
        if m_dot is not None:
            checked += 1
            if m_dot <= 0:
                issues.append(f"{qid}: m_dot_steam = {m_dot:.4f}")

        T4 = exp.get("T4", {}).get("value")  # K
        # T8 is steam turbine inlet; from given T8_superheat_C + T_sat(P_steam)
        # We don't have T8 directly — check via state 8 enthalpy is reasonable
        # Instead check that T8_superheat given implies T8 < T4
        T8_superheat_C = q["given"].get("T8_superheat_C")
        P_steam_MPa = q["given"].get("P_steam_MPa")
        if T4 is not None and T8_superheat_C is not None and P_steam_MPa is not None:
            try:
                import CoolProp.CoolProp as CP
                T_sat_K = CP.PropsSI("T", "P", P_steam_MPa * 1e6, "Q", 0, "Water")
                T8_K = T_sat_K + T8_superheat_C
                checked += 1
                if T8_K >= T4 - 10:
                    issues.append(f"{qid}: T8={T8_K:.1f}K >= T4-10={T4-10:.1f}K (pinch violated)")
            except Exception as e:
                issues.append(f"{qid}: CoolProp error computing T_sat: {e}")

    ok = len(issues) == 0
    notes = f"Checked {checked} CCGT constraints"
    if issues:
        notes += f"; {len(issues)} issues: " + "; ".join(issues[:5])
    return ok, notes


# ---------------------------------------------------------------------------
# Check 7: NASA polynomial spot check
# ---------------------------------------------------------------------------

def check_nasa_spot(questions):
    """Call h_ideal_air() and s0_ideal_air() at canonical temperatures,
    compare to textbook values."""
    try:
        sys.path.insert(0, str(ROOT))
        from generation.cycle_state_generator import h_ideal_air, s0_ideal_air
    except ImportError as e:
        return False, f"Cannot import cycle_state_generator: {e}"

    issues = []
    # Textbook values: Cengel/Boles air table A-17 (per unit mass)
    # T(K), h(kJ/kg), s0(kJ/(kg·K))
    textbook = [
        (300,  300.19, 1.70203),
        (400,  400.98, 1.99194),
        (500,  503.02, 2.21952),
        (600,  607.02, 2.40902),
        (800,  821.95, 2.71787),
        (1000, 1046.04, 2.96770),
        (1200, 1277.79, 3.17888),
        (1500, 1635.80, 3.42892),
    ]

    checked = 0
    for T, h_ref, s0_ref in textbook:
        h_calc = h_ideal_air(T)
        s0_calc = s0_ideal_air(T)
        checked += 1

        h_err = abs(h_calc - h_ref)
        s0_err = abs(s0_calc - s0_ref)

        # NASA polynomials vs textbook: allow 0.5% relative error
        # (textbook values are rounded; NASA fit diverges slightly above ~1400K)
        h_rel = h_err / max(abs(h_ref), 1e-10) * 100
        s0_rel = s0_err / max(abs(s0_ref), 1e-10) * 100
        if h_rel > 0.5:
            issues.append(f"h({T}K): calc={h_calc:.2f} vs ref={h_ref:.2f}, err={h_rel:.3f}%")
        if s0_rel > 0.5:
            issues.append(f"s0({T}K): calc={s0_calc:.5f} vs ref={s0_ref:.5f}, err={s0_rel:.3f}%")

    ok = len(issues) == 0
    notes = f"Checked {checked} reference points"
    if issues:
        notes += f"; {len(issues)} deviations: " + "; ".join(issues[:5])
    else:
        notes += "; all within tolerance"
    return ok, notes


# ---------------------------------------------------------------------------
# Check 8: R-134a IIR reference state
# ---------------------------------------------------------------------------

def check_r134a_iir(questions):
    """Check IIR reference state for R-134a VCR questions.
    Verify h1 values are consistent with CoolProp (which uses IIR by default)."""
    issues = []
    checked = 0

    try:
        import CoolProp.CoolProp as CP
        # CoolProp R-134a default: IIR reference (h=200 kJ/kg, s=1 kJ/(kg·K) at 0°C sat liquid)
        h_ref_0C = CP.PropsSI("H", "T", 273.15, "Q", 0, "R134a") / 1000
        s_ref_0C = CP.PropsSI("S", "T", 273.15, "Q", 0, "R134a") / 1000
        checked += 1
        # IIR: h_f(0°C) = 200 kJ/kg, s_f(0°C) = 1.0 kJ/(kg·K)
        if abs(h_ref_0C - 200.0) > 1.0:
            issues.append(f"CoolProp h_f(0°C) = {h_ref_0C:.2f}, expected ~200 (IIR)")
        if abs(s_ref_0C - 1.0) > 0.01:
            issues.append(f"CoolProp s_f(0°C) = {s_ref_0C:.4f}, expected ~1.0 (IIR)")
    except Exception as e:
        return False, f"CoolProp R-134a error: {e}"

    # Check VCR questions mention IIR
    vcr_qs = [q for q in questions if q["cycle_type"].startswith("VCR")]
    iir_count = sum(1 for q in vcr_qs if "IIR" in q["question"])
    checked += 1
    if iir_count == 0:
        issues.append(f"No VCR questions mention IIR reference state (out of {len(vcr_qs)})")

    # Spot-check h1 for a VCR question
    for q in vcr_qs:
        exp = q["expected"]
        h1 = exp.get("h1", {}).get("value")
        if h1 is not None:
            checked += 1
            # h1 is saturated vapor at evaporator T — should be > 200 for R-134a
            if h1 < 100 or h1 > 500:
                issues.append(f"{q['id']}: h1={h1:.2f} out of plausible R-134a range")
            break

    ok = len(issues) == 0
    notes = f"Checked {checked} R-134a/IIR items"
    if issues:
        notes += f"; {len(issues)} issues: " + "; ".join(issues[:5])
    else:
        notes += "; IIR reference state consistent"
    return ok, notes


# ---------------------------------------------------------------------------
# Check 9: Variable vs constant cp (BRY-AV vs BRY-A comparison)
# ---------------------------------------------------------------------------

def check_variable_vs_constant_cp(questions):
    """Find BRY-AV and BRY-A questions with similar r_p and T3.
    Variable cp (BRY-AV) should give different eta_th than constant cp (BRY-A)."""
    bry_av = [q for q in questions if q["cycle_type"] == "BRY-AV"]
    bry_a = [q for q in questions if q["cycle_type"] == "BRY-A"]
    issues = []
    checked = 0

    if not bry_av or not bry_a:
        return False, "Missing BRY-AV or BRY-A questions"

    # Check that BRY-AV and BRY-A produce different eta_th for similar inputs
    for qv in bry_av:
        rv = qv["given"].get("r_p")
        T3v = qv["given"].get("T3_K")
        eta_v = qv["expected"].get("eta_th", {}).get("value")
        if rv is None or T3v is None or eta_v is None:
            continue

        for qa in bry_a:
            ra = qa["given"].get("r_p")
            T3a = qa["given"].get("T3_K")
            eta_a = qa["expected"].get("eta_th", {}).get("value")
            if ra is None or T3a is None or eta_a is None:
                continue

            # Similar r_p and T3
            if abs(rv - ra) < 2 and abs(T3v - T3a) < 100:
                checked += 1
                # Variable cp typically gives different (usually lower) eta_th
                # than constant cp at high T3 — they should NOT be identical
                if abs(eta_v - eta_a) < 0.001:
                    issues.append(
                        f"{qv['id']} vs {qa['id']}: eta_th identical "
                        f"({eta_v:.4f} vs {eta_a:.4f}), r_p={rv}/{ra}, T3={T3v}/{T3a}"
                    )
                break

    ok = len(issues) == 0
    if checked == 0:
        notes = "No comparable BRY-AV/BRY-A pairs found (different r_p/T3)"
    else:
        notes = f"Compared {checked} BRY-AV/BRY-A pairs"
        if issues:
            notes += f"; {len(issues)} identical eta_th: " + "; ".join(issues[:3])
        else:
            notes += "; eta_th values differ as expected"
    return ok, notes


# ---------------------------------------------------------------------------
# Check 10: Tolerance values match spec
# ---------------------------------------------------------------------------

def check_tolerances(questions):
    """Verify abs_tolerance values:
    - dimensionless (eta_th, COP_R, eta_combined, eta_II, COP_Carnot): 0.02
    - x4: 0.03
    - energy_balance_error*: 0.01
    - everything else: 0.5
    """
    issues = []
    checked = 0

    spec = {
        "eta_th": 0.02, "COP_R": 0.02, "eta_combined": 0.02,
        "eta_II": 0.02, "COP_Carnot": 0.02,
        "x4": 0.03,
    }
    balance_keys = {"energy_balance_error", "energy_balance_error_gas",
                    "energy_balance_error_steam"}

    for q in questions:
        for k, v in q["expected"].items():
            if not isinstance(v, dict) or "abs_tolerance" not in v:
                continue
            checked += 1
            actual_tol = v["abs_tolerance"]

            if k in spec:
                expected_tol = spec[k]
            elif k in balance_keys:
                expected_tol = 0.01
            else:
                expected_tol = 0.5

            if abs(actual_tol - expected_tol) > 1e-9:
                issues.append(f"{q['id']}: {k} abs_tol={actual_tol}, expected {expected_tol}")

    ok = len(issues) == 0
    notes = f"Checked {checked} tolerance values"
    if issues:
        notes += f"; {len(issues)} mismatches: " + "; ".join(issues[:5])
        if len(issues) > 5:
            notes += f" (+{len(issues)-5} more)"
    return ok, notes


# ---------------------------------------------------------------------------
# Check 11: Distribution — count by cycle, depth, fluid
# ---------------------------------------------------------------------------

def check_distribution(questions):
    """Count by cycle, depth, fluid; compare to expected."""
    expected_cycles = {
        "RNK-I": 2, "RNK-A": 15, "RNK-RH": 10,
        "BRY-I": 3, "BRY-A": 9, "BRY-AV": 6, "BRY-RG": 6, "BRY-RV": 4,
        "VCR-A": 15, "CCGT": 12,
    }
    expected_depths = {"A": 29, "B": 26, "C": 27}
    expected_fluids = {"Water": 27, "Air": 28, "R-134a": 15, "Air+Water": 12}
    expected_total = 82

    issues = []

    actual_total = len(questions)
    if actual_total != expected_total:
        issues.append(f"Total: {actual_total} vs expected {expected_total}")

    cycle_counts = Counter(q["cycle_type"] for q in questions)
    for ct, exp_n in expected_cycles.items():
        act_n = cycle_counts.get(ct, 0)
        if act_n != exp_n:
            issues.append(f"{ct}: {act_n} vs expected {exp_n}")

    depth_counts = Counter(q["depth"] for q in questions)
    for d, exp_n in expected_depths.items():
        act_n = depth_counts.get(d, 0)
        if act_n != exp_n:
            issues.append(f"Depth {d}: {act_n} vs expected {exp_n}")

    fluid_counts = Counter(q.get("fluid", "?") for q in questions)
    for fl, exp_n in expected_fluids.items():
        act_n = fluid_counts.get(fl, 0)
        if act_n != exp_n:
            issues.append(f"Fluid {fl}: {act_n} vs expected {exp_n}")

    ok = len(issues) == 0
    notes = f"Total={actual_total}, {len(cycle_counts)} cycle types, {len(depth_counts)} depths, {len(fluid_counts)} fluids"
    if issues:
        notes += f"; {len(issues)} mismatches: " + "; ".join(issues[:5])
    return ok, notes


# ---------------------------------------------------------------------------
# Check 12: Cross-provider ideal cycle scores
# ---------------------------------------------------------------------------

def check_cross_provider_ideal(questions, all_responses):
    """Check scores for RNK-I/BRY-I across providers — ideal cycles
    should be easiest, expect high scores."""
    ideal_ids = {q["id"] for q in questions if q["cycle_type"] in ("RNK-I", "BRY-I")}
    issues = []
    checked = 0

    for provider, responses in all_responses.items():
        resp_by_id = {r["id"]: r for r in responses}
        for qid in ideal_ids:
            r = resp_by_id.get(qid)
            if r is None:
                issues.append(f"{provider}: missing response for {qid}")
                continue
            checked += 1
            score = r.get("question_score", 0)
            if score < 0.5:
                issues.append(f"{provider}/{qid}: score={score:.2f} (low for ideal cycle)")

    ok = len(issues) == 0
    notes = f"Checked {checked} ideal-cycle responses across {len(all_responses)} providers"
    if issues:
        notes += f"; {len(issues)} low scores: " + "; ".join(issues[:5])
    else:
        notes += "; all ideal-cycle scores >= 0.5"
    return ok, notes


# ---------------------------------------------------------------------------
# Check 13: Scoring sanity — 0% <= scores <= 100%, no empty extractions
# ---------------------------------------------------------------------------

def check_scoring_sanity(all_responses):
    """Verify 0 <= question_score <= 1, no empty extractions."""
    issues = []
    warnings = []
    checked = 0

    for provider, responses in all_responses.items():
        for r in responses:
            checked += 1
            score = r.get("question_score")
            if score is None:
                issues.append(f"{provider}/{r['id']}: missing question_score")
            elif not (0 <= score <= 1.0 + 1e-9):
                issues.append(f"{provider}/{r['id']}: score={score:.4f} out of [0,1]")

            extracted = r.get("extracted")
            if extracted is None or (isinstance(extracted, dict) and len(extracted) == 0):
                # Empty extraction = model failed to produce parseable answer (warning, not error)
                warnings.append(f"{provider}/{r['id']}: empty extraction")

    ok = len(issues) == 0
    notes = f"Checked {checked} responses"
    if warnings:
        notes += f"; {len(warnings)} empty extractions (models failed to parse)"
    if issues:
        notes += f"; {len(issues)} errors: " + "; ".join(issues[:5])
        if len(issues) > 5:
            notes += f" (+{len(issues)-5} more)"
    return ok, notes


# ---------------------------------------------------------------------------
# Check 14: Duplicates / missing — unique IDs, correct pattern, 82 per provider
# ---------------------------------------------------------------------------

def check_duplicates_missing(questions, all_responses):
    """Verify unique question IDs, correct ID pattern, 82 per provider."""
    import re
    issues = []

    # Question IDs
    qids = [q["id"] for q in questions]
    if len(qids) != len(set(qids)):
        dupes = [qid for qid, cnt in Counter(qids).items() if cnt > 1]
        issues.append(f"Duplicate question IDs: {dupes[:5]}")

    # ID pattern: T3-{CYCLE}-{FLUID}-{DEPTH}-{NUM} or T3-{CYCLE}-{SUBTYPE}-{FLUID}-{DEPTH}-{NUM}
    pattern = re.compile(r"^T3-[A-Z]+-(?:[A-Z]+-)?[A-Z]+-[A-Z]+-\d{3}$")
    bad_ids = [qid for qid in qids if not pattern.match(qid)]
    if bad_ids:
        issues.append(f"Non-conforming IDs: {bad_ids[:5]}")

    # Provider response counts
    question_id_set = set(qids)
    for provider, responses in all_responses.items():
        rids = [r["id"] for r in responses]
        if len(responses) != 82:
            issues.append(f"{provider}: {len(responses)} responses, expected 82")
        if len(rids) != len(set(rids)):
            dupes = [rid for rid, cnt in Counter(rids).items() if cnt > 1]
            issues.append(f"{provider}: duplicate response IDs: {dupes[:3]}")
        missing = question_id_set - set(rids)
        extra = set(rids) - question_id_set
        if missing:
            issues.append(f"{provider}: missing {len(missing)} responses: {list(missing)[:3]}")
        if extra:
            issues.append(f"{provider}: {len(extra)} extra responses: {list(extra)[:3]}")

    ok = len(issues) == 0
    notes = f"{len(qids)} questions, {len(all_responses)} providers"
    if issues:
        notes += f"; {len(issues)} issues: " + "; ".join(issues[:5])
    return ok, notes


# ===========================================================================
# Main
# ===========================================================================

def main():
    print("=" * 72)
    print("ThermoQA Tier 3 — Pre-Publish Verification")
    print("=" * 72)
    print()

    # Load data
    print("Loading data...")
    questions = load_questions()
    print(f"  Questions: {len(questions)}")

    all_responses = {}
    all_summaries = {}
    for prov in PROVIDERS:
        resp_path = RESULTS_DIR / prov / "responses.jsonl"
        summ_path = RESULTS_DIR / prov / "summary.json"
        if resp_path.exists():
            all_responses[prov] = load_responses(prov)
            print(f"  {prov}: {len(all_responses[prov])} responses")
        else:
            print(f"  {prov}: responses.jsonl NOT FOUND")
        if summ_path.exists():
            all_summaries[prov] = load_summary(prov)

    print()

    # Run checks
    checks = [
        ("1. Energy balance",          lambda: check_energy_balance(questions)),
        ("2. Second law (s_gen>=0)",   lambda: check_second_law(questions)),
        ("3. Efficiency ranges",       lambda: check_efficiency_ranges(questions)),
        ("4. VCR x4 in (0,1)",        lambda: check_vcr_x4(questions)),
        ("5. No negative work/heat",   lambda: check_no_negative_work_heat(questions)),
        ("6. CCGT HRSG constraints",   lambda: check_ccgt_hrsg(questions)),
        ("7. NASA polynomial spot",    lambda: check_nasa_spot(questions)),
        ("8. R-134a IIR ref state",    lambda: check_r134a_iir(questions)),
        ("9. Var vs const cp",         lambda: check_variable_vs_constant_cp(questions)),
        ("10. Tolerance spec",         lambda: check_tolerances(questions)),
        ("11. Distribution",           lambda: check_distribution(questions)),
        ("12. Cross-provider ideal",   lambda: check_cross_provider_ideal(questions, all_responses)),
        ("13. Scoring sanity",         lambda: check_scoring_sanity(all_responses)),
        ("14. Duplicates/missing",     lambda: check_duplicates_missing(questions, all_responses)),
    ]

    results = []
    for name, fn in checks:
        try:
            ok, notes = fn()
            results.append((name, ok, notes))
        except Exception as e:
            results.append((name, False, f"ERROR: {e}"))

    # Print summary table
    print("-" * 72)
    print(f"{'Check':<30} {'Status':<8} {'Notes'}")
    print("-" * 72)

    fail_count = 0
    for name, ok, notes in results:
        status = "PASS" if ok else "FAIL"
        if not ok:
            fail_count += 1
        # Truncate notes for table display
        max_notes = 120
        display_notes = notes if len(notes) <= max_notes else notes[:max_notes] + "..."
        print(f"{name:<30} {status:<8} {display_notes}")

    print("-" * 72)

    # Print detailed issues for failures
    failures = [(name, notes) for name, ok, notes in results if not ok]
    if failures:
        print(f"\n{'='*72}")
        print(f"ISSUES ({fail_count} check(s) failed)")
        print(f"{'='*72}")
        for name, notes in failures:
            print(f"\n  {name}:")
            print(f"    {notes}")
    else:
        print(f"\nAll {len(checks)} checks passed.")

    print()

    # Provider score summary
    if all_summaries:
        print("-" * 72)
        print("Provider Score Summary")
        print("-" * 72)
        print(f"{'Provider':<14} {'Overall':>8} {'RNK':>8} {'BRY':>8} {'VCR':>8} {'CCGT':>8}")
        print("-" * 72)
        for prov in PROVIDERS:
            s = all_summaries.get(prov)
            if s is None:
                continue
            by_ct = s.get("by_cycle_type", {})
            print(f"{prov:<14} {s['overall_score']:>7.1%}"
                  f" {by_ct.get('RNK', {}).get('score', 0):>7.1%}"
                  f" {by_ct.get('BRY', {}).get('score', 0):>7.1%}"
                  f" {by_ct.get('VCR', {}).get('score', 0):>7.1%}"
                  f" {by_ct.get('CCGT', {}).get('score', 0):>7.1%}")
        print("-" * 72)

    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
