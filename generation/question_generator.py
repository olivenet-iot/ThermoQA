"""
Question generation pipeline for ThermoQA Tier 1 and Tier 2.

Orchestrates: templates -> param_sampler -> ground_truth -> JSON output.
"""

import json
import os
from datetime import datetime, timezone

from generation.ground_truth import compute_properties, get_coolprop_version, cross_verify
from generation.param_sampler import sample_params, sample_tier2_params, sample_tier3_params
from generation.templates.tier1_properties import (
    TIER1_TEMPLATES,
    TEMPLATE_COUNTS,
    get_templates_by_category,
)
from generation.templates.tier2_components import (
    TIER2_TEMPLATES,
    TIER2_TEMPLATE_COUNTS,
    FLUID_CODES,
    ComponentTemplate,
)

# Category code mapping
CATEGORY_CODES = {
    "subcooled_liquid": "SL",
    "saturated_liquid": "SF",
    "wet_steam": "WS",
    "saturated_vapor": "SV",
    "superheated_vapor": "SH",
    "supercritical": "SC",
    "phase_determination": "PD",
    "inverse_lookups": "IL",
}

# Scoring defaults
DEFAULT_TOLERANCE_PCT = 2.0
DEFAULT_ABS_TOLERANCE = 0.5

# Answer format hints: map expected keys to symbol + unit hint
ANSWER_HINTS = {
    "h_kJ_kg": "h = ___ kJ/kg",
    "s_kJ_kgK": "s = ___ kJ/(kg\u00b7K)",
    "v_m3_kg": "v = ___ m\u00b3/kg",
    "u_kJ_kg": "u = ___ kJ/kg",
    "rho_kg_m3": "rho = ___ kg/m\u00b3",
    "T_C": "T = ___ \u00b0C",
    "T_sat_C": "T_sat = ___ \u00b0C",
    "P_kPa": "P = ___ kPa",
    "P_sat_kPa": "P_sat = ___ kPa",
    "h_f_kJ_kg": "h_f = ___ kJ/kg",
    "h_g_kJ_kg": "h_g = ___ kJ/kg",
    "s_f_kJ_kgK": "s_f = ___ kJ/(kg\u00b7K)",
    "s_g_kJ_kgK": "s_g = ___ kJ/(kg\u00b7K)",
    "v_f_m3_kg": "v_f = ___ m\u00b3/kg",
    "v_g_m3_kg": "v_g = ___ m\u00b3/kg",
    "x": "x = ___",
    "phase_name": "Phase: ___",
}

# Phase aliases for exact-match scoring
PHASE_ALIASES = {
    "subcooled_liquid": [
        "subcooled", "compressed liquid", "subcooled liquid", "liquid",
        "compressed water",
    ],
    "superheated_vapor": [
        "superheated", "superheated vapor", "superheated steam",
        "vapor", "gas", "steam",
    ],
    "wet_steam": [
        "two-phase", "two phase", "wet steam", "mixture",
        "liquid-vapor mixture", "saturated mixture", "two-phase mixture",
    ],
    "supercritical": [
        "supercritical", "supercritical fluid",
    ],
    "saturated_liquid": [
        "saturated liquid", "saturated water",
    ],
    "saturated_vapor": [
        "saturated vapor", "saturated steam", "dry saturated steam",
    ],
}


def _format_expected(prop_key: str, result: dict) -> dict:
    """Format a single property result for the expected output JSON."""
    if result.get("type") == "exact_match":
        return {
            "value": result["value"],
            "type": "exact_match",
            "acceptable_aliases": PHASE_ALIASES.get(result["value"], []),
        }
    abs_tol = 0.03 if prop_key == "x" else DEFAULT_ABS_TOLERANCE
    return {
        "value": result["value"],
        "unit": result["unit"],
        "tolerance_pct": DEFAULT_TOLERANCE_PCT,
        "abs_tolerance": abs_tol,
    }


