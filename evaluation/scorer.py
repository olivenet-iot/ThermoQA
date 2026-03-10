"""
Score extracted values against ground truth for ThermoQA.

Two levels: per-question (QuestionResult) and per-dataset (DatasetResults).
"""

import json
from dataclasses import dataclass, field

from evaluation.extractor import extract_properties


@dataclass
class PropertyResult:
    prop_key: str
    expected: float | str
    extracted: float | str | None
    passed: bool
    error_pct: float | None  # relative error for numerics, None for phase/missing
    error_type: str  # "correct", "wrong", "missing"


@dataclass
class QuestionResult:
    question_id: str
    category: str
    subcategory: str
    difficulty: str
    n_properties: int
    n_correct: int
    score: float  # n_correct / n_properties
    property_results: list[PropertyResult]


@dataclass
class DatasetResults:
    total_questions: int
    total_properties: int
    total_correct_properties: int
    mean_question_score: float
    property_accuracy: float
    per_category: dict  # cat -> {n_questions, mean_score, n_props, n_correct, accuracy}
    per_difficulty: dict  # diff -> {n_questions, mean_score}
    per_property_key: dict  # key -> {n_total, n_correct, n_missing, accuracy, mean_error_pct}
    question_results: list[QuestionResult]


def check_numeric(
    expected: float,
    actual: float,
    tolerance_pct: float = 2.0,
    abs_tolerance: float = 0.5,
) -> tuple[bool, float]:
    """
    Pass if within +/-tolerance_pct OR within +/-abs_tolerance (whichever is more lenient).
    abs_tolerance handles near-zero values.

    Returns (passed, relative_error_pct).
    """
    if expected == 0:
        passed = abs(actual) <= abs_tolerance
        return passed, float("inf") if not passed else 0.0

    relative_error = abs((actual - expected) / expected) * 100
    absolute_error = abs(actual - expected)
    passed = relative_error <= tolerance_pct or absolute_error <= abs_tolerance
    return passed, relative_error


def check_phase(
    expected_value: str,
    actual_value: str,
    acceptable_aliases: list[str] | None = None,
) -> bool:
    """Case-insensitive match against expected value or any acceptable alias."""
    if actual_value is None:
        return False
    actual_lower = actual_value.lower().strip()
    if actual_lower == expected_value.lower().strip():
        return True
    if actual_lower == expected_value.replace("_", " ").lower():
        return True
    if acceptable_aliases:
        for alias in acceptable_aliases:
            if actual_lower == alias.lower().strip():
                return True
    return False


def score_question(question: dict, extracted: dict) -> QuestionResult:
    """
    Score a single question given extracted property values.

    Args:
        question: A question dict from questions.jsonl.
        extracted: Dict from extract_properties() mapping keys to values.

    Returns:
        QuestionResult with per-property breakdown.
    """
    expected = question["expected"]
    prop_results = []
    n_correct = 0

    for prop_key, spec in expected.items():
        ext_val = extracted.get(prop_key)

        if spec.get("type") == "exact_match":
            # Phase matching
            if ext_val is None:
                prop_results.append(PropertyResult(
                    prop_key=prop_key,
                    expected=spec["value"],
                    extracted=None,
                    passed=False,
                    error_pct=None,
                    error_type="missing",
                ))
            else:
                passed = check_phase(
                    spec["value"], ext_val, spec.get("acceptable_aliases")
                )
                prop_results.append(PropertyResult(
                    prop_key=prop_key,
                    expected=spec["value"],
                    extracted=ext_val,
                    passed=passed,
                    error_pct=None,
                    error_type="correct" if passed else "wrong",
                ))
                if passed:
                    n_correct += 1
        else:
            # Numeric matching
            exp_val = spec["value"]
            tol_pct = spec.get("tolerance_pct", 2.0)
            abs_tol = spec.get("abs_tolerance", 0.5)

            if ext_val is None:
                prop_results.append(PropertyResult(
                    prop_key=prop_key,
                    expected=exp_val,
                    extracted=None,
                    passed=False,
                    error_pct=None,
                    error_type="missing",
                ))
            else:
                passed, error_pct = check_numeric(exp_val, ext_val, tol_pct, abs_tol)
                prop_results.append(PropertyResult(
                    prop_key=prop_key,
                    expected=exp_val,
                    extracted=ext_val,
                    passed=passed,
                    error_pct=error_pct,
                    error_type="correct" if passed else "wrong",
                ))
                if passed:
                    n_correct += 1

    n_props = len(expected)
    score = n_correct / n_props if n_props > 0 else 0.0

    return QuestionResult(
        question_id=question["id"],
        category=question["category"],
        subcategory=question.get("subcategory", ""),
        difficulty=question.get("difficulty", ""),
        n_properties=n_props,
        n_correct=n_correct,
        score=score,
        property_results=prop_results,
    )


