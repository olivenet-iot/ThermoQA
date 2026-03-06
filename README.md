# ThermoQA

A comprehensive benchmark for evaluating LLM performance on engineering thermodynamics — from steam table lookups to multi-step exergy analysis and full cycle calculations.

## Why ThermoQA?

Only 72 dedicated thermodynamics benchmark problems exist in the entire LLM evaluation literature. Neither existing set (UTQA: 50 MCQ, Loubet: 22 calc) touches engineering thermodynamics. ThermoQA fills this gap with CoolProp-verified ground truth across four difficulty tiers.

## Tiers

| Tier | Description | Status |
|------|-------------|--------|
| 1 | Property lookups (steam tables, phase determination) | In progress |
| 2 | Single-device energy/exergy balances | Planned |
| 3 | Multi-step cycle analysis | Planned |
| 4 | Open-ended system design | Planned |

## Phase 1: Water/Steam Property Lookups

Tier 1 covers 100-120 water/steam property lookup questions:
- Subcooled liquid, saturated, wet steam, superheated, supercritical states
- Phase determination from given conditions
- Inverse lookups (given properties, find state)

All ground truth values computed via CoolProp — no LLM-generated answers.

## Quick Start

```bash
pip install -r requirements.txt
python scripts/validate_coolprop.py   # Verify CoolProp installation
python scripts/generate_tier1.py      # Generate Tier 1 questions
```

## Scoring

Numerical answers scored with +/-2% relative tolerance (absolute fallback for near-zero values). Phase determination scored as exact match.

## Dependencies

- Python 3.10+
- CoolProp >= 6.6.0
- NumPy >= 1.24.0
- PyYAML >= 6.0