def _format_question_text(template, params: dict, target_properties: list | None = None) -> str:
    """Select and format a question template string with parameters.

    If target_properties is provided, appends an answer format hint line.
    """
    # Use a deterministic index based on parameter values
    idx = hash(frozenset(params.items())) % len(template.question_templates)

    # Try templates starting from idx, cycling through all options
    templates = template.question_templates
    text = None
    for i in range(len(templates)):
        tmpl = templates[(idx + i) % len(templates)]
        try:
            text = tmpl.format(**params)
            break
        except (KeyError, ValueError, IndexError):
            continue

    if text is None:
        # Last resort: manual substitution
        text = templates[0]
        for k, v in params.items():
            text = text.replace("{" + k + "}", str(v))

    # Append answer format hint
    if target_properties:
        hints = [ANSWER_HINTS[k] for k in target_properties if k in ANSWER_HINTS]
        if hints:
            text += "\n\nReport your answers as:\n" + "\n".join(hints)

    return text


def generate_tier1_questions(output_dir: str, total_target: int = 110,
                              seed: int = 42) -> list[dict]:
    """
    Generate all Tier 1 questions.

    Returns list of question dicts and writes to output_dir.
    """
    questions = []
    category_counters = {}
    warnings = []
    coolprop_version = get_coolprop_version()
    generated_at = datetime.now(timezone.utc).isoformat()

    for template in TIER1_TEMPLATES:
        count = TEMPLATE_COUNTS.get(template.template_id, 0)
        if count == 0:
            continue

        cat = template.category
        code = CATEGORY_CODES[cat]
        if cat not in category_counters:
            category_counters[cat] = 0

        # Use a per-template seed for reproducibility
        template_seed = seed + hash(template.template_id) % 10000
        param_sets = sample_params(template, count, seed=template_seed)

        if len(param_sets) < count:
            warnings.append(
                f"{template.template_id}: requested {count}, got {len(param_sets)} params"
            )

        for params in param_sets:
            category_counters[cat] += 1
            num = category_counters[cat]
            question_id = f"T1-{code}-{num:03d}"

            # Compute ground truth
            try:
                results = compute_properties(
                    params, template.target_properties, fluid="Water"
                )
            except Exception as e:
                warnings.append(f"{question_id}: ground truth failed: {e}")
                category_counters[cat] -= 1
                continue

            # Cross-verify
            verified = cross_verify(params, results, fluid="Water")

            # Format question text
            question_text = _format_question_text(template, params, template.target_properties)

            # Build expected dict
            expected = {}
            for prop_key in template.target_properties:
                if prop_key in results:
                    expected[prop_key] = _format_expected(prop_key, results[prop_key])

            # Build given dict with units
            given = {"fluid": "Water"}
            for k, v in params.items():
                given[k] = v

            question = {
                "id": question_id,
                "tier": 1,
                "category": cat,
                "subcategory": template.subcategory,
                "difficulty": template.difficulty,
                "question": question_text,
                "given": given,
                "expected": expected,
                "metadata": {
                    "template_id": template.template_id,
                    "coolprop_version": coolprop_version,
                    "generated_at": generated_at,
                    "verified": verified,
                },
            }
            questions.append(question)

    # Write output
    os.makedirs(output_dir, exist_ok=True)
    jsonl_path = os.path.join(output_dir, "questions.jsonl")
    with open(jsonl_path, "w") as f:
        for q in questions:
            f.write(json.dumps(q, ensure_ascii=False) + "\n")

    # Build metadata
    cat_dist = {}
    for q in questions:
        c = q["category"]
        cat_dist[c] = cat_dist.get(c, 0) + 1

    difficulty_dist = {}
    for q in questions:
        d = q["difficulty"]
        difficulty_dist[d] = difficulty_dist.get(d, 0) + 1

    metadata = {
        "total_questions": len(questions),
        "target": total_target,
        "tier": 1,
        "fluid": "Water",
        "coolprop_version": coolprop_version,
        "generated_at": generated_at,
        "seed": seed,
        "category_distribution": cat_dist,
        "difficulty_distribution": difficulty_dist,
        "warnings": warnings,
        "scoring": {
            "numerical_tolerance_pct": DEFAULT_TOLERANCE_PCT,
            "absolute_tolerance": DEFAULT_ABS_TOLERANCE,
            "phase_matching": "exact_match_with_aliases",
        },
    }
    meta_path = os.path.join(output_dir, "metadata.json")
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    return questions, warnings, metadata


# ══════════════════════════════════════════════════════════
# TIER 2: Component Analysis Question Generation
# ══════════════════════════════════════════════════════════