def score_dataset(
    questions: list[dict], responses: dict[str, str]
) -> DatasetResults:
    """
    Score all questions against model responses.

    Args:
        questions: List of question dicts (from load_questions).
        responses: Dict mapping question_id -> raw LLM response text.

    Returns:
        DatasetResults with full breakdown.
    """
    question_results = []

    for q in questions:
        qid = q["id"]
        response_text = responses.get(qid, "")
        expected_keys = list(q["expected"].keys())
        extracted = extract_properties(response_text, expected_keys)
        qr = score_question(q, extracted)
        question_results.append(qr)

    # Aggregate stats
    total_questions = len(question_results)
    total_props = sum(qr.n_properties for qr in question_results)
    total_correct = sum(qr.n_correct for qr in question_results)
    mean_score = (
        sum(qr.score for qr in question_results) / total_questions
        if total_questions > 0
        else 0.0
    )
    prop_accuracy = total_correct / total_props if total_props > 0 else 0.0

    # Per-category
    per_category: dict = {}
    for qr in question_results:
        cat = qr.category
        if cat not in per_category:
            per_category[cat] = {
                "n_questions": 0,
                "total_score": 0.0,
                "n_props": 0,
                "n_correct": 0,
            }
        per_category[cat]["n_questions"] += 1
        per_category[cat]["total_score"] += qr.score
        per_category[cat]["n_props"] += qr.n_properties
        per_category[cat]["n_correct"] += qr.n_correct
    for cat, d in per_category.items():
        d["mean_score"] = d["total_score"] / d["n_questions"] if d["n_questions"] else 0
        d["accuracy"] = d["n_correct"] / d["n_props"] if d["n_props"] else 0
        del d["total_score"]

    # Per-difficulty
    per_difficulty: dict = {}
    for qr in question_results:
        diff = qr.difficulty
        if diff not in per_difficulty:
            per_difficulty[diff] = {"n_questions": 0, "total_score": 0.0}
        per_difficulty[diff]["n_questions"] += 1
        per_difficulty[diff]["total_score"] += qr.score
    for diff, d in per_difficulty.items():
        d["mean_score"] = d["total_score"] / d["n_questions"] if d["n_questions"] else 0
        del d["total_score"]

    # Per-property key
    per_property_key: dict = {}
    for qr in question_results:
        for pr in qr.property_results:
            k = pr.prop_key
            if k not in per_property_key:
                per_property_key[k] = {
                    "n_total": 0,
                    "n_correct": 0,
                    "n_missing": 0,
                    "error_pcts": [],
                }
            per_property_key[k]["n_total"] += 1
            if pr.passed:
                per_property_key[k]["n_correct"] += 1
            if pr.error_type == "missing":
                per_property_key[k]["n_missing"] += 1
            if pr.error_pct is not None and pr.error_pct != float("inf"):
                per_property_key[k]["error_pcts"].append(pr.error_pct)
    for k, d in per_property_key.items():
        d["accuracy"] = d["n_correct"] / d["n_total"] if d["n_total"] else 0
        errs = d.pop("error_pcts")
        d["mean_error_pct"] = sum(errs) / len(errs) if errs else None

    return DatasetResults(
        total_questions=total_questions,
        total_properties=total_props,
        total_correct_properties=total_correct,
        mean_question_score=mean_score,
        property_accuracy=prop_accuracy,
        per_category=per_category,
        per_difficulty=per_difficulty,
        per_property_key=per_property_key,
        question_results=question_results,
    )


