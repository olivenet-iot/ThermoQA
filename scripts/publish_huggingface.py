#!/usr/bin/env python3
"""
Publish ThermoQA dataset to HuggingFace Hub.

Usage:
    export HF_TOKEN=hf_xxx
    python scripts/publish_huggingface.py                    # Publish all tiers
    python scripts/publish_huggingface.py --tier 1           # Publish only Tier 1
    python scripts/publish_huggingface.py --tier 2           # Publish only Tier 2
    python scripts/publish_huggingface.py --tier 3           # Publish only Tier 3
    python scripts/publish_huggingface.py --dry-run          # List files without uploading
    python scripts/publish_huggingface.py --repo olivenet/thermoqa-test  # Custom repo
"""

import argparse
import io
import json
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from huggingface_hub import CommitOperationAdd, HfApi


DATASET_FRONTMATTER = """\
---
language:
  - en
license: cc-by-4.0
task_categories:
  - question-answering
tags:
  - thermodynamics
  - benchmark
  - engineering
  - steam-tables
  - coolprop
  - exergy
  - iapws-if97
  - component-analysis
  - r134a
  - cycle-analysis
pretty_name: ThermoQA
size_categories:
  - n<1K
configs:
  - config_name: tier1_properties
    data_files:
      - split: test
        path: tier1_properties/questions.jsonl
  - config_name: tier2_components
    data_files:
      - split: test
        path: tier2_components/questions.jsonl
  - config_name: tier3_cycles
    data_files:
      - split: test
        path: tier3_cycles/questions.jsonl
---
"""

PROVIDERS = ["anthropic", "deepseek", "google", "minimax", "openai"]

TIER1_KEEP = {"id", "model", "response_text", "extracted", "scores", "question_score", "input_tokens", "output_tokens"}
TIER2_KEEP = TIER1_KEEP | {"component", "depth", "fluid", "steps"}
TIER3_KEEP = TIER1_KEEP | {"cycle_type", "depth", "fluid", "steps"}

TIER_CONFIG = {
    1: {
        "questions_path": os.path.join(PROJECT_ROOT, "data", "tier1_properties", "questions.jsonl"),
        "results_dir": os.path.join(PROJECT_ROOT, "results"),
        "repo_prefix": "tier1_properties",
        "keep_fields": TIER1_KEEP,
    },
    2: {
        "questions_path": os.path.join(PROJECT_ROOT, "data", "tier2_components", "questions.jsonl"),
        "results_dir": os.path.join(PROJECT_ROOT, "results_tier2"),
        "repo_prefix": "tier2_components",
        "keep_fields": TIER2_KEEP,
    },
    3: {
        "questions_path": os.path.join(PROJECT_ROOT, "data", "tier3_cycles", "questions.jsonl"),
        "results_dir": os.path.join(PROJECT_ROOT, "results_tier3"),
        "repo_prefix": "tier3_cycles",
        "keep_fields": TIER3_KEEP,
    },
}


def strip_result(row: dict, tier: int) -> dict:
    """Strip large/unnecessary fields from a result row."""
    keep = TIER_CONFIG[tier]["keep_fields"]
    return {k: v for k, v in row.items() if k in keep}


def stringify_nested(row: dict) -> dict:
    """Convert nested dict/list values to JSON strings.

    The HF dataset viewer auto-infers 'Json' feature type for nested objects,
    which is unsupported by datasets<4.7.0. Stringifying avoids this.
    """
    out = {}
    for k, v in row.items():
        if isinstance(v, (dict, list)):
            out[k] = json.dumps(v, ensure_ascii=False)
        else:
            out[k] = v
    return out