# Component code mapping
COMPONENT_CODES = {
    "turbine": "TRB",
    "compressor": "CMP",
    "pump": "PMP",
    "heat_exchanger": "HX",
    "boiler": "BLR",
    "mixing_chamber": "MIX",
    "nozzle": "NOZ",
}

# Answer hint mapping: step_id -> formatted hint
TIER2_ANSWER_HINTS = {
    "h1": "h_1 = ___ kJ/kg",
    "s1": "s_1 = ___ kJ/(kg·K)",
    "h2s": "h_2s = ___ kJ/kg",
    "h2": "h_2 = ___ kJ/kg",
    "s2": "s_2 = ___ kJ/(kg·K)",
    "w_out": "w_out = ___ kJ/kg",
    "w_in": "w_in = ___ kJ/kg",
    "s_gen": "s_gen = ___ kJ/(kg·K)",
    "x_dest": "x_dest = ___ kJ/kg",
    "eta_II": "η_II = ___",
    "h_in": "h_in = ___ kJ/kg",
    "h_out": "h_out = ___ kJ/kg",
    "s_in": "s_in = ___ kJ/(kg·K)",
    "s_out": "s_out = ___ kJ/(kg·K)",
    "q_in": "q_in = ___ kJ/kg",
    "h_h_in": "h_h_in = ___ kJ/kg",
    "h_h_out": "h_h_out = ___ kJ/kg",
    "h_c_in": "h_c_in = ___ kJ/kg",
    "h_c_out": "h_c_out = ___ kJ/kg",
    "Q_dot": "Q̇ = ___ kW",
    "T_c_out": "T_c_out = ___ °C",
    "s_h_in": "s_h_in = ___ kJ/(kg·K)",
    "s_h_out": "s_h_out = ___ kJ/(kg·K)",
    "s_c_in": "s_c_in = ___ kJ/(kg·K)",
    "s_c_out": "s_c_out = ___ kJ/(kg·K)",
    "S_gen_dot": "Ṡ_gen = ___ kW/K",
    "X_dest_dot": "Ẋ_dest = ___ kW",
    "h3": "h_3 = ___ kJ/kg",
    "T3": "T_3 = ___ °C",
    "m3": "ṁ_3 = ___ kg/s",
    "s3": "s_3 = ___ kJ/(kg·K)",
    "V2": "V_2 = ___ m/s",
}


def _format_tier2_question_text(template: ComponentTemplate, params: dict) -> str:
    """Format a Tier 2 question with parameter substitution and answer hints."""
    # Build format dict with derived values
    fmt = dict(params)
    # Add percentage versions of efficiencies
    if "eta_s" in params:
        fmt["eta_s_pct"] = round(params["eta_s"] * 100, 1)
    if "eta_nozzle" in params:
        fmt["eta_nozzle_pct"] = round(params["eta_nozzle"] * 100, 1)

    # Select template phrasing deterministically
    idx = hash(frozenset(params.items())) % len(template.question_templates)
    templates = template.question_templates
    text = None
    for i in range(len(templates)):
        tmpl = templates[(idx + i) % len(templates)]
        try:
            text = tmpl.format(**fmt)
            break
        except (KeyError, ValueError, IndexError):
            continue

    if text is None:
        text = templates[0]
        for k, v in fmt.items():
            text = text.replace("{" + k + "}", str(v))

    # Append answer format hints
    step_ids = [s["id"] for s in template.steps]
    hints = [TIER2_ANSWER_HINTS[sid] for sid in step_ids if sid in TIER2_ANSWER_HINTS]
    if hints:
        text += "\n\nPresent your final answers in the following format:\n" + "\n".join(hints)

    return text