CATEGORY_CODE_MAP = {
    # Tier 1
    "SL": "subcooled_liquid",
    "SF": "saturated_liquid",
    "WS": "wet_steam",
    "SV": "saturated_vapor",
    "SH": "superheated_vapor",
    "SC": "supercritical",
    "PD": "phase_determination",
    "IL": "inverse_lookups",
    # Tier 2
    "TRB": "turbine",
    "CMP": "compressor",
    "PMP": "pump",
    "HX": "heat_exchanger",
    "BLR": "boiler",
    "MIX": "mixing_chamber",
    "NOZ": "nozzle",
}


def build_summary_from_entries(entries: list[dict], questions: list[dict]) -> dict:
    """
    Build summary stats directly from pre-scored entry dicts.

    Reads question_score and scores fields from each entry instead of
    re-extracting/re-scoring from response text. This ensures summaries
    reflect the actual stored scores (e.g. from LLM extraction).

    Args:
        entries: List of response dicts with question_score, scores fields.
        questions: List of question dicts (for difficulty lookup).

    Returns:
        Dict with summary stats: total_questions, total_properties,
        total_correct_properties, mean_question_score, property_accuracy,
        per_category, per_difficulty, per_property_key.
    """
    questions_by_id = {q["id"]: q for q in questions}

    total_properties = 0
    total_correct = 0
    score_sum = 0.0
    per_category: dict = {}
    per_difficulty: dict = {}
    per_property_key: dict = {}

    for entry in entries:
        qid = entry["id"]
        q_score = entry.get("question_score", 0.0)
        scores = entry.get("scores", [])
        score_sum += q_score

        # Derive category from question ID prefix
        # T1-XX-NNN -> XX (Tier 1: 2-char codes like SL, SH)
        # T2-XXX-DFNNN -> XXX (Tier 2: 3-char codes like TRB, CMP)
        parts = qid.split("-")
        code = parts[1] if len(parts) >= 3 else "??"
        category = CATEGORY_CODE_MAP.get(code, code)

        # Difficulty from questions list
        q = questions_by_id.get(qid)
        difficulty = q.get("difficulty", "") if q else ""

        n_props = len(scores) if scores else 0
        n_correct = sum(1 for s in scores if s.get("passed"))
        total_properties += n_props
        total_correct += n_correct

        # Per-category
        if category not in per_category:
            per_category[category] = {
                "n_questions": 0,
                "total_score": 0.0,
                "n_props": 0,
                "n_correct": 0,
            }
        per_category[category]["n_questions"] += 1
        per_category[category]["total_score"] += q_score
        per_category[category]["n_props"] += n_props
        per_category[category]["n_correct"] += n_correct

        # Per-difficulty
        if difficulty not in per_difficulty:
            per_difficulty[difficulty] = {"n_questions": 0, "total_score": 0.0}
        per_difficulty[difficulty]["n_questions"] += 1
        per_difficulty[difficulty]["total_score"] += q_score

        # Per-property key
        for s in scores:
            k = s.get("key", "unknown")
            if k not in per_property_key:
                per_property_key[k] = {
                    "n_total": 0,
                    "n_correct": 0,
                    "n_missing": 0,
                    "error_pcts": [],
                }
            per_property_key[k]["n_total"] += 1
            if s.get("passed"):
                per_property_key[k]["n_correct"] += 1
            if s.get("error_type") == "missing":
                per_property_key[k]["n_missing"] += 1
            err = s.get("error_pct")
            if err is not None and err != float("inf"):
                per_property_key[k]["error_pcts"].append(err)

    total_questions = len(entries)
    mean_score = score_sum / total_questions if total_questions > 0 else 0.0
    prop_accuracy = total_correct / total_properties if total_properties > 0 else 0.0

    # Finalize per-category
    for d in per_category.values():
        d["mean_score"] = d["total_score"] / d["n_questions"] if d["n_questions"] else 0
        d["accuracy"] = d["n_correct"] / d["n_props"] if d["n_props"] else 0
        del d["total_score"]

    # Finalize per-difficulty
    for d in per_difficulty.values():
        d["mean_score"] = d["total_score"] / d["n_questions"] if d["n_questions"] else 0
        del d["total_score"]

    # Finalize per-property key
    for d in per_property_key.values():
        d["accuracy"] = d["n_correct"] / d["n_total"] if d["n_total"] else 0
        errs = d.pop("error_pcts")
        d["mean_error_pct"] = sum(errs) / len(errs) if errs else None

    return {
        "total_questions": total_questions,
        "total_properties": total_properties,
        "total_correct_properties": total_correct,
        "mean_question_score": mean_score,
        "property_accuracy": prop_accuracy,
        "per_category": per_category,
        "per_difficulty": per_difficulty,
        "per_property_key": per_property_key,
    }


