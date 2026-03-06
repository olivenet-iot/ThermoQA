"""
Question generation pipeline for ThermoQA Tier 1.

Orchestrates: templates -> param_sampler -> ground_truth -> JSON output.
"""

import json
import os
from datetime import datetime, timezone

from generation.ground_truth import compute_properties, get_coolprop_version, cross_verify
from generation.param_sampler import sample_params
from generation.templates.tier1_properties import (
    TIER1_TEMPLATES,
    TEMPLATE_COUNTS,
    get_templates_by_category,
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
    return {
        "value": result["value"],
        "unit": result["unit"],
        "tolerance_pct": DEFAULT_TOLERANCE_PCT,
        "abs_tolerance": DEFAULT_ABS_TOLERANCE,
    }


def _format_question_text(template, params: dict) -> str:
    """Select and format a question template string with parameters."""
    # Use a deterministic index based on parameter values
    idx = hash(frozenset(params.items())) % len(template.question_templates)

    # Try templates starting from idx, cycling through all options
    templates = template.question_templates
    for i in range(len(templates)):
        tmpl = templates[(idx + i) % len(templates)]
        try:
            return tmpl.format(**params)
        except (KeyError, ValueError, IndexError):
            continue

    # Last resort: manual substitution
    result = templates[0]
    for k, v in params.items():
        result = result.replace("{" + k + "}", str(v))
    return result


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
            question_text = _format_question_text(template, params)

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