def _compute_tier2_ground_truth(template: ComponentTemplate, params: dict):
    """Compute ground truth for a Tier 2 question using state_generator."""
    from generation.state_generator import (
        generate_turbine_state, generate_compressor_state, generate_pump_state,
        generate_hx_state, generate_boiler_state, generate_mixer_state,
        generate_nozzle_state,
    )

    comp = template.component
    depth = template.depth
    fluid = template.fluid

    if comp == "turbine":
        return generate_turbine_state(
            params["T1_C"], params["P1_MPa"], params["P2_MPa"],
            params["eta_s"], fluid, depth,
        )
    elif comp == "compressor":
        return generate_compressor_state(
            params["T1_C"], params["P1_MPa"], params["P2_MPa"],
            params["eta_s"], fluid, depth,
        )
    elif comp == "pump":
        return generate_pump_state(
            params["T1_C"], params["P1_MPa"], params["P2_MPa"],
            params["eta_s"], depth,
        )
    elif comp == "heat_exchanger":
        fluid_hot = "Water"
        fluid_cold = "R134a" if "R" in template.template_id else "Water"
        return generate_hx_state(
            params["T_h_in"], params["T_h_out"], params["T_c_in"],
            params["P_h_MPa"], params["P_c_MPa"],
            params["m_h"], params["m_c"],
            fluid_hot, fluid_cold, depth,
        )
    elif comp == "boiler":
        return generate_boiler_state(
            params["T_in_C"], params["P_MPa"], params["T_out_C"],
            params["T_source_K"], depth,
        )
    elif comp == "mixing_chamber":
        return generate_mixer_state(
            params["T1_C"], params["T2_C"], params["P_MPa"],
            params["m1"], params["m2"], depth,
        )
    elif comp == "nozzle":
        return generate_nozzle_state(
            params["T1_C"], params["P1_MPa"], params["P2_MPa"],
            params["V1"], params["eta_nozzle"], fluid, depth,
        )
    else:
        raise ValueError(f"Unknown component: {comp}")


def generate_tier2_questions(output_dir: str, total_target: int = 100,
                              seed: int = 42):
    """
    Generate all Tier 2 questions.

    Returns (questions, warnings, metadata).
    """
    questions = []
    component_counters = {}  # "TRB-W" -> int
    warnings = []
    coolprop_version = get_coolprop_version()
    generated_at = datetime.now(timezone.utc).isoformat()

    for template in TIER2_TEMPLATES:
        count = TIER2_TEMPLATE_COUNTS.get(template.template_id, 0)
        if count == 0:
            continue

        comp_code = COMPONENT_CODES[template.component]
        fluid_code = FLUID_CODES.get(template.fluid, "W")
        counter_key = f"{comp_code}-{template.depth}{fluid_code}"
        if counter_key not in component_counters:
            component_counters[counter_key] = 0

        # Per-template seed for reproducibility
        template_seed = seed + hash(template.template_id) % 10000
        try:
            param_sets = sample_tier2_params(
                template.template_id, count, seed=template_seed
            )
        except Exception as e:
            warnings.append(f"{template.template_id}: sampling failed: {e}")
            continue

        if len(param_sets) < count:
            warnings.append(
                f"{template.template_id}: requested {count}, got {len(param_sets)} params"
            )

        for params in param_sets:
            component_counters[counter_key] += 1
            num = component_counters[counter_key]
            question_id = f"T2-{comp_code}-{template.depth}{fluid_code}-{num:03d}"

            # Compute ground truth via state_generator
            try:
                state = _compute_tier2_ground_truth(template, params)
            except Exception as e:
                warnings.append(f"{question_id}: ground truth failed: {e}")
                component_counters[counter_key] -= 1
                continue

            # Skip questions that failed validation
            if state.warnings:
                for w in state.warnings:
                    warnings.append(f"{question_id}: {w}")
                if not state.validated:
                    component_counters[counter_key] -= 1
                    continue

            # Format question text
            question_text = _format_tier2_question_text(template, params)

            # Build expected dict (flat, keyed by step_id)
            expected = {}
            for step in state.steps:
                expected[step.step_id] = {
                    "value": step.value,
                    "unit": step.unit,
                    "tolerance_pct": step.tolerance_pct,
                    "abs_tolerance": step.abs_tolerance,
                }

            # Build steps list (ordering + weights for scorer)
            steps_list = [
                {"id": step.step_id, "weight": step.weight, "unit": step.unit}
                for step in state.steps
            ]

            # Build given dict
            given = dict(params)
            given["fluid"] = template.fluid

            question = {
                "id": question_id,
                "tier": 2,
                "component": template.component,
                "depth": template.depth,
                "fluid": template.fluid,
                "difficulty": template.difficulty,
                "question": question_text,
                "given": given,
                "expected": expected,
                "steps": steps_list,
                "metadata": {
                    "template_id": template.template_id,
                    "coolprop_version": coolprop_version,
                    "generated_at": generated_at,
                    "validated": state.validated,
                },
            }
            questions.append(question)

    # Write output
    os.makedirs(output_dir, exist_ok=True)
    jsonl_path = os.path.join(output_dir, "questions.jsonl")
    with open(jsonl_path, "w") as f:
        for q in questions:
            f.write(json.dumps(q, ensure_ascii=False) + "\n")

    # Build metadata
    comp_dist = {}
    for q in questions:
        c = q["component"]
        comp_dist[c] = comp_dist.get(c, 0) + 1

    depth_dist = {}
    for q in questions:
        d = q["depth"]
        depth_dist[d] = depth_dist.get(d, 0) + 1

    fluid_dist = {}
    for q in questions:
        f = q["fluid"]
        fluid_dist[f] = fluid_dist.get(f, 0) + 1

    difficulty_dist = {}
    for q in questions:
        d = q["difficulty"]
        difficulty_dist[d] = difficulty_dist.get(d, 0) + 1

    metadata = {
        "total_questions": len(questions),
        "target": total_target,
        "tier": 2,
        "working_fluids": ["Water", "R134a", "Air"],
        "coolprop_version": coolprop_version,
        "generated_at": generated_at,
        "seed": seed,
        "component_distribution": comp_dist,
        "depth_distribution": depth_dist,
        "fluid_distribution": fluid_dist,
        "difficulty_distribution": difficulty_dist,
        "warnings": warnings,
        "scoring": {
            "type": "weighted_step",
            "numerical_tolerance_pct": DEFAULT_TOLERANCE_PCT,
            "absolute_tolerance": DEFAULT_ABS_TOLERANCE,
        },
    }
    meta_path = os.path.join(output_dir, "metadata.json")
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    return questions, warnings, metadata