# ══════════════════════════════════════════════════════════
# TIER 2: Weighted step-level scoring
# ══════════════════════════════════════════════════════════

@dataclass
class StepScoreResult:
    step_id: str
    expected: float
    extracted: float | None
    weight: float
    passed: bool
    error_pct: float | None
    error_type: str  # "correct", "wrong", "missing"


@dataclass
class Tier2QuestionResult:
    question_id: str
    component: str
    depth: str
    fluid: str
    difficulty: str
    n_steps: int
    n_correct: int
    weighted_score: float
    step_results: list[StepScoreResult]


def score_tier2_question(question: dict, extracted: dict) -> Tier2QuestionResult:
    """
    Score a Tier 2 question with weighted step-level scoring.

    Args:
        question: A Tier 2 question dict with 'expected' and 'steps' fields.
        extracted: Dict mapping step_id -> extracted value.

    Returns:
        Tier2QuestionResult with weighted score and per-step breakdown.
    """
    expected = question["expected"]
    steps = question.get("steps", [])

    # Build weight map from steps
    weight_map = {s["id"]: s["weight"] for s in steps}

    step_results = []
    total_weight = 0.0
    weighted_sum = 0.0
    n_correct = 0

    for step_id, spec in expected.items():
        weight = weight_map.get(step_id, 1.0)
        total_weight += weight
        ext_val = extracted.get(step_id)
        exp_val = spec["value"]
        tol_pct = spec.get("tolerance_pct", 2.0)
        abs_tol = spec.get("abs_tolerance", 0.5)

        if ext_val is None:
            step_results.append(StepScoreResult(
                step_id=step_id, expected=exp_val, extracted=None,
                weight=weight, passed=False, error_pct=None,
                error_type="missing",
            ))
        else:
            passed, error_pct = check_numeric(exp_val, ext_val, tol_pct, abs_tol)
            step_results.append(StepScoreResult(
                step_id=step_id, expected=exp_val, extracted=ext_val,
                weight=weight, passed=passed, error_pct=error_pct,
                error_type="correct" if passed else "wrong",
            ))
            if passed:
                n_correct += 1
                weighted_sum += weight

    weighted_score = weighted_sum / total_weight if total_weight > 0 else 0.0

    return Tier2QuestionResult(
        question_id=question["id"],
        component=question.get("component", ""),
        depth=question.get("depth", ""),
        fluid=question.get("fluid", ""),
        difficulty=question.get("difficulty", ""),
        n_steps=len(expected),
        n_correct=n_correct,
        weighted_score=weighted_score,
        step_results=step_results,
    )


@dataclass
class Tier3QuestionResult:
    question_id: str
    cycle_type: str
    depth: str
    fluid: str
    difficulty: str
    n_steps: int
    n_correct: int
    weighted_score: float
    step_results: list[StepScoreResult]


def score_tier3_question(question: dict, extracted: dict) -> Tier3QuestionResult:
    """Score a Tier 3 question with weighted step-level scoring."""
    expected = question["expected"]
    steps = question.get("steps", [])
    weight_map = {s["id"]: s["weight"] for s in steps}

    step_results = []
    total_weight = 0.0
    weighted_sum = 0.0
    n_correct = 0

    for step_id, spec in expected.items():
        weight = weight_map.get(step_id, 1.0)
        total_weight += weight
        ext_val = extracted.get(step_id)
        exp_val = spec["value"]
        tol_pct = spec.get("tolerance_pct", 2.0)
        abs_tol = spec.get("abs_tolerance", 0.5)

        if ext_val is None:
            step_results.append(StepScoreResult(
                step_id=step_id, expected=exp_val, extracted=None,
                weight=weight, passed=False, error_pct=None,
                error_type="missing",
            ))
        else:
            passed, error_pct = check_numeric(exp_val, ext_val, tol_pct, abs_tol)
            step_results.append(StepScoreResult(
                step_id=step_id, expected=exp_val, extracted=ext_val,
                weight=weight, passed=passed, error_pct=error_pct,
                error_type="correct" if passed else "wrong",
            ))
            if passed:
                n_correct += 1
                weighted_sum += weight

    weighted_score = weighted_sum / total_weight if total_weight > 0 else 0.0

    return Tier3QuestionResult(
        question_id=question["id"],
        cycle_type=question.get("cycle_type", ""),
        depth=question.get("depth", ""),
        fluid=question.get("fluid", ""),
        difficulty=question.get("difficulty", ""),
        n_steps=len(expected),
        n_correct=n_correct,
        weighted_score=weighted_score,
        step_results=step_results,
    )


