#!/usr/bin/env python3
"""
CLI script to run ThermoQA Tier 3 evaluations against LLM providers.

Tier 3 tests multi-step cycle analysis (Rankine, Brayton, refrigeration, etc.)
with weighted step-level scoring.

Usage:
    python scripts/run_evaluation_tier3.py --provider anthropic
    python scripts/run_evaluation_tier3.py --provider ollama --model llama3
    python scripts/run_evaluation_tier3.py --provider anthropic --ids T3-RNK-I-001,T3-BRY-I-001
    python scripts/run_evaluation_tier3.py --reextract --provider anthropic
    python scripts/run_evaluation_tier3.py --report
"""

import argparse
import json
import os
import sys
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

# Ensure project root is on path when running as script
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evaluation.extractor import extract_tier3_properties, strip_thinking_tags
from evaluation.runner import PROVIDERS, SYSTEM_PROMPT, get_provider, BaseProvider
from evaluation.scorer import (
    build_summary_from_entries,
    load_questions,
    score_tier3_question,
)

DEFAULT_QUESTIONS = "data/tier3_cycles/questions.jsonl"
DEFAULT_OUTPUT_DIR = "results_tier3/"


def _build_tier3_summary(entries, questions, provider_name, model_name,
                         errors=0, latencies=None, batch_id=None):
    """Build Tier 3 summary dict from scored entries."""
    stats = build_summary_from_entries(entries, questions)
    questions_by_id = {q["id"]: q for q in questions}

    # by_depth and by_fluid from entries
    by_depth = {}
    by_fluid = {}
    for entry in entries:
        q = questions_by_id.get(entry["id"], {})
        depth = q.get("depth", entry.get("depth", "?"))
        fluid = q.get("fluid", entry.get("fluid", "?"))
        score = entry.get("question_score", 0.0)
        for key, group in [(depth, by_depth), (fluid, by_fluid)]:
            if key not in group:
                group[key] = {"count": 0, "total_score": 0.0}
            group[key]["count"] += 1
            group[key]["total_score"] += score
    for group in [by_depth, by_fluid]:
        for d in group.values():
            d["score"] = round(d["total_score"] / d["count"], 4) if d["count"] else 0
            del d["total_score"]

    # by_ideal_vs_actual breakdown
    IDEAL_CYCLES = {"RNK-I", "BRY-I"}
    by_ideal_vs_actual = {"ideal": {"count": 0, "total_score": 0.0}, "actual": {"count": 0, "total_score": 0.0}}
    for entry in entries:
        q = questions_by_id.get(entry["id"], {})
        ct = q.get("cycle_type", entry.get("cycle_type", ""))
        score = entry.get("question_score", 0.0)
        group_key = "ideal" if ct in IDEAL_CYCLES else "actual"
        by_ideal_vs_actual[group_key]["count"] += 1
        by_ideal_vs_actual[group_key]["total_score"] += score
    for d in by_ideal_vs_actual.values():
        d["score"] = round(d["total_score"] / d["count"], 4) if d["count"] else 0
        del d["total_score"]

    # Token stats
    input_toks = [e["input_tokens"] for e in entries if e.get("input_tokens") is not None]
    output_toks = [e["output_tokens"] for e in entries if e.get("output_tokens") is not None]

    if latencies is None:
        latencies = [e.get("latency_s", 0) for e in entries]

    summary = {
        "provider": provider_name,
        "model": model_name,
        "tier": 3,
        "overall_score": round(stats["mean_question_score"], 4),
        "total_questions": stats["total_questions"],
        "total_responses": len(entries),
        "total_properties": stats["total_properties"],
        "total_correct_properties": stats["total_correct_properties"],
        "property_accuracy": round(stats["property_accuracy"], 4),
        "by_cycle_type": {
            cat: {"score": round(d.get("mean_score", 0), 4), "count": d["n_questions"]}
            for cat, d in stats["per_category"].items()
        },
        "by_ideal_vs_actual": by_ideal_vs_actual,
        "by_depth": by_depth,
        "by_fluid": by_fluid,
        "by_step_type": {
            k: {"score": round(d.get("accuracy", 0), 4)}
            for k, d in stats.get("per_property_key", {}).items()
        },
        "errors": errors,
        "timing": {
            "mean_latency_s": round(sum(latencies) / len(latencies), 2) if latencies else 0,
            "min_latency_s": round(min(latencies), 2) if latencies else 0,
            "max_latency_s": round(max(latencies), 2) if latencies else 0,
        },
        "tokens": {
            "total_input": sum(input_toks) if input_toks else None,
            "total_output": sum(output_toks) if output_toks else None,
            "mean_input": round(sum(input_toks) / len(input_toks), 1) if input_toks else None,
            "mean_output": round(sum(output_toks) / len(output_toks), 1) if output_toks else None,
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    if batch_id:
        summary["batch_id"] = batch_id
    return summary


def _build_entry(qid, q, resp_or_dict, extracted, result, model):
    """Build a Tier 3 entry dict from scoring results."""
    # Support both ProviderResponse objects and raw dicts
    if hasattr(resp_or_dict, "raw_text"):
        raw_response = resp_or_dict.raw_text
        response_text = resp_or_dict.text
        thinking_text = resp_or_dict.thinking_text
        latency_s = resp_or_dict.latency_s
        input_tokens = resp_or_dict.input_tokens
        output_tokens = resp_or_dict.output_tokens
    else:
        raw_response = resp_or_dict.get("raw_response", "")
        response_text = resp_or_dict.get("response_text", "")
        thinking_text = resp_or_dict.get("thinking_text")
        latency_s = resp_or_dict.get("latency_s", 0.0)
        input_tokens = resp_or_dict.get("input_tokens")
        output_tokens = resp_or_dict.get("output_tokens")

    scores = []
    steps = []
    for sr in result.step_results:
        scores.append({
            "key": sr.step_id,
            "expected": sr.expected,
            "extracted": sr.extracted,
            "passed": sr.passed,
            "error_pct": sr.error_pct,
            "error_type": sr.error_type,
        })
        steps.append({
            "id": sr.step_id,
            "expected": sr.expected,
            "extracted": sr.extracted,
            "weight": sr.weight,
            "passed": sr.passed,
            "error_pct": sr.error_pct,
        })

    return {
        "id": qid,
        "question": q["question"],
        "raw_response": raw_response,
        "response_text": response_text,
        "thinking_text": thinking_text,
        "extracted": {k: v for k, v in extracted.items()},
        "scores": scores,
        "question_score": result.weighted_score,
        "steps": steps,
        "cycle_type": q.get("cycle_type", ""),
        "depth": q.get("depth", ""),
        "fluid": q.get("fluid", ""),
        "model": model,
        "latency_s": latency_s,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _write_summary(all_entries, questions, provider_name, model_name, summary_path):
    """Build and write summary.json from all entries."""
    entry_list = list(all_entries.values()) if isinstance(all_entries, dict) else all_entries
    if not entry_list:
        return
    errors = sum(1 for e in entry_list if e.get("error"))
    summary = _build_tier3_summary(
        entry_list, questions, provider_name, model_name, errors=errors,
    )
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    return summary


def run_tier3_evaluation(provider, questions, output_dir, delay_s=1.0,
                         selected_ids=None, run_num=None, parallel=1):
    """Run Tier 3 evaluation loop with incremental saves."""
    provider_dir = os.path.join(output_dir, provider.name)
    if run_num is not None:
        provider_dir = os.path.join(provider_dir, f"run{run_num}")
    os.makedirs(provider_dir, exist_ok=True)
    responses_path = os.path.join(provider_dir, "responses.jsonl")
    summary_path = os.path.join(provider_dir, "summary.json")

    # If specific IDs given, filter questions
    if selected_ids:
        ids_set = set(selected_ids)
        all_ids = {q["id"] for q in questions}
        unknown = ids_set - all_ids
        if unknown:
            print(f"ERROR: Unknown question IDs: {', '.join(sorted(unknown))}", file=sys.stderr)
            sys.exit(1)
        run_questions = [q for q in questions if q["id"] in ids_set]
        print(f"Filtered to {len(run_questions)} questions: {', '.join(selected_ids)}")
    else:
        run_questions = questions

    # Load existing entries
    existing_entries = {}
    if os.path.exists(responses_path):
        with open(responses_path) as f:
            for line in f:
                line = line.strip()
                if line:
                    entry = json.loads(line)
                    existing_entries[entry["id"]] = entry

    # If re-running specific IDs, remove them from file so we can append fresh
    if selected_ids:
        for qid in selected_ids:
            existing_entries.pop(qid, None)
        with open(responses_path, "w") as f:
            for entry in existing_entries.values():
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        pending = run_questions
    else:
        completed = set(existing_entries.keys())
        pending = [q for q in run_questions if q["id"] not in completed]

    if not pending:
        print("All questions already answered. Use --ids to re-run specific questions.")
        return

    total = len(questions)
    done_count = len(existing_entries)
    print(f"Questions: {total} total, {done_count} done, {len(pending)} remaining")

    total_score = 0.0
    n_scored = 0

    # Track all entries for summary (existing + new)
    all_entries = dict(existing_entries)

    if parallel > 1:
        # ---- Parallel execution path ----
        file_lock = threading.Lock()
        progress_count = [0]

        def process_question(q):
            qid = q["id"]
            step_ids = [s["id"] for s in q["steps"]]
            try:
                resp = provider.generate(SYSTEM_PROMPT, q["question"])
            except Exception as exc:
                print(f"\n  ERROR on {qid}: {exc}")
                return {
                    "id": qid, "question": q["question"],
                    "raw_response": "", "response_text": "",
                    "thinking_text": None, "extracted": {},
                    "scores": [], "question_score": 0.0, "steps": [],
                    "cycle_type": q.get("cycle_type", ""),
                    "depth": q.get("depth", ""),
                    "fluid": q.get("fluid", ""),
                    "model": provider.model, "latency_s": 0.0,
                    "input_tokens": None, "output_tokens": None,
                    "error": str(exc),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            extraction_text = resp.text if resp.text.strip() else (resp.thinking_text or "")
            extracted = extract_tier3_properties(extraction_text, step_ids)
            result = score_tier3_question(q, extracted)
            return _build_entry(qid, q, resp, extracted, result, resp.model)

        try:
            with open(responses_path, "a") as f_out:
                with ThreadPoolExecutor(max_workers=parallel) as executor:
                    futures = {executor.submit(process_question, q): q for q in pending}
                    for future in as_completed(futures):
                        try:
                            entry = future.result()
                        except Exception as e:
                            q = futures[future]
                            print(f"\nFatal error on {q['id']}: {e}")
                            continue
                        qid = entry["id"]
                        with file_lock:
                            f_out.write(json.dumps(entry, ensure_ascii=False) + "\n")
                            f_out.flush()
                            all_entries[qid] = entry
                            progress_count[0] += 1
                            sys.stdout.write(
                                f"\r  [{done_count + progress_count[0]}/{total}] completed {qid}"
                            )
                            sys.stdout.flush()
                            _write_summary(all_entries, questions, provider.name, provider.model, summary_path)
            print()
        except KeyboardInterrupt:
            print("\n\nInterrupted! Partial results saved.")

        # Skip to final summary
        summary = _write_summary(all_entries, questions, provider.name, provider.model, summary_path)
        if summary is None:
            return
        print(f"Wrote {len(all_entries)} responses to {responses_path}")
        print(f"Wrote summary to {summary_path}")
        print(f"\n=== Results ===")
        print(f"  Questions:    {summary['total_questions']}")
        print(f"  Overall:      {summary['overall_score']:.1%}")
        print(f"  Errors:       {summary['errors']}")
        if summary["tokens"]["total_input"]:
            print(f"  Total tokens: {summary['tokens']['total_input']} in / "
                  f"{summary['tokens']['total_output']} out")
        return

    # ---- Sequential execution path (original) ----
    try:
        with open(responses_path, "a") as f_out:
            for i, q in enumerate(pending, 1):
                qid = q["id"]
                step_ids = [s["id"] for s in q["steps"]]

                sys.stdout.write(f"\r  [{done_count + i}/{total}] {qid} ...")
                sys.stdout.flush()

                try:
                    resp = provider.generate(SYSTEM_PROMPT, q["question"])
                except Exception as exc:
                    print(f"\n  ERROR on {qid}: {exc}")
                    entry = {
                        "id": qid,
                        "question": q["question"],
                        "raw_response": "",
                        "response_text": "",
                        "thinking_text": None,
                        "extracted": {},
                        "scores": [],
                        "question_score": 0.0,
                        "steps": [],
                        "cycle_type": q.get("cycle_type", ""),
                        "depth": q.get("depth", ""),
                        "fluid": q.get("fluid", ""),
                        "model": provider.model,
                        "latency_s": 0.0,
                        "input_tokens": None,
                        "output_tokens": None,
                        "error": str(exc),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                    f_out.write(json.dumps(entry, ensure_ascii=False) + "\n")
                    f_out.flush()
                    all_entries[qid] = entry
                    n_scored += 1
                    # Rebuild summary after each question
                    _write_summary(all_entries, questions, provider.name, provider.model, summary_path)
                    if delay_s > 0:
                        time.sleep(delay_s)
                    continue

                # Extract and score
                extraction_text = resp.text if resp.text.strip() else (resp.thinking_text or "")
                extracted = extract_tier3_properties(extraction_text, step_ids)
                result = score_tier3_question(q, extracted)

                entry = _build_entry(qid, q, resp, extracted, result, resp.model)

                # Write immediately and flush
                f_out.write(json.dumps(entry, ensure_ascii=False) + "\n")
                f_out.flush()
                all_entries[qid] = entry

                n_scored += 1
                total_score += result.weighted_score
                running_score = total_score / n_scored if n_scored > 0 else 0.0

                bar_len = 30
                filled = int(bar_len * (done_count + i) / total) if total > 0 else 0
                bar = "#" * filled + "-" * (bar_len - filled)
                sys.stdout.write(
                    f"\r[{bar}] {done_count + i}/{total} {qid} | Running score: {running_score:.1%}"
                )
                sys.stdout.flush()

                # Rebuild summary after each question
                _write_summary(all_entries, questions, provider.name, provider.model, summary_path)

                if delay_s > 0 and i < len(pending):
                    time.sleep(delay_s)

        print()  # newline after progress

    except KeyboardInterrupt:
        print("\n\nInterrupted! Partial results saved.")

    # Final summary (covers normal completion and interrupt)
    summary = _write_summary(all_entries, questions, provider.name, provider.model, summary_path)
    if summary is None:
        return

    print(f"Wrote {len(all_entries)} responses to {responses_path}")
    print(f"Wrote summary to {summary_path}")
    print(f"\n=== Results ===")
    print(f"  Questions:    {summary['total_questions']}")
    print(f"  Overall:      {summary['overall_score']:.1%}")
    print(f"  Errors:       {summary['errors']}")
    if summary["tokens"]["total_input"]:
        print(f"  Total tokens: {summary['tokens']['total_input']} in / "
              f"{summary['tokens']['total_output']} out")


def run_reextract(provider_name, output_dir, questions, run_num=None):
    """Re-extract and re-score existing responses using LLM extractor."""
    from evaluation.llm_extractor import LLMExtractor

    provider_dir = os.path.join(output_dir, provider_name)
    if run_num is not None:
        provider_dir = os.path.join(provider_dir, f"run{run_num}")
    responses_path = os.path.join(provider_dir, "responses.jsonl")
    if not os.path.isfile(responses_path):
        print(f"No responses.jsonl found at {responses_path}")
        sys.exit(1)

    questions_by_id = {q["id"]: q for q in questions}

    # Load entries
    entries = []
    with open(responses_path) as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    print(f"Loaded {len(entries)} responses from {responses_path}")

    extractor = LLMExtractor()

    old_scores = []
    new_scores = []

    for i, entry in enumerate(entries):
        qid = entry["id"]
        q = questions_by_id.get(qid)
        old_score = entry.get("question_score", 0.0)
        old_scores.append(old_score)

        if q is None:
            new_scores.append(old_score)
            continue

        step_ids = [s["id"] for s in q["steps"]]
        response_text = entry.get("raw_response", entry.get("response_text", ""))

        print(f"  Extracting {i + 1}/{len(entries)} ({qid})...", end="\r")
        new_extracted = extractor.extract_tier3(response_text, step_ids, q["question"])

        result = score_tier3_question(q, new_extracted)
        new_score = result.weighted_score
        new_scores.append(new_score)

        # Update entry
        scores = []
        steps = []
        for sr in result.step_results:
            scores.append({
                "key": sr.step_id,
                "expected": sr.expected,
                "extracted": sr.extracted,
                "passed": sr.passed,
                "error_pct": sr.error_pct,
                "error_type": sr.error_type,
            })
            steps.append({
                "id": sr.step_id,
                "expected": sr.expected,
                "extracted": sr.extracted,
                "weight": sr.weight,
                "passed": sr.passed,
                "error_pct": sr.error_pct,
            })
        entry["extracted"] = {k: v for k, v in new_extracted.items()}
        entry["scores"] = scores
        entry["steps"] = steps
        entry["question_score"] = new_score

        if i < len(entries) - 1:
            time.sleep(0.5)

    print()

    # Print comparison
    print(f"\n  {'ID':<20} {'Old':>6} {'New':>6} {'Delta':>7}")
    print(f"  {'-'*20} {'-'*6} {'-'*6} {'-'*7}")
    changed = 0
    for entry, old_s, new_s in zip(entries, old_scores, new_scores):
        delta = new_s - old_s
        marker = ""
        if abs(delta) > 0.001:
            marker = " +" if delta > 0 else " -"
            changed += 1
        print(f"  {entry['id']:<20} {old_s:>5.1%} {new_s:>5.1%} {delta:>+6.1%}{marker}")

    old_mean = sum(old_scores) / len(old_scores) if old_scores else 0
    new_mean = sum(new_scores) / len(new_scores) if new_scores else 0
    print(f"\n  Aggregate: {old_mean:.1%} -> {new_mean:.1%} (delta: {new_mean - old_mean:+.1%})")
    print(f"  Changed: {changed}/{len(entries)} questions")

    # Write updated responses
    with open(responses_path, "w") as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"  Wrote {len(entries)} entries to {responses_path}")

    # Rebuild summary
    errors = sum(1 for e in entries if e.get("error"))
    model_name = entries[0].get("model", "unknown") if entries else "unknown"
    summary = _build_tier3_summary(entries, questions, provider_name, model_name, errors=errors)
    summary["reextracted_at"] = datetime.now(timezone.utc).isoformat()

    summary_path = os.path.join(provider_dir, "summary.json")
    # Preserve batch_id if it exists
    if os.path.isfile(summary_path):
        with open(summary_path) as f:
            old_summary = json.load(f)
        if "batch_id" in old_summary:
            summary["batch_id"] = old_summary["batch_id"]
        summary["generated_at"] = old_summary.get("generated_at", summary["generated_at"])

    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"  Wrote summary to {summary_path}")


def print_tier3_leaderboard(results_dir):
    """Print Tier 3 leaderboard from all provider summaries."""
    if not os.path.isdir(results_dir):
        print(f"No results directory found at {results_dir}")
        return

    results = []
    for name in sorted(os.listdir(results_dir)):
        summary_path = os.path.join(results_dir, name, "summary.json")
        if os.path.isfile(summary_path):
            with open(summary_path) as f:
                summary = json.load(f)
            results.append(summary)

    if not results:
        print("No Tier 3 results found.")
        return

    results.sort(key=lambda s: s.get("overall_score", 0), reverse=True)

    # Get depth keys across all results
    all_depths = sorted({d for s in results for d in s.get("by_depth", {}).keys()})

    # Header
    header = f"{'Rank':>4} | {'Model':<30} | {'Overall':>7}"
    for d in all_depths:
        header += f" | {'Depth ' + d:>8}"
    header += f" | {'Tokens/Q':>9}"
    print()
    print("=" * len(header))
    print("ThermoQA Tier 3 Leaderboard")
    print("=" * len(header))
    print(header)
    print("-" * len(header))

    for rank, s in enumerate(results, 1):
        model = s.get("model", "unknown")
        overall = s.get("overall_score", 0)
        row = f"{rank:>4} | {model:<30} | {overall:>6.1%}"
        for d in all_depths:
            depth_score = s.get("by_depth", {}).get(d, {}).get("score", 0)
            row += f" |  {depth_score:>6.1%}"
        # Tokens per question
        toks = s.get("tokens", {})
        total_in = toks.get("total_input") or 0
        total_out = toks.get("total_output") or 0
        n_q = s.get("total_questions", 1)
        toks_per_q = (total_in + total_out) / n_q if n_q > 0 else 0
        row += f" | {toks_per_q:>8.0f}"
        print(row)

    print("=" * len(header))

    # Cycle type breakdown for top model
    if results:
        top = results[0]
        print(f"\nTop model ({top.get('model', '?')}) — by cycle type:")
        by_ct = top.get("by_cycle_type", {})
        for ct in sorted(by_ct.keys()):
            d = by_ct[ct]
            print(f"  {ct:<20} {d.get('score', 0):>6.1%} ({d.get('count', 0)} questions)")


def main():
    parser = argparse.ArgumentParser(
        description="Run ThermoQA Tier 3 evaluations against LLM providers"
    )
    parser.add_argument(
        "--provider",
        choices=list(PROVIDERS.keys()) + ["all"],
        help="LLM provider to evaluate",
    )
    parser.add_argument(
        "--model",
        help="Override default model for the provider",
    )
    parser.add_argument(
        "--questions", default=DEFAULT_QUESTIONS,
        help=f"Path to questions JSONL (default: {DEFAULT_QUESTIONS})",
    )
    parser.add_argument(
        "--output", default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory for results (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--delay", type=float, default=1.0,
        help="Delay between API calls in seconds (default: 1.0)",
    )
    parser.add_argument(
        "--timeout", type=float, default=300.0,
        help="API timeout in seconds (default: 300)",
    )
    parser.add_argument(
        "--max-tokens", type=int, default=None,
        help="Max completion tokens (default: 65536 for thinking models, 16000 otherwise)",
    )
    parser.add_argument(
        "--ids",
        help="Comma-separated question IDs to (re-)run",
    )
    parser.add_argument(
        "--run", type=int, default=None,
        help="Run number for multi-run analysis (e.g., --run 1 saves to provider/run1/)",
    )
    parser.add_argument(
        "--parallel", type=int, default=1,
        help="Number of parallel workers for evaluation (default: 1, sequential)",
    )
    parser.add_argument(
        "--reextract", action="store_true",
        help="Re-extract responses using LLM extractor (requires --provider)",
    )
    parser.add_argument(
        "--report", action="store_true",
        help="Print Tier 3 leaderboard from all providers",
    )
    args = parser.parse_args()

    if args.report:
        print_tier3_leaderboard(args.output)
        return

    if not args.provider:
        parser.error("--provider is required unless using --report")

    questions = load_questions(args.questions)
    print(f"Loaded {len(questions)} Tier 3 questions from {args.questions}")

    if args.reextract:
        if args.provider == "all":
            providers = []
            if os.path.isdir(args.output):
                for name in sorted(os.listdir(args.output)):
                    if os.path.isfile(os.path.join(args.output, name, "responses.jsonl")):
                        providers.append(name)
            if not providers:
                print(f"No providers found in {args.output}")
                sys.exit(1)
            for p in providers:
                print(f"\n{'='*50}")
                print(f"Re-extracting: {p}")
                print(f"{'='*50}")
                run_reextract(p, args.output, questions, run_num=args.run)
        else:
            run_reextract(args.provider, args.output, questions, run_num=args.run)
        return

    selected_ids = args.ids.split(",") if args.ids else None

    if args.provider == "all":
        for name in PROVIDERS:
            print(f"\n{'='*50}")
            print(f"Provider: {name}")
            print(f"{'='*50}")
            try:
                provider_kwargs = {"timeout": args.timeout}
                if args.model:
                    provider_kwargs["model"] = args.model
                if args.max_tokens:
                    provider_kwargs["max_tokens"] = args.max_tokens
                provider = get_provider(name, **provider_kwargs)
                run_tier3_evaluation(provider, questions, args.output,
                                     delay_s=args.delay, selected_ids=selected_ids,
                                     run_num=args.run, parallel=args.parallel)
            except (ValueError, ImportError) as e:
                print(f"  Skipping {name}: {e}")
        return

    provider_kwargs = {"timeout": args.timeout}
    if args.model:
        provider_kwargs["model"] = args.model
    if args.max_tokens:
        provider_kwargs["max_tokens"] = args.max_tokens

    try:
        provider = get_provider(args.provider, **provider_kwargs)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ImportError as e:
        print(f"Error: Missing SDK for {args.provider}: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Provider: {provider.name}")
    print(f"Model:    {provider.model}")
    print()

    run_tier3_evaluation(provider, questions, args.output,
                         delay_s=args.delay, selected_ids=selected_ids,
                         run_num=args.run, parallel=args.parallel)


if __name__ == "__main__":
    main()