# ══════════════════════════════════════════════════════════
# TIER 3: Cycle Analysis Question Generation
# ══════════════════════════════════════════════════════════

from generation.templates.tier3_cycles import (
    TIER3_TEMPLATES,
    TIER3_TEMPLATE_COUNTS,
    TIER3_FLUID_CODES,
    CycleTemplate,
)

TIER3_ANSWER_HINTS = {
    "h1": "h₁ = ___ kJ/kg", "h2": "h₂ = ___ kJ/kg", "h3": "h₃ = ___ kJ/kg",
    "h4": "h₄ = ___ kJ/kg", "h5": "h₅ = ___ kJ/kg", "h6": "h₆ = ___ kJ/kg",
    "h2s": "h₂s = ___ kJ/kg", "h4s": "h₄s = ___ kJ/kg", "h5s": "h₅s = ___ kJ/kg",
    "s1": "s₁ = ___ kJ/(kg·K)", "s2": "s₂ = ___ kJ/(kg·K)",
    "s3": "s₃ = ___ kJ/(kg·K)", "s4": "s₄ = ___ kJ/(kg·K)",
    "s5": "s₅ = ___ kJ/(kg·K)", "s6": "s₆ = ___ kJ/(kg·K)",
    "ef1": "ef₁ = ___ kJ/kg", "ef2": "ef₂ = ___ kJ/kg",
    "ef3": "ef₃ = ___ kJ/kg", "ef4": "ef₄ = ___ kJ/kg",
    "ef5": "ef₅ = ___ kJ/kg", "ef6": "ef₆ = ___ kJ/kg",
    "w_pump": "w_pump = ___ kJ/kg", "w_comp": "w_comp = ___ kJ/kg",
    "w_turb": "w_turb = ___ kJ/kg", "w_HPT": "w_HPT = ___ kJ/kg",
    "w_LPT": "w_LPT = ___ kJ/kg", "w_net": "w_net = ___ kJ/kg",
    "q_in": "q_in = ___ kJ/kg", "q_L": "q_L = ___ kJ/kg", "q_H": "q_H = ___ kJ/kg",
    "eta_th": "η_th = ___", "COP_R": "COP_R = ___",
    "COP_Carnot": "COP_Carnot = ___", "eta_II": "η_II = ___", "x4": "x₄ = ___",
    "W_dot_net": "Ẇ_net = ___ kW", "W_dot_comp": "Ẇ_comp = ___ kW",
    "Q_dot_L": "Q̇_L = ___ kW",
    "s_gen_pump": "s_gen,pump = ___ kJ/(kg·K)", "s_gen_boiler": "s_gen,boiler = ___ kJ/(kg·K)",
    "s_gen_turb": "s_gen,turb = ___ kJ/(kg·K)", "s_gen_cond": "s_gen,cond = ___ kJ/(kg·K)",
    "s_gen_HPT": "s_gen,HPT = ___ kJ/(kg·K)", "s_gen_LPT": "s_gen,LPT = ___ kJ/(kg·K)",
    "s_gen_reheater": "s_gen,reheater = ___ kJ/(kg·K)",
    "s_gen_comp": "s_gen,comp = ___ kJ/(kg·K)", "s_gen_cc": "s_gen,cc = ___ kJ/(kg·K)",
    "s_gen_hr": "s_gen,hr = ___ kJ/(kg·K)", "s_gen_regen": "s_gen,regen = ___ kJ/(kg·K)",
    "s_gen_throttle": "s_gen,throttle = ___ kJ/(kg·K)",
    "s_gen_evap": "s_gen,evap = ___ kJ/(kg·K)", "s_gen_total": "s_gen,total = ___ kJ/(kg·K)",
    "x_dest_pump": "x_dest,pump = ___ kJ/kg", "x_dest_boiler": "x_dest,boiler = ___ kJ/kg",
    "x_dest_turb": "x_dest,turb = ___ kJ/kg", "x_dest_cond": "x_dest,cond = ___ kJ/kg",
    "x_dest_HPT": "x_dest,HPT = ___ kJ/kg", "x_dest_LPT": "x_dest,LPT = ___ kJ/kg",
    "x_dest_reheater": "x_dest,reheater = ___ kJ/kg",
    "x_dest_comp": "x_dest,comp = ___ kJ/kg", "x_dest_cc": "x_dest,cc = ___ kJ/kg",
    "x_dest_hr": "x_dest,hr = ___ kJ/kg", "x_dest_regen": "x_dest,regen = ___ kJ/kg",
    "x_dest_throttle": "x_dest,throttle = ___ kJ/kg",
    "x_dest_evap": "x_dest,evap = ___ kJ/kg", "x_dest_total": "x_dest,total = ___ kJ/kg",
    # Variable cp temperatures
    "T2": "T₂ = ___ K", "T4": "T₄ = ___ K", "T5": "T₅ = ___ K",
    # States 7-9 for CCGT
    "h7": "h₇ = ___ kJ/kg", "h7s": "h₇s = ___ kJ/kg",
    "h8": "h₈ = ___ kJ/kg", "h9": "h₉ = ___ kJ/kg", "h9s": "h₉s = ___ kJ/kg",
    "s7": "s₇ = ___ kJ/(kg·K)", "s8": "s₈ = ___ kJ/(kg·K)", "s9": "s₉ = ___ kJ/(kg·K)",
    "ef7": "ef₇ = ___ kJ/kg", "ef8": "ef₈ = ___ kJ/kg", "ef9": "ef₉ = ___ kJ/kg",
    # CCGT-specific
    "m_dot_steam": "ṁ_steam = ___ kg/s",
    "w_gas_turb": "w_gas_turb = ___ kJ/kg", "w_steam_turb": "w_steam_turb = ___ kJ/kg",
    "q_combustion": "q_combustion = ___ kJ/kg",
    "W_net_combined": "W_net_combined = ___ kW",
    "eta_combined": "η_combined = ___",
    "eta_II_combined": "η_II_combined = ___",
    # CCGT s_gen
    "s_gen_gas_turb": "s_gen,gas_turb = ___ kJ/(kg·K)",
    "s_gen_steam_turb": "s_gen,steam_turb = ___ kJ/(kg·K)",
    "s_gen_HRSG": "s_gen,HRSG = ___ kJ/(kg·K)",
    # CCGT x_dest
    "x_dest_gas_turb": "x_dest,gas_turb = ___ kJ/kg",
    "x_dest_steam_turb": "x_dest,steam_turb = ___ kJ/kg",
    "x_dest_HRSG": "x_dest,HRSG = ___ kJ/kg",
    # Consistency
    "energy_balance_error": "energy_balance_error = ___",
    "energy_balance_error_gas": "energy_balance_error_gas = ___",
    "energy_balance_error_steam": "energy_balance_error_steam = ___",
    "hrsg_balance_error": "hrsg_balance_error = ___",
}


