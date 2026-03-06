"""
Report generation for ThermoQA evaluation results.

Generates leaderboards and detailed per-provider reports.
"""

import json
import os

from evaluation.scorer import DatasetResults, load_questions, print_summary, score_dataset


# Category codes for column headers
_CAT_CODES = {
    "subcooled_liquid": "SL",
    "saturated_liquid": "SF",
    "wet_steam": "WS",
    "saturated_vapor": "SV",
    "superheated_vapor": "SH",
    "supercritical": "SC",
    "phase_determination": "PD",
    "inverse_lookups": "IL",
}

_DIFF_ORDER = ["easy", "medium", "hard"]


def generate_leaderboard(results_dir: str) -> str:
    """
    Scan results_dir for provider subdirectories with summary.json files.
    Build a markdown leaderboard table.

    Returns markdown string.
    """
    summaries = []
    if not os.path.isdir(results_dir):
        return "_No results directory found._"

    for name in sorted(os.listdir(results_dir)):
        summary_path = os.path.join(results_dir, name, "summary.json")
        if os.path.isfile(summary_path):
            with open(summary_path) as f:
                try:
                    s = json.load(f)
                    s["_dir_name"] = name
                    summaries.append(s)
                except json.JSONDecodeError:
                    continue

    if not summaries:
        return "_No evaluation results found._"

    # Sort by mean_question_score descending
    summaries.sort(key=lambda s: s.get("mean_question_score", 0), reverse=True)

    # Build header
    cat_cols = list(_CAT_CODES.values())
    diff_cols = [d.capitalize()[:4] for d in _DIFF_ORDER]
    header = "| Rank | Model | Overall | Props |"
    for c in cat_cols:
        header += f" {c} |"
    for d in diff_cols:
        header += f" {d} |"
    header += "\n"

    sep = "|" + "|".join(["---"] * (4 + len(cat_cols) + len(diff_cols))) + "|\n"

    rows = ""
    for rank, s in enumerate(summaries, 1):
        model = s.get("model", s.get("provider", "?"))
        overall = s.get("mean_question_score", 0)
        props = s.get("property_accuracy", 0)
        row = f"| {rank} | {model} | {overall:.1%} | {props:.1%} |"

        per_cat = s.get("per_category", {})
        for cat_name, code in _CAT_CODES.items():
            cat_data = per_cat.get(cat_name, {})
            score = cat_data.get("mean_score", None)
            row += f" {score:.1%} |" if score is not None else " - |"

        per_diff = s.get("per_difficulty", {})
        for diff in _DIFF_ORDER:
            diff_data = per_diff.get(diff, {})
            score = diff_data.get("mean_score", None)
            row += f" {score:.1%} |" if score is not None else " - |"

        rows += row + "\n"

    return "## ThermoQA Leaderboard\n\n" + header + sep + rows


def print_detailed_report(results_path: str, questions_path: str | None = None) -> None:
    """
    Print a detailed report for a single provider's results.

    Args:
        results_path: Path to provider directory (containing responses.jsonl).
        questions_path: Path to questions.jsonl. If None, uses default.
    """
    responses_file = os.path.join(results_path, "responses.jsonl")
    summary_file = os.path.join(results_path, "summary.json")

    if not os.path.isfile(responses_file):
        print(f"No responses.jsonl found in {results_path}")
        return

    # Load summary for provider/model info
    summary = {}
    if os.path.isfile(summary_file):
        with open(summary_file) as f:
            try:
                summary = json.load(f)
            except json.JSONDecodeError:
                pass

    # Load responses
    response_entries = []
    with open(responses_file) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                response_entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    if not response_entries:
        print("No valid response entries found.")
        return

    # Print header
    print("=" * 60)
    print("ThermoQA Detailed Report")
    print("=" * 60)
    provider = summary.get("provider", os.path.basename(results_path))
    model = summary.get("model", "unknown")
    print(f"Provider: {provider}")
    print(f"Model:    {model}")
    print(f"Responses: {len(response_entries)}")

    # Timing stats
    latencies = [e.get("latency_s", 0) for e in response_entries if e.get("latency_s", 0) > 0]
    if latencies:
        print(f"\nTiming:")
        print(f"  Mean latency: {sum(latencies)/len(latencies):.2f}s")
        print(f"  Min latency:  {min(latencies):.2f}s")
        print(f"  Max latency:  {max(latencies):.2f}s")

    # Token usage
    in_tokens = [e["input_tokens"] for e in response_entries if e.get("input_tokens") is not None]
    out_tokens = [e["output_tokens"] for e in response_entries if e.get("output_tokens") is not None]
    if in_tokens or out_tokens:
        print(f"\nToken usage:")
        if in_tokens:
            print(f"  Total input:  {sum(in_tokens):,}")
            print(f"  Mean input:   {sum(in_tokens)/len(in_tokens):.0f}")
        if out_tokens:
            print(f"  Total output: {sum(out_tokens):,}")
            print(f"  Mean output:  {sum(out_tokens)/len(out_tokens):.0f}")

    # Rebuild scores from questions + responses if questions available
    if questions_path and os.path.isfile(questions_path):
        questions = load_questions(questions_path)
        responses_map = {e["id"]: e.get("response_text", "") for e in response_entries}
        ds = score_dataset(questions, responses_map)
        print()
        print_summary(ds)
    elif summary:
        # Use summary data
        print(f"\nOverall score:     {summary.get('mean_question_score', 0):.1%}")
        print(f"Property accuracy: {summary.get('property_accuracy', 0):.1%}")

    # Failed questions
    failed = [e for e in response_entries if e.get("error")]
    if failed:
        print(f"\nFailed questions ({len(failed)}):")
        for e in failed:
            print(f"  {e['id']}: {e.get('error', 'unknown error')}")

    print("=" * 60)
