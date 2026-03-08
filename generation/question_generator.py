"""
Question generation pipeline for ThermoQA Tier 1 and Tier 2.

Orchestrates: templates -> param_sampler -> ground_truth -> JSON output.
"""

import json
import os
from datetime import datetime, timezone

from generation.ground_truth import compute_properties, get_coolprop_version, cross_verify
from generation.param_sampler import sample_params, sample_tier2_params
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