def _extract_tier3_steps(template: CycleTemplate, result: dict) -> dict:
    """Map cycle generator output to flat step_id -> value dict."""
    states = result["states"]
    derived = result["derived"]
    values = {}

    for step in template.steps:
        sid = step["id"]
        val = None
        if sid.startswith("h") and sid[1:].isdigit():
            val = states.get(int(sid[1:]), {}).get("h")
        elif sid.startswith("s") and len(sid) == 2 and sid[1:].isdigit():
            val = states.get(int(sid[1:]), {}).get("s")
        elif sid.startswith("ef") and sid[2:].isdigit():
            val = states.get(int(sid[2:]), {}).get("ef")
        elif sid in ("h2s", "h4s", "h5s", "h6s", "h7s", "h9s"):
            val = states.get(sid[1:], {}).get("h")
        elif sid.startswith("T") and sid[1:].isdigit():
            state_num = int(sid[1:])
            val = derived.get(f"T{state_num}_K")
            if val is None:
                val = states.get(state_num, {}).get("T_K")
        else:
            val = derived.get(sid)

        if val is not None:
            values[sid] = val

    return values


def _format_tier3_question_text(template: CycleTemplate, params: dict) -> str:
    """Format a Tier 3 question with parameter substitution and answer hints."""
    fmt = dict(params)
    for key in ("eta_pump", "eta_turb", "eta_comp", "eta_HPT", "eta_LPT", "eta_gas_turb", "eta_steam_turb"):
        if key in params:
            fmt[f"{key}_pct"] = round(params[key] * 100, 1)
    if "epsilon_regen" in params:
        fmt["epsilon_regen_pct"] = round(params["epsilon_regen"] * 100, 1)
    for key in ("T_source_K", "T_sink_K", "T_H_K", "T_L_K"):
        if key in params:
            fmt[key] = round(params[key], 1)

    idx = hash(frozenset(params.items())) % len(template.question_templates)
    templates = template.question_templates
    text = None
    for i in range(len(templates)):
        tmpl = templates[(idx + i) % len(templates)]
        try:
            text = tmpl.format(**fmt)
            break
        except (KeyError, ValueError, IndexError):
            continue

    if text is None:
        text = templates[0]
        for k, v in fmt.items():
            text = text.replace("{" + k + "}", str(v))

    step_ids = [s["id"] for s in template.steps]
    hints = [TIER3_ANSWER_HINTS[sid] for sid in step_ids if sid in TIER3_ANSWER_HINTS]
    if hints:
        text += "\n\nPresent your final answers in the following format:\n" + "\n".join(hints)

    return text


