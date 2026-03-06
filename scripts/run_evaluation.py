#!/usr/bin/env python3
"""
CLI script to run ThermoQA evaluations against LLM providers.

Usage:
    python scripts/run_evaluation.py --provider anthropic
    python scripts/run_evaluation.py --provider ollama --model llama3
    python scripts/run_evaluation.py --report results/
"""

import argparse
import os
import sys

# Ensure project root is on path when running as script
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evaluation.runner import PROVIDERS, get_provider, run_evaluation
from evaluation.report import generate_leaderboard, print_detailed_report


def main():
    parser = argparse.ArgumentParser(
        description="Run ThermoQA evaluations against LLM providers"
    )
    parser.add_argument(
        "--provider",
        choices=list(PROVIDERS.keys()),
        help="LLM provider to evaluate",
    )
    parser.add_argument(
        "--model",
        help="Override default model for the provider",
    )
    parser.add_argument(
        "--questions", default="data/tier1_properties/questions.jsonl",
        help="Path to questions JSONL (default: data/tier1_properties/questions.jsonl)",
    )
    parser.add_argument(
        "--output", default="results/",
        help="Output directory for results (default: results/)",
    )
    parser.add_argument(
        "--n-runs", type=int, default=1,
        help="Number of evaluation runs (default: 1)",
    )
    parser.add_argument(
        "--delay", type=float, default=1.0,
        help="Delay between API calls in seconds (default: 1.0)",
    )
    parser.add_argument(
        "--timeout", type=float, default=120.0,
        help="API timeout in seconds (default: 120)",
    )
    parser.add_argument(
        "--report",
        nargs="?", const="results/",
        help="Print leaderboard and detailed reports. Optionally specify results dir.",
    )
    args = parser.parse_args()

    if args.report is not None:
        results_dir = args.report
        print(generate_leaderboard(results_dir))

        # Print detailed report for each provider
        if os.path.isdir(results_dir):
            for name in sorted(os.listdir(results_dir)):
                provider_dir = os.path.join(results_dir, name)
                if os.path.isfile(os.path.join(provider_dir, "responses.jsonl")):
                    print()
                    print_detailed_report(provider_dir, args.questions)
        return

    if not args.provider:
        parser.error("--provider is required unless using --report")

    # Build provider kwargs
    provider_kwargs = {"timeout": args.timeout}
    if args.model:
        provider_kwargs["model"] = args.model

    try:
        provider = get_provider(args.provider, **provider_kwargs)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ImportError as e:
        print(f"Error: Missing SDK for {args.provider}: {e}", file=sys.stderr)
        print(f"Install with: pip install thermoqa[eval]", file=sys.stderr)
        sys.exit(1)

    print(f"Provider: {provider.name}")
    print(f"Model:    {provider.model}")
    print(f"Questions: {args.questions}")
    print(f"Output:   {args.output}")
    print()

    run_evaluation(
        provider=provider,
        questions_path=args.questions,
        output_dir=args.output,
        n_runs=args.n_runs,
        delay_s=args.delay,
    )


if __name__ == "__main__":
    main()