def build_operations(tiers: list[int]) -> list[CommitOperationAdd]:
    """Build list of commit operations for the specified tiers."""
    operations = []

    # 1. README.md (dataset card with frontmatter)
    readme_path = os.path.join(PROJECT_ROOT, "README.md")
    if not os.path.isfile(readme_path):
        print(f"Error: {readme_path} not found.")
        sys.exit(1)

    with open(readme_path, "r") as f:
        readme_content = f.read()

    dataset_card = DATASET_FRONTMATTER + readme_content
    operations.append(CommitOperationAdd(
        path_in_repo="README.md",
        path_or_fileobj=io.BytesIO(dataset_card.encode("utf-8")),
    ))
    print(f"  README.md (dataset card)")

    # 2. Per-tier files
    for tier in sorted(tiers):
        cfg = TIER_CONFIG[tier]
        prefix = cfg["repo_prefix"]

        # Questions file (stringify nested JSON to avoid HF viewer 'Json' type inference)
        if not os.path.isfile(cfg["questions_path"]):
            print(f"Error: {cfg['questions_path']} not found.")
            sys.exit(1)

        q_lines = []
        with open(cfg["questions_path"], "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                q_lines.append(json.dumps(stringify_nested(row), ensure_ascii=False))

        q_buffer = io.BytesIO(("\n".join(q_lines) + "\n").encode("utf-8"))
        operations.append(CommitOperationAdd(
            path_in_repo=f"{prefix}/questions.jsonl",
            path_or_fileobj=q_buffer,
        ))
        print(f"  {prefix}/questions.jsonl ({len(q_lines)} rows, nested fields stringified)")

        # Result files per provider
        for provider in PROVIDERS:
            responses_path = os.path.join(cfg["results_dir"], provider, "responses.jsonl")
            if not os.path.isfile(responses_path):
                print(f"  Warning: {responses_path} not found, skipping")
                continue

            # Read, strip, and serialize
            stripped_lines = []
            with open(responses_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    row = json.loads(line)
                    stripped = strip_result(row, tier)
                    stripped_lines.append(json.dumps(stripped, ensure_ascii=False))

            buffer = io.BytesIO(("\n".join(stripped_lines) + "\n").encode("utf-8"))
            repo_path = f"{prefix}/results/{provider}.jsonl"
            operations.append(CommitOperationAdd(
                path_in_repo=repo_path,
                path_or_fileobj=buffer,
            ))
            print(f"  {repo_path} ({len(stripped_lines)} rows)")

    return operations


def get_token() -> str:
    """Get HF token from environment, .env file, or HF cache."""
    token = os.environ.get("HF_TOKEN")
    if token:
        return token

    # Try .env file
    env_path = os.path.join(PROJECT_ROOT, ".env")
    if os.path.isfile(env_path):
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith("HF_TOKEN="):
                    token = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if token:
                        return token

    # Try HF cache (from `huggingface-cli login`)
    for cache_path in [
        os.path.expanduser("~/.cache/huggingface/token"),
        os.path.expanduser("~/.huggingface/token"),
    ]:
        if os.path.isfile(cache_path):
            with open(cache_path, "r") as f:
                token = f.read().strip()
                if token:
                    return token

    print("Error: HF_TOKEN not found.")
    print("  Set HF_TOKEN environment variable or add it to .env")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Publish ThermoQA dataset to HuggingFace Hub")
    parser.add_argument("--repo", default="olivenet/thermoqa", help="HuggingFace repo ID (default: olivenet/thermoqa)")
    parser.add_argument("--tier", type=int, choices=[1, 2, 3], help="Publish only this tier (default: all)")
    parser.add_argument("--dry-run", action="store_true", help="List files without uploading")
    args = parser.parse_args()

    tiers = [args.tier] if args.tier else [1, 2, 3]

    print(f"Building upload for: {', '.join(f'Tier {t}' for t in tiers)}")
    print(f"Target repo: {args.repo}")
    print()

    operations = build_operations(tiers)

    print(f"\nTotal: {len(operations)} files")

    if args.dry_run:
        print("\n[DRY RUN] No files uploaded.")
        return

    token = get_token()

    print(f"\nUploading to {args.repo}...")
    api = HfApi(token=token)
    api.create_repo(args.repo, repo_type="dataset", exist_ok=True)

    tier_desc = " + ".join(f"Tier {t}" for t in tiers)
    commit_info = api.create_commit(
        repo_id=args.repo,
        repo_type="dataset",
        operations=operations,
        commit_message=f"Update dataset card: remove Tier 4 placeholder, add future work",
    )

    print(f"\nDone! Commit: {commit_info.commit_url}")
    print(f"Dataset: https://huggingface.co/datasets/{args.repo}")
    print(f"\nTest with:")
    print(f'  from datasets import load_dataset')
    print(f'  t1 = load_dataset("{args.repo}", "tier1_properties", split="test")')
    print(f'  t2 = load_dataset("{args.repo}", "tier2_components", split="test")')
    print(f'  t3 = load_dataset("{args.repo}", "tier3_cycles", split="test")')
    print(f'  print(len(t1), len(t2), len(t3))  # 110, 101, 82')


if __name__ == "__main__":
    main()