def generate_tier3_questions(output_dir: str, total_target: int = 82,
                              seed: int = 42, cycle_filter: str | None = None):
    """Generate all Tier 3 questions. Returns (questions, warnings, metadata)."""
    from generation.cycle_state_generator import generate_cycle

    questions = []
    cycle_counters = {}
    warnings = []
    coolprop_version = get_coolprop_version()
    generated_at = datetime.now(timezone.utc).isoformat()

    tmpl_list = TIER3_TEMPLATES
    if cycle_filter:
        tmpl_list = [t for t in tmpl_list if t.cycle_type == cycle_filter]

    for template in tmpl_list:
        count = TIER3_TEMPLATE_COUNTS.get(template.template_id, 0)
        if count == 0:
            continue

        counter_key = f"{template.cycle_type}-{template.fluid_code}-{template.depth}"
        if counter_key not in cycle_counters:
            cycle_counters[counter_key] = 0

        template_seed = seed + hash(template.template_id) % 10000
        try:
            param_sets = sample_tier3_params(template.template_id, count, seed=template_seed)
        except Exception as e:
            warnings.append(f"{template.template_id}: sampling failed: {e}")
            continue

        if len(param_sets) < count:
            warnings.append(f"{template.template_id}: requested {count}, got {len(param_sets)} params")

        for params in param_sets:
            cycle_counters[counter_key] += 1
            num = cycle_counters[counter_key]
            qid = f"T3-{template.cycle_type}-{template.fluid_code}-{template.depth}-{num:03d}"

            try:
                result = generate_cycle(template.cycle_type, params)
            except Exception as e:
                warnings.append(f"{qid}: ground truth failed: {e}")
                cycle_counters[counter_key] -= 1
                continue

            if not result["meta"]["is_valid"]:
                for note in result["meta"]["validation_notes"]:
                    warnings.append(f"{qid}: {note}")
                cycle_counters[counter_key] -= 1
                continue

            step_values = _extract_tier3_steps(template, result)
            question_text = _format_tier3_question_text(template, params)

            expected = {}
            consistency_steps = {"energy_balance_error", "energy_balance_error_gas",
                                 "energy_balance_error_steam", "hrsg_balance_error"}
            dimensionless_steps = {"eta_th", "eta_combined", "eta_II",
                                   "COP_R", "COP_Carnot"}
            for step in template.steps:
                sid = step["id"]
                if sid in step_values:
                    if sid in consistency_steps:
                        expected[sid] = {
                            "value": step_values[sid],
                            "unit": step["unit"],
                            "tolerance_pct": DEFAULT_TOLERANCE_PCT,
                            "abs_tolerance": 0.01,
                        }
                    elif sid in dimensionless_steps:
                        expected[sid] = {
                            "value": step_values[sid],
                            "unit": step["unit"],
                            "tolerance_pct": DEFAULT_TOLERANCE_PCT,
                            "abs_tolerance": 0.02,
                        }
                    else:
                        expected[sid] = {
                            "value": step_values[sid],
                            "unit": step["unit"],
                            "tolerance_pct": DEFAULT_TOLERANCE_PCT,
                            "abs_tolerance": 0.03 if sid == "x4" else DEFAULT_ABS_TOLERANCE,
                        }

            steps_list = [
                {"id": step["id"], "weight": step["weight"], "unit": step["unit"]}
                for step in template.steps if step["id"] in step_values
            ]

            given = dict(params)
            given["fluid"] = template.fluid
            if template.fluid == "Air+Water":
                given["fluid_gas"] = "Air"
                given["fluid_steam"] = "Water"

            questions.append({
                "id": qid, "tier": 3,
                "cycle_type": template.cycle_type, "depth": template.depth,
                "fluid": template.fluid, "difficulty": template.difficulty,
                "question": question_text, "given": given,
                "expected": expected, "steps": steps_list,
                "metadata": {"template_id": template.template_id,
                              "coolprop_version": coolprop_version,
                              "generated_at": generated_at},
            })

    # Write output
    os.makedirs(output_dir, exist_ok=True)
    with open(os.path.join(output_dir, "questions.jsonl"), "w") as f:
        for q in questions:
            f.write(json.dumps(q, ensure_ascii=False) + "\n")

    cycle_dist = {}
    depth_dist = {}
    fluid_dist = {}
    difficulty_dist = {}
    for q in questions:
        cycle_dist[q["cycle_type"]] = cycle_dist.get(q["cycle_type"], 0) + 1
        depth_dist[q["depth"]] = depth_dist.get(q["depth"], 0) + 1
        fluid_dist[q["fluid"]] = fluid_dist.get(q["fluid"], 0) + 1
        difficulty_dist[q["difficulty"]] = difficulty_dist.get(q["difficulty"], 0) + 1

    metadata = {
        "total_questions": len(questions), "target": total_target, "tier": 3,
        "working_fluids": ["Water", "Air", "R-134a"],
        "coolprop_version": coolprop_version, "generated_at": generated_at, "seed": seed,
        "cycle_distribution": cycle_dist, "depth_distribution": depth_dist,
        "fluid_distribution": fluid_dist, "difficulty_distribution": difficulty_dist,
        "warnings": warnings,
        "scoring": {"type": "weighted_step",
                    "numerical_tolerance_pct": DEFAULT_TOLERANCE_PCT,
                    "absolute_tolerance": DEFAULT_ABS_TOLERANCE},
    }
    with open(os.path.join(output_dir, "metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    return questions, warnings, metadata
