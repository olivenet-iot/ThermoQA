# CLAUDE.md — ThermoQA Project Instructions

## Project Identity

**ThermoQA** is a comprehensive benchmark for evaluating LLM performance on engineering thermodynamics — from steam table lookups to multi-step exergy analysis and full cycle calculations. **No such benchmark exists today.** Only 72 dedicated thermodynamics benchmark problems exist in the entire LLM evaluation literature (UTQA: 50 MCQ, Loubet: 22 calc). Neither touches engineering thermodynamics.

**Owner:** Kemal Düzkar — chemical engineer, founder of Olivenet (KKTC). Built EntropyHunter v0.4 (92.7% adjusted accuracy, fine-tuned Qwen3-8B for exergy analysis, published on HuggingFace). This is not a toy project — this is the world's first engineering thermodynamics LLM benchmark.

**Repository:** `github.com/olivenet-iot/ThermoQA` (or kemal's github)
**Target publication:** arxiv paper: "ThermoQA: A Benchmark for Evaluating Thermodynamic Reasoning in Large Language Models"
**Target dataset:** HuggingFace `olivenet/thermoqa-v0.1`

---

## Critical Context: Read First

1. **Read `THERMOQA_HANDOFF.md`** in the project root — it contains the full architecture, competitive landscape, scoring design, and format decisions. That document is the source of truth.

2. **EntropyHunter taxonomy files** are at `~/entropy-hunter/taxonomy/`. These YAML files contain battle-tested equipment types, fluid properties, analysis types, operating conditions, output formats, and sector definitions from the predecessor project. **Reference them but do NOT copy them blindly** — ThermoQA has its own taxonomy needs (focused on property lookups and benchmark scoring, not training data generation).

3. **Ground truth comes from CoolProp, NEVER from LLM generation.** This is the #1 lesson from EntropyHunter: Opus is an excellent teacher but makes arithmetic errors. Every reference value must be computed programmatically via CoolProp.

4. **Water/steam only for Phase 1 (Tier 1).** No ideal gas, no refrigerants, no air. Single fluid, maximum depth. CoolProp fluid string: `'Water'`.

---

## Current Phase: Phase 1 — Tier 1: Property Lookups

### Goal
Build the complete generation + evaluation pipeline and produce 100-120 water/steam property lookup questions with CoolProp ground truth, a scorer, a runner, and a HuggingFace-ready dataset.

### What Tier 1 Tests
Single-step, exact-answer problems. Does the model know basic thermodynamic properties?
- Steam table lookups (given T, P → find h, s, v, u, rho, x)
- Phase determination (given T, P → what phase?)
- Saturation property lookups (given P → T_sat, h_f, h_g, s_f, s_g, etc.)
- Basic energy/entropy calculations from properties
- Scoring: ±2% relative tolerance against CoolProp, with absolute fallback for near-zero values

---

## Project Structure

```
ThermoQA/
├── CLAUDE.md                          # THIS FILE — project instructions
├── THERMOQA_HANDOFF.md                # Full architecture & design doc
├── README.md                          # Public-facing project description
├── .gitignore
├── pyproject.toml                     # Project metadata + dependencies
├── requirements.txt                   # CoolProp, numpy, etc.
│
├── taxonomy/
│   └── tier1_properties.yaml          # NEW: ThermoQA-specific property taxonomy
│
├── generation/
│   ├── __init__.py
│   ├── param_sampler.py               # Physics-valid parameter generation
│   ├── ground_truth.py                # CoolProp reference value computation
│   ├── question_generator.py          # Template → question + ground truth JSON
│   └── templates/
│       └── tier1_properties.py        # Parametric question templates (Python dataclasses)
│
├── evaluation/
│   ├── __init__.py
│   ├── extractor.py                   # Extract numerical values from model responses
│   ├── scorer.py                      # ±2% numerical matching + unit check
│   ├── runner.py                      # Ollama + API model execution
│   └── report.py                      # Results tables, leaderboard
│
├── data/
│   └── tier1_properties/              # Generated: question JSONs with ground truth
│       ├── questions.jsonl            # All questions in JSONL format
│       └── metadata.json              # Generation metadata, counts, distribution
│
├── results/                           # Model evaluation results (gitignored initially)
│
└── scripts/
    ├── generate_tier1.py              # CLI: generate all Tier 1 questions
    ├── run_evaluation.py              # CLI: run models against dataset
    └── validate_coolprop.py           # CLI: smoke test CoolProp installation
```

---

## Step-by-Step Implementation Plan

### Step 1: Project Skeleton + CoolProp Validation

1. Create the directory structure above
2. Set up `pyproject.toml` with metadata and dependencies
3. Create `requirements.txt`: `CoolProp>=6.6.0`, `numpy`, `pyyaml`
4. Install CoolProp: `pip install CoolProp`
5. Write `scripts/validate_coolprop.py`:
   - Compute h, s, v for superheated steam at 10 bar, 250°C
   - Compute saturated properties at 1, 10, 20, 40, 100 bar
   - Compare against the reference table in `~/entropy-hunter/taxonomy/fluid_properties.yaml` (steam.reference_table)
   - Verify dead state: T₀=298.15K, P₀=101325Pa → h₀, s₀
   - Print all values with units, show agreement
6. Create `.gitignore` (Python defaults + results/ + __pycache__ + .env)
7. Create initial `README.md`
8. **Commit: "Initial project structure + CoolProp validation"**

### Step 2: Tier 1 Property Taxonomy

Create `taxonomy/tier1_properties.yaml` — this defines the COMPLETE space of Tier 1 questions:

```yaml
# ThermoQA Tier 1 Property Taxonomy
# Fluid: Water/Steam only (Phase 1)
# This file defines WHAT we test, not HOW we test it

fluid: Water  # CoolProp fluid string

phases:
  subcooled_liquid:
    description: "T < T_sat at given P, or P > P_sat at given T"
    given_pairs: [[T, P]]  # T and P both known, T < T_sat(P)
    target_properties: [h, s, v, u, rho, phase_name]
    param_ranges:
      T_C: [20, 180]       # Below saturation
      P_kPa: [200, 10000]  # 2-100 bar
    n_questions: 10-12
    notes: "Ensure T is at least 5°C below T_sat(P) to avoid near-boundary ambiguity"

  saturated_liquid:
    description: "On the saturation curve, x = 0"
    given_pairs: [[P], [T]]  # Given P → find T_sat and liquid props, or given T → find P_sat
    target_properties: [T_sat_or_P_sat, h_f, s_f, v_f, u_f, rho_f]
    param_ranges:
      P_kPa: [100, 10000]   # 1-100 bar
      # or T_C: [100, 311]   # Saturation range
    n_questions: 12-15
    notes: "Include both P-given and T-given variants"

  wet_steam:
    description: "Two-phase mixture, 0 < x < 1"
    given_pairs: [[P, x], [T, x], [P, h], [P, s]]
    target_properties: [h, s, v, u, T_sat_or_P_sat, phase_name]
    param_ranges:
      P_kPa: [100, 8000]
      x: [0.1, 0.9]         # Avoid trivial x near 0 or 1
    n_questions: 15-18
    notes: |
      Most discriminating category. Models often fail wet steam.
      Include inverse problems: given h and P, find x.
      Formulas: h = h_f + x*(h_g - h_f), s = s_f + x*(s_g - s_f)

  saturated_vapor:
    description: "On the saturation curve, x = 1"
    given_pairs: [[P], [T]]
    target_properties: [T_sat_or_P_sat, h_g, s_g, v_g, u_g, rho_g]
    param_ranges:
      P_kPa: [100, 10000]
    n_questions: 10-12

  superheated_vapor:
    description: "T > T_sat at given P"
    given_pairs: [[T, P]]
    target_properties: [h, s, v, u, rho, phase_name]
    param_ranges:
      T_C: [120, 600]       # Superheated range
      P_kPa: [100, 15000]   # 1-150 bar
    n_questions: 18-22
    notes: |
      Most common engineering scenario. Ensure T > T_sat(P) + 10°C minimum.
      Include high superheat (500°C+) and moderate superheat cases.

  supercritical:
    description: "T > T_crit (373.95°C) AND P > P_crit (22.064 MPa)"
    given_pairs: [[T, P]]
    target_properties: [h, s, v, u, rho, phase_name]
    param_ranges:
      T_C: [380, 600]
      P_kPa: [23000, 35000]  # Above critical pressure
    n_questions: 8-10
    notes: "Edge case — many models don't know critical point. Very discriminating."

  # === SPECIAL QUESTION TYPES ===

  phase_determination:
    description: "Given T and P, determine the phase (no property calculation)"
    target_properties: [phase_name]
    n_questions: 10-12
    notes: |
      Include tricky cases near saturation line.
      Model must compare T with T_sat(P) to determine phase.
      Categories: clearly subcooled, clearly superheated, near-boundary, supercritical

  inverse_lookups:
    description: "Given a property value, find T or P or x"
    given_pairs: [[P, h], [P, s], [T, h], [h, s]]  # Two properties → find state
    target_properties: [T, P, x, phase_name]
    n_questions: 10-12
    notes: |
      Hardest Tier 1 category. Requires understanding state determination.
      Example: "Steam at 500 kPa has h = 2700 kJ/kg. What is its temperature?"

# Total target: 100-120 questions
# Distribution ensures coverage across ALL phases and question types
```

**Design the actual taxonomy based on this skeleton. Adjust n_questions to hit 100-120 total, ensuring good coverage of edge cases and discriminating problems.**

**Commit: "Tier 1 property taxonomy"**

### Step 3: Template Engine + Parameter Sampler

Create the parametric template system:

**`generation/templates/tier1_properties.py`:**
- Python dataclasses defining each question template
- Each template has: `template_id`, `category` (phase), `given_params`, `target_properties`, `param_ranges`, `question_text_template` (string with {placeholders}), `difficulty_notes`
- Example template:

```python
@dataclass
class PropertyTemplate:
    template_id: str
    category: str           # phase name from taxonomy
    given_params: list       # e.g., ["T_C", "P_kPa"]
    target_properties: list  # e.g., ["h_kJ_kg", "s_kJ_kgK", "v_m3_kg"]
    param_ranges: dict       # e.g., {"T_C": (120, 600), "P_kPa": (100, 15000)}
    question_template: str   # "Determine the specific enthalpy, entropy, and specific volume of steam at {T_C}°C and {P_kPa} kPa."
    constraints: list        # e.g., ["T_C > T_sat(P_kPa) + 10"] — physics validity
    notes: str = ""
```

**`generation/param_sampler.py`:**
- Takes a template + desired count → generates physically valid parameter sets
- For superheated: ensures T > T_sat(P) + margin
- For subcooled: ensures T < T_sat(P) - margin
- For wet steam: ensures 0.1 < x < 0.9 (avoids trivial)
- For supercritical: ensures T > 373.95°C AND P > 22064 kPa
- Uses CoolProp for T_sat lookups during parameter validation
- Produces diverse values (not clustered) — spread across the param range
- Returns list of dicts: `[{"T_C": 350, "P_kPa": 2000}, ...]`

**Commit: "Template engine + parameter sampler"**

### Step 4: Ground Truth Generator

**`generation/ground_truth.py`:**
- Takes a template + parameter set → computes ALL reference values via CoolProp
- Core function: `compute_properties(fluid, given_params) -> dict`
- Uses `CoolProp.CoolProp.PropsSI()` for all calculations
- **Unit conversions** (CoolProp returns SI: J, K, Pa):
  - h: J/kg → kJ/kg (÷1000)
  - s: J/(kg·K) → kJ/(kg·K) (÷1000)
  - v: m³/kg (no conversion)
  - u: J/kg → kJ/kg (÷1000)
  - T: K → °C (-273.15)
  - P: Pa → kPa (÷1000)
  - rho: kg/m³ (no conversion)
  - x: dimensionless (0-1), only in two-phase region
- Phase determination via CoolProp phase string
- Dead state reference: T₀ = 298.15 K (25°C), P₀ = 101.325 kPa
- **Every value cross-checked**: compute forward AND verify (e.g., for wet steam: compute h from x, then verify x from h)

**`generation/question_generator.py`:**
- Orchestrates: taxonomy → templates → param_sampler → ground_truth → JSON output
- Each question output:

```json
{
  "id": "T1-SH-001",
  "tier": 1,
  "category": "superheated_vapor",
  "question": "Determine the specific enthalpy (h), specific entropy (s), and specific volume (v) of superheated steam at 350°C and 2000 kPa.",
  "given": {
    "T_C": 350,
    "P_kPa": 2000,
    "fluid": "Water"
  },
  "expected": {
    "h_kJ_kg": {"value": 3137.7, "unit": "kJ/kg", "tolerance_pct": 2.0},
    "s_kJ_kgK": {"value": 6.9583, "unit": "kJ/(kg·K)", "tolerance_pct": 2.0},
    "v_m3_kg": {"value": 0.13857, "unit": "m³/kg", "tolerance_pct": 2.0},
    "phase": {"value": "superheated_vapor", "type": "exact_match"}
  },
  "metadata": {
    "template_id": "SH-MULTI-001",
    "coolprop_version": "6.6.0",
    "generated_at": "2026-03-06T...",
    "difficulty": "easy"
  }
}
```

- ID convention: `T1-{CATEGORY_CODE}-{NUMBER}`
  - Category codes: SL (subcooled liquid), SF (saturated liquid), WS (wet steam), SV (saturated vapor), SH (superheated), SC (supercritical), PD (phase determination), IL (inverse lookup)
- Output to `data/tier1_properties/questions.jsonl` (one JSON per line)
- Generate `data/tier1_properties/metadata.json` with distribution stats

**`scripts/generate_tier1.py`:**
- CLI entry point: `python scripts/generate_tier1.py --output data/tier1_properties/ --count 110`
- Prints summary: questions per category, parameter ranges used, any warnings

**Commit: "Ground truth generator + question generation pipeline"**

---

## Technical Rules

### CoolProp Usage
```python
from CoolProp.CoolProp import PropsSI

# ALWAYS use SI inputs: T in K, P in Pa
# ALWAYS convert outputs to engineering units for the question/answer

# Superheated: T and P known
h = PropsSI('H', 'T', T_K, 'P', P_Pa, 'Water') / 1000  # → kJ/kg
s = PropsSI('S', 'T', T_K, 'P', P_Pa, 'Water') / 1000  # → kJ/(kg·K)
v = 1.0 / PropsSI('D', 'T', T_K, 'P', P_Pa, 'Water')   # → m³/kg

# Saturated: use quality Q
h_f = PropsSI('H', 'P', P_Pa, 'Q', 0, 'Water') / 1000   # saturated liquid
h_g = PropsSI('H', 'P', P_Pa, 'Q', 1, 'Water') / 1000   # saturated vapor
T_sat = PropsSI('T', 'P', P_Pa, 'Q', 0, 'Water') - 273.15  # → °C

# Wet steam: h = h_f + x*(h_g - h_f)
h_wet = PropsSI('H', 'P', P_Pa, 'Q', x, 'Water') / 1000

# Phase determination
phase = PropsSI('Phase', 'T', T_K, 'P', P_Pa, 'Water')
# CoolProp phase indices: 0=liquid, 5=gas, 6=twophase, 3=supercritical, etc.
# Map these to human-readable: subcooled_liquid, superheated_vapor, wet_steam, etc.

# Critical point
T_crit = PropsSI('Tcrit', 'Water')   # 647.096 K
P_crit = PropsSI('Pcrit', 'Water')   # 22064000 Pa
```

### CoolProp Phase Mapping
```python
PHASE_MAP = {
    0: "subcooled_liquid",       # Liquid (subcooled / compressed)
    2: "supercritical",          # Supercritical
    3: "supercritical_gas",      # Supercritical gas
    4: "supercritical_liquid",   # Supercritical liquid  
    5: "superheated_vapor",      # Gas (superheated)
    6: "wet_steam",              # Two-phase
    8: "not_imposed",
}
# Verify this mapping against CoolProp docs — phase index values may vary by version.
# Always test with known states.
```

### Scoring Rules for Tier 1
```python
def check_value(expected: float, actual: float, tolerance_pct: float = 2.0, abs_min: float = 0.5) -> bool:
    """
    Pass if within ±tolerance_pct OR within ±abs_min (whichever is more lenient).
    abs_min handles near-zero values (e.g., subcooled liquid entropy near 0).
    """
    if expected == 0:
        return abs(actual) <= abs_min
    relative_error = abs((actual - expected) / expected) * 100
    absolute_error = abs(actual - expected)
    return relative_error <= tolerance_pct or absolute_error <= abs_min
```

### Question Text Guidelines
- Write in clear, unambiguous English
- Always specify the fluid ("steam" or "water" — context appropriate)
- Always give units for input parameters
- Always list which properties to find
- Use engineering conventions: pressure in kPa or MPa (not Pa), temperature in °C (not K)
- Include "Assume steady-state conditions" where relevant
- Do NOT give hints about the phase — let the model determine it
- Vary question phrasing across templates (don't make all questions identical in structure)

### Question Phrasing Variety
Use diverse question formats to avoid pattern-matching:
- "Determine the specific enthalpy of steam at..."
- "What is the specific entropy of water at..."  
- "Find the specific volume and internal energy of steam at..."
- "Steam enters a system at X kPa and Y°C. What are its thermodynamic properties (h, s, v)?"
- "At a pressure of X kPa, what is the saturation temperature of water?"
- "A wet steam mixture at X kPa has a quality of Y. Calculate h, s, and v."
- "Steam at X kPa has a specific enthalpy of Y kJ/kg. Determine its temperature and phase."

---

## What NOT to Do

- **Do NOT use LLMs to generate ground truth values.** CoolProp only.
- **Do NOT hardcode property values.** Always compute from CoolProp at generation time.
- **Do NOT include MCQ format.** All questions are open calculation (per handoff decision).
- **Do NOT include ideal gas, refrigerants, or air in Tier 1.** Water/steam only.
- **Do NOT over-engineer the runner/scorer yet.** Keep it simple for v0.1 — we'll extend for Tier 2.
- **Do NOT create complex class hierarchies.** Flat, readable Python. Dataclasses, not OOP forests.
- **Do NOT skip unit conversions.** CoolProp SI ↔ engineering units is where bugs hide.

---

## Git Workflow

- Commit after each meaningful step (see Step 1-4 commit messages above)
- Use conventional commits: `feat:`, `fix:`, `docs:`, `test:`
- Push after each commit
- Branch: work on `main` for now (solo project, fast iteration)

---

## Dependencies

```
CoolProp>=6.6.0
numpy>=1.24.0
pyyaml>=6.0
```

Python 3.10+ required.

---

## Reference Files

- `THERMOQA_HANDOFF.md` — Full project architecture and competitive landscape (IN PROJECT ROOT)
- `~/entropy-hunter/taxonomy/equipment.yaml` — 7 equipment types, 48 subtypes (reference for Tier 2)
- `~/entropy-hunter/taxonomy/fluid_properties.yaml` — Fluid properties with steam reference table (USE FOR VALIDATION)
- `~/entropy-hunter/taxonomy/analysis_types.yaml` — ExergyLab analysis engines (reference for Tier 2-3)
- `~/entropy-hunter/taxonomy/operating_conditions.yaml` — Operating modes (reference for Tier 2-3)
- `~/entropy-hunter/taxonomy/output_format.yaml` — Response format spec (reference for extractor design)
- `~/entropy-hunter/taxonomy/sectors.yaml` — Industry sectors (reference for Tier 4)

---

## Success Criteria for Phase 1

1. ✅ `scripts/validate_coolprop.py` runs clean, matches fluid_properties.yaml reference table
2. ✅ `taxonomy/tier1_properties.yaml` covers all 8 categories with well-defined param ranges
3. ✅ `scripts/generate_tier1.py` produces 100-120 questions in `data/tier1_properties/`
4. ✅ Every question's ground truth is CoolProp-verified (no manual values)
5. ✅ Distribution is balanced across phases and question types
6. ✅ Edge cases included: near-critical, low-quality wet steam, supercritical, inverse lookups
7. ✅ `evaluation/scorer.py` correctly scores known-good and known-bad answers
8. ✅ `evaluation/extractor.py` can parse at least 3 different response formats
9. ✅ Dataset is in HuggingFace-compatible JSONL format
10. ✅ README.md clearly explains what ThermoQA is and how to use it