def score_question_auto(question: dict, extracted: dict):
    """Route to Tier 1, 2, or 3 scorer based on question tier."""
    tier = question.get("tier", 1)
    if tier == 3:
        result = score_tier3_question(question, extracted)
        return QuestionResult(
            question_id=result.question_id,
            category=result.cycle_type,
            subcategory=result.depth,
            difficulty=result.difficulty,
            n_properties=result.n_steps,
            n_correct=result.n_correct,
            score=result.weighted_score,
            property_results=[
                PropertyResult(
                    prop_key=sr.step_id, expected=sr.expected,
                    extracted=sr.extracted, passed=sr.passed,
                    error_pct=sr.error_pct, error_type=sr.error_type,
                )
                for sr in result.step_results
            ],
        )
    elif tier == 2:
        result = score_tier2_question(question, extracted)
        return QuestionResult(
            question_id=result.question_id,
            category=result.component,
            subcategory=result.depth,
            difficulty=result.difficulty,
            n_properties=result.n_steps,
            n_correct=result.n_correct,
            score=result.weighted_score,
            property_results=[
                PropertyResult(
                    prop_key=sr.step_id, expected=sr.expected,
                    extracted=sr.extracted, passed=sr.passed,
                    error_pct=sr.error_pct, error_type=sr.error_type,
                )
                for sr in result.step_results
            ],
        )
    else:
        return score_question(question, extracted)


def load_questions(path: str) -> list[dict]:
    """Load questions from a JSONL file."""
    questions = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                questions.append(json.loads(line))
    return questions


def print_summary(results: DatasetResults) -> None:
    """Print a formatted summary of evaluation results."""
    print("=" * 60)
    print("ThermoQA Evaluation Summary")
    print("=" * 60)
    print(f"Total questions:    {results.total_questions}")
    print(f"Total properties:   {results.total_properties}")
    print(f"Correct properties: {results.total_correct_properties}")
    print(f"Property accuracy:  {results.property_accuracy:.1%}")
    print(f"Mean question score:{results.mean_question_score:.1%}")

    print("\n--- By Category ---")
    print(f"{'Category':<25} {'N':>4} {'Score':>7} {'Props':>6} {'Acc':>7}")
    print("-" * 55)
    for cat, d in sorted(results.per_category.items()):
        print(
            f"{cat:<25} {d['n_questions']:>4} "
            f"{d['mean_score']:>6.1%} {d['n_props']:>6} {d['accuracy']:>6.1%}"
        )

    print("\n--- By Difficulty ---")
    print(f"{'Difficulty':<15} {'N':>4} {'Score':>7}")
    print("-" * 30)
    for diff, d in sorted(results.per_difficulty.items()):
        print(f"{diff:<15} {d['n_questions']:>4} {d['mean_score']:>6.1%}")

    print("\n--- By Property Key ---")
    print(f"{'Key':<20} {'N':>4} {'Correct':>8} {'Miss':>5} {'Acc':>7} {'Err%':>7}")
    print("-" * 55)
    for k, d in sorted(results.per_property_key.items()):
        err_str = f"{d['mean_error_pct']:.2f}" if d["mean_error_pct"] is not None else "N/A"
        print(
            f"{k:<20} {d['n_total']:>4} {d['n_correct']:>8} "
            f"{d['n_missing']:>5} {d['accuracy']:>6.1%} {err_str:>7}"
        )
    print("=" * 60)
