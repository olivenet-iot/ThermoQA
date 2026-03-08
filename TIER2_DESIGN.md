# ThermoQA — Tier 2: Component Analysis
## Design Document — Draft v0.1
### 8 March 2026

---

## 1. Overview

Tier 1 tested property lookups — "given T and P, find h, s, v." Single-step, single-answer.

Tier 2 tests **component-level thermodynamic analysis** — "given a turbine with inlet/outlet conditions, calculate work output, entropy generation, exergy destruction, and second-law efficiency." Multi-step, 3–6 calculation steps per problem, with partial credit for correct intermediate results.

**Why this matters:** This is where EntropyHunter lives. Tier 2 directly evaluates whether models can perform the kind of second-law analysis that EntropyHunter was trained for. It's also the bridge between "can the model look up properties?" (Tier 1) and "can the model analyze a full cycle?" (Tier 3).

---

## 2. Component Types

Seven standard steady-state flow devices from Çengel & Boles Ch. 5–8:

| # | Component | Key Equation | Typical Steps | Complexity |
|---|-----------|-------------|---------------|------------|
| 1 | **Turbine** | w_out = h₁ − h₂ | 4–5 | Medium |
| 2 | **Compressor** | w_in = h₂ − h₁ | 4–5 | Medium |
| 3 | **Pump** | w_in = v₁(P₂ − P₁) or h₂ − h₁ | 4–5 | Medium |
| 4 | **Heat Exchanger** | q = ṁ(h₂ − h₁) per stream | 5–6 | High |
| 5 | **Boiler** | q_in = h_out − h_in, η_II via Carnot | 5–6 | High |
| 6 | **Mixing Chamber** | ṁ₁h₁ + ṁ₂h₂ = ṁ₃h₃ | 4–5 | Medium |
| 7 | **Nozzle/Diffuser** | V₂² = V₁² + 2(h₁ − h₂) | 4–5 | Medium |

### Question Distribution (Target: ~100 questions)

| Component | Count | Rationale |
|-----------|-------|-----------|
| Turbine | 18 | Core power cycle component, many state variations |
| Compressor | 14 | Similar to turbine but work-input device |
| Pump | 10 | Compressed liquid handling, v·ΔP approximation |
| Heat Exchanger | 18 | Two liquid streams, sensible heat only |
| Boiler | 14 | Massive exergy destruction, Carnot factor test, phase change |
| Mixing Chamber | 12 | Mass + energy balance coupling |
| Nozzle/Diffuser | 14 | Kinetic energy term, velocity calculations |
| **Total** | **~100** | |

---

## 3. Analysis Depth Levels

Each question has a **depth level** that determines how many calculation steps are required:

### Level A — First Law Only (energy balance)
- Steps: Property lookup → Energy balance → Work/heat transfer
- Properties tested: h, s at inlet/outlet
- Answers: w, q, or exit state
- ~30% of questions

### Level B — First + Second Law (entropy generation)
- Steps: Level A + Entropy balance → ΔS_total = S_gen
- S_gen = ṁ(s₂ − s₁) + Q_surr/T_surr (for adiabatic: S_gen = ṁ(s₂ − s₁))
- Answers: Level A + s_gen, ΔS_universe
- ~35% of questions

### Level C — Exergy Analysis (full second-law)
- Steps: Level B + Exergy balance → X_destroyed = T₀·S_gen
- Second-law efficiency: η_II = X_recovered / X_expended
- Answers: Level B + x_destroyed, η_II
- ~35% of questions

This maps directly to EntropyHunter's taxonomy: Level A = energy, Level B = entropy, Level C = exergy (SPECO).

---

## 4. Anchor-Derive Pattern for State Generation

### The Problem
If we randomly sample inlet T, P, outlet T, P independently, we get physically impossible states — e.g., a turbine where s₂ < s₁ (impossible in real adiabatic expansion) or a heat exchanger where the hot stream exits hotter than it enters.

### The Solution: EntropyHunter's Anchor-Derive Pattern
1. **Anchor** a physically meaningful starting state (e.g., superheated steam at turbine inlet)
2. **Define** the process constraint (e.g., isentropic efficiency η_s = 0.85)
3. **Derive** the exit state from physics:
   - Ideal exit: s₂s = s₁ (isentropic)
   - Actual exit: h₂ = h₁ − η_s(h₁ − h₂s)
4. **All intermediate properties** computed from CoolProp at the derived state

### State Generation Strategy Per Component

```
TURBINE:
  anchor: {T₁, P₁} → superheated steam (sample from Tier 1 ranges)
  constraint: P₂ < P₁ (expansion), η_s ∈ [0.70, 0.95]
  derive:
    h₁, s₁ = CoolProp(T₁, P₁)
    h₂s = CoolProp(s=s₁, P=P₂)        # isentropic exit
    h₂ = h₁ - η_s * (h₁ - h₂s)        # actual exit
    T₂, s₂, x₂ = CoolProp(h=h₂, P=P₂) # derive all exit props
  given_to_model: {T₁, P₁, P₂, η_s} or {T₁, P₁, T₂, P₂}

COMPRESSOR:
  anchor: {T₁, P₁} → low-pressure gas/vapor
  constraint: P₂ > P₁ (compression), η_s ∈ [0.75, 0.90]
  derive: same as turbine but w_in = h₂ - h₁

PUMP:
  anchor: {T₁, P₁} → compressed liquid or saturated liquid
  constraint: P₂ >> P₁, η_s ∈ [0.70, 0.90]
  derive:
    v₁ = CoolProp(T₁, P₁)
    w_pump_ideal = v₁ * (P₂ - P₁)  # kJ/kg
    h₂ = h₁ + w_pump_ideal / η_s
    OR full CoolProp: h₂s = CoolProp(s=s₁, P=P₂)

HEAT_EXCHANGER:
  anchor: {T_hot_in, P_hot, T_cold_in, P_cold}
  constraint: ΔT_approach ∈ [5, 30] K, both streams liquid (no phase change)
  derive:
    q = ṁ_hot * c_p_hot * (T_hot_in - T_hot_out)   # or enthalpy-based
        = ṁ_cold * c_p_cold * (T_cold_out - T_cold_in)
    sub-types: counter-flow, parallel-flow (both sensible heat only)
  fluids: Water-Water, Water-R134a(liquid)

BOILER (replaces Throttling Valve):
  anchor: {T_in, P} → compressed liquid entering boiler
  constraint: T_out > T_sat(P), T_source ∈ [800, 2000] K (combustion gases)
  derive:
    h_in, s_in = CoolProp(T=T_in, P=P)         # compressed liquid
    h_out, s_out = CoolProp(T=T_out, P=P)       # superheated steam
    q_in = h_out - h_in                          # heat added per unit mass
    s_gen = (s_out - s_in) - q_in / T_source     # entropy balance
    x_dest = T₀ · s_gen                          # exergy destroyed
    η_II = (ψ_out - ψ_in) / [q_in · (1 - T₀/T_source)]
    # numerator: exergy gained by working fluid
    # denominator: exergy of heat from source (Carnot factor × Q)
  notes: >
    Boiler is the largest exergy destroyer in most power plants.
    The Carnot factor (1 - T₀/T_source) is the key discriminator —
    models must know that heat has exergy proportional to its temperature level.

MIXING_CHAMBER:
  anchor: {T₁, P, ṁ₁} + {T₂, P, ṁ₂} (same pressure, isobaric mixing)
  constraint: ṁ₃ = ṁ₁ + ṁ₂, energy balance
  derive:
    h₃ = (ṁ₁·h₁ + ṁ₂·h₂) / ṁ₃
    T₃, s₃ = CoolProp(h=h₃, P=P)

NOZZLE:
  anchor: {T₁, P₁, V₁} → high-pressure, low-velocity
  constraint: P₂ < P₁, η_nozzle ∈ [0.90, 0.98]
  derive:
    h₂s = CoolProp(s=s₁, P=P₂)
    V₂² = V₁² + 2·η_nozzle·(h₁ - h₂s) · 1000  # kJ→J
    h₂ = h₁ - (V₂² - V₁²) / (2·1000)
```

---

## 5. Question Templates

### Template Structure

Each template is a parameterized question with:
- `component`: one of 7 types
- `depth`: A, B, or C
- `given`: the information presented to the model
- `find`: what the model must calculate
- `steps`: ordered list of intermediate calculations (for step-level scoring)
- `expected`: dict of {property: value} with tolerances

### Example Templates

#### T2-TRB-01: Adiabatic Steam Turbine (Depth C — Full Exergy)

```
Steam enters an adiabatic turbine at {T1}°C and {P1} MPa and exits at {P2} MPa.
The isentropic efficiency of the turbine is {eta_s}%.
The dead state is T₀ = {T0}°C, P₀ = {P0} MPa.

Determine:
(a) the actual work output per unit mass (kJ/kg)
(b) the entropy generation per unit mass (kJ/kg·K)
(c) the exergy destruction per unit mass (kJ/kg)
(d) the second-law (exergetic) efficiency

Steps (internal, for scoring):
  step_1: h₁ = CoolProp(T={T1}, P={P1}) → h₁
  step_2: s₁ = CoolProp(T={T1}, P={P1}) → s₁
  step_3: h₂s = CoolProp(s=s₁, P={P2}) → h₂s (isentropic exit)
  step_4: h₂ = h₁ - η_s·(h₁ - h₂s) → h₂ (actual exit)
  step_5: w_out = h₁ - h₂
  step_6: s₂ = CoolProp(h=h₂, P={P2}) → s₂
  step_7: s_gen = s₂ - s₁ (adiabatic, so no Q/T term)
  step_8: x_destroyed = T₀ · s_gen
  step_9: η_II = w_out / (Δψ) where Δψ = (h₁-h₂) - T₀(s₁-s₂)
```

#### T2-BLR-01: Steam Boiler with External Heat Source (Depth C — Full Exergy)

```
Water enters a boiler as compressed liquid at {T_in}°C and {P} MPa.
It exits as superheated steam at {T_out}°C and {P} MPa (constant pressure).
The heat is supplied by combustion gases at an average temperature of {T_source} K.
The dead state is T₀ = 25°C, P₀ = 0.1 MPa.

Determine:
(a) the heat input per unit mass (kJ/kg)
(b) the entropy generation per unit mass (kJ/kg·K)
(c) the exergy destruction per unit mass (kJ/kg)
(d) the second-law (exergetic) efficiency

Steps:
  step_1: h_in = CoolProp(T={T_in}, P={P})
  step_2: s_in = CoolProp(T={T_in}, P={P})
  step_3: h_out = CoolProp(T={T_out}, P={P})
  step_4: s_out = CoolProp(T={T_out}, P={P})
  step_5: q_in = h_out - h_in
  step_6: s_gen = (s_out - s_in) - q_in / T_source
  step_7: x_dest = T₀_K · s_gen
  step_8: ψ_in = (h_in - h₀) - T₀(s_in - s₀)
  step_9: ψ_out = (h_out - h₀) - T₀(s_out - s₀)
  step_10: η_II = (ψ_out - ψ_in) / [q_in · (1 - T₀/T_source)]
```

#### T2-HX-01: Counter-Flow Heat Exchanger — Two Liquid Streams (Depth C)

```
In a counter-flow heat exchanger, hot water enters at {T_h_in}°C
and {P_h} MPa with a mass flow rate of {m_h} kg/s, and exits at {T_h_out}°C.
Cold water enters at {T_c_in}°C and {P_c} MPa with a mass flow rate of {m_c} kg/s.
Both streams remain in the liquid phase throughout.
The dead state is T₀ = 25°C, P₀ = 0.1 MPa.

Determine:
(a) the exit temperature of the cold stream (°C)
(b) the total entropy generation rate (kW/K)
(c) the total exergy destruction rate (kW)
(d) the second-law efficiency

Steps:
  step_1: h_h_in, s_h_in = CoolProp(T_h_in, P_h)
  step_2: h_h_out, s_h_out = CoolProp(T_h_out, P_h)
  step_3: Q = m_h · (h_h_in - h_h_out)
  step_4: h_c_out = h_c_in + Q/m_c
  step_5: T_c_out, s_c_out = CoolProp(h=h_c_out, P_c)
  step_6: S_gen = m_h·(s_h_out - s_h_in) + m_c·(s_c_out - s_c_in)
  step_7: X_destroyed = T₀ · S_gen
  step_8: η_II = (m_c·Δψ_cold) / (m_h·Δψ_hot)
```

---

## 6. Scoring System

### Step-Level Scoring (Partial Credit)

Unlike Tier 1 (binary correct/incorrect per property), Tier 2 awards partial credit:

```
Question score = Σ(step_weight × step_correct) / Σ(step_weight)
```

### Weight Distribution by Depth

| Depth | Step Category | Weight | Rationale |
|-------|--------------|--------|-----------|
| A | Property lookups (h₁, s₁, h₂, s₂) | 0.3 | Foundation — already tested in Tier 1 |
| A | Energy balance (w, q) | 0.3 | Core first-law |
| B | Entropy generation (s_gen) | 0.2 | Second-law step |
| C | Exergy destruction (x_dest) | 0.1 | Builds on s_gen (just T₀ · s_gen) |
| C | Second-law efficiency (η_II) | 0.1 | Most advanced, depends on all prior |

### Tolerance

Same as Tier 1 base:
- Numerical: ±2% relative OR ±0.5 absolute (whichever more lenient)
- Quality (x): abs_tolerance = 0.03
- Phase: exact match

### Error Propagation Consideration

**Key design decision:** If a model gets h₁ wrong but then correctly applies s_gen = s₂ - s₁ with its (wrong) s values, does it get credit for the entropy step?

**Proposed approach: Score against ground truth at each step.**
- Rationale: We're testing if the model can produce correct final numbers. Error propagation is a real concern, but "correct methodology with wrong inputs" is already captured by the step weights — getting h₁ right is weighted separately from getting s_gen right.
- Alternative: "Methodology scoring" — check if the formula is correct regardless of numerical inputs. But this requires parsing methodology from prose, which is extremely fragile.
- **Decision: Ground truth at each step. Simpler, more objective, reproducible.**

---

## 7. Working Fluids

### Primary: Water/Steam (H₂O)
- Same as Tier 1, enables direct comparison
- Covers subcooled, saturated, superheated, supercritical
- ~60% of questions

### Secondary: R-134a
- Standard refrigerant, different property behavior than water
- Used in: compressor, heat exchanger (liquid-liquid), boiler (as comparison fluid)
- All R-134a questions in liquid or superheated vapor region (no two-phase)
- ~25% of questions

### Tertiary: Ideal Gas (Air)
- Simplified property model: Δh = c_p·ΔT, Δs = c_p·ln(T₂/T₁) - R·ln(P₂/P₁)
- Tests whether models can switch between real substance and ideal gas models
- Compressors, turbines, nozzles
- ~15% of questions

### CoolProp Fluid Strings
```python
"Water"    # IAPWS-IF97
"R134a"    # Tillner-Roth & Baehr
"Air"      # Lemmon et al. (real gas) — but questions will use ideal gas model
```

For ideal gas questions, ground truth computed analytically with:
- c_p = 1.005 kJ/kg·K (air at ~300 K)
- R = 0.287 kJ/kg·K
- k = 1.4

---

## 8. Dead State Convention

All exergy (Level C) questions use:
- **Standard (always):** T₀ = 25°C (298.15 K), P₀ = 0.1 MPa

Dead state is always explicitly stated in the question. Keeping T₀ constant across all questions eliminates a variable that doesn't test thermodynamic reasoning — it only tests whether the model plugs in the right number.

Exergy of a flow stream:
```
ψ = (h - h₀) - T₀(s - s₀) + V²/2 + gz
```
Kinetic and potential energy terms neglected unless explicitly stated (nozzle questions include KE).

---

## 9. Expected Answer Format

### Structured Output Request

Questions will explicitly request structured output:

```
Present your final answers in the following format:
h_1: [value] kJ/kg
s_1: [value] kJ/kg·K
h_2s: [value] kJ/kg
h_2: [value] kJ/kg
w_out: [value] kJ/kg
s_gen: [value] kJ/kg·K
x_destroyed: [value] kJ/kg
eta_II: [value]
```

This matches Tier 1's approach and feeds directly into the LLM extractor.

### LLM Extractor Adaptation

The Sonnet 4.6 extractor will need a Tier 2–specific prompt that:
1. Knows the step structure (which variables to extract)
2. Handles intermediate vs final answers
3. Ignores "checking" or "verification" calculations
4. Extracts from multi-step reasoning chains

---

## 10. Question ID Convention

```
T2-{COMPONENT}-{DEPTH}{FLUID}-{NUMBER}

Components: TRB (turbine), CMP (compressor), PMP (pump),
            HX (heat exchanger), BLR (boiler), MIX (mixer),
            NOZ (nozzle)

Depth: A, B, C

Fluid: W (water), R (R-134a), A (air/ideal gas)

Examples:
  T2-TRB-CW-001  → Turbine, Depth C, Water, question 1
  T2-BLR-CW-005  → Boiler, Depth C, Water, question 5
  T2-NOZ-AA-003  → Nozzle, Depth A, Air, question 3
  T2-HX-BR-002   → Heat Exchanger, Depth B, R-134a, question 2
```

---

## 11. Implementation Plan

### Phase 2a — Taxonomy + Templates (~2 days)

1. Create `taxonomy/tier2_components.yaml` with:
   - 7 component definitions
   - Parameter ranges per component (T, P, η, ṁ ranges)
   - Depth-level step definitions
   - Scoring weights

2. Create `generation/templates/tier2_components.py` with:
   - Parameterized templates for each component × depth combination
   - ~20 templates total (some components share depth patterns)

### Phase 2b — State Generation + Ground Truth (~2 days)

3. Create `generation/state_generator.py`:
   - Anchor-derive logic per component type
   - CoolProp validation (all states physically realizable)
   - Constraint checking (η_s ∈ valid range, T₂ > 0, no negative quality, etc.)

4. Extend `generation/ground_truth.py`:
   - Multi-step ground truth computation
   - Step-by-step intermediate values stored
   - Error propagation tracking (which steps depend on which)

### Phase 2c — Scoring + Extraction (~1 day)

5. Extend `evaluation/scorer.py`:
   - Step-level scoring with weights
   - Partial credit calculation
   - Per-component and per-depth breakdown in summary

6. Extend `evaluation/llm_extractor.py`:
   - Tier 2 extraction prompt (multi-variable)
   - Step-aware extraction

### Phase 2d — Generation + Validation (~1 day)

7. Generate ~100 questions → `data/tier2_components/questions.jsonl`
8. Manual spot-check: 10 questions solved by hand against CoolProp
9. Run on 2 models (Opus + Gemini) as validation pass

### Phase 2e — Full Evaluation (~2 days)

10. Run all 5 frontier models + EntropyHunter v0.4
11. Multi-run if budget allows (3 runs × 5 models × 100 questions)
12. Analysis: per-component, per-depth, per-fluid breakdown
13. Update HuggingFace dataset, README, leaderboard

---

## 12. Key Design Decisions To Resolve

| # | Question | Options | Decision |
|---|----------|---------|----------|
| 1 | Step scoring: ground truth vs methodology? | Ground truth at each step / Parse methodology | **Ground truth** — objective, reproducible |
| 2 | Error propagation credit? | No credit if upstream wrong / Credit if formula correct | **No credit** — score each step independently vs ground truth |
| 3 | Which components have Level C? | All / Selected | **All 7 have A+B+C.** Boiler replaces throttle — now every component has a clear η_II definition. |
| 4 | Include mass flow rate problems? | Specific (per kg) only / Include ṁ | **Both.** Some "per unit mass" (kJ/kg), some with ṁ (kW). Tests unit handling. |
| 5 | Ideal gas: analytical or CoolProp? | Analytical (c_p, R) / CoolProp real gas | **Analytical** — models should use ideal gas model when told "assume ideal gas" |
| 6 | Template count target | 15-20 / 25-30 | **Balanced ~25 templates** generating ~100 questions (~4 parameter sets each) |
| 7 | R-134a scope | Refrigeration only / Broader | **Broader** — compressor, HX (liquid-liquid), and where thermodynamically appropriate |
| 8 | Nozzle/diffuser: include KE in exergy? | Yes / No | **Yes for nozzle only** — ψ includes V²/2, tests if model handles it |
| 9 | Dead state | Standard only / Vary T₀ | **Always 25°C / 0.1 MPa** — reduces noise, focuses on analysis skill |
| 10 | Unit system | SI only / Include BTU | **SI only** — clean, consistent |
| 11 | HX phase change | Include condenser/evaporator / Liquid only | **Liquid-liquid only** — sensible heat, no phase change in HX |
| 12 | Throttle vs Boiler | Keep throttle / Replace with boiler | **Boiler** — massive exergy destruction, clear η_II via Carnot factor, better discriminator |

---

## 13. Relationship to EntropyHunter

### Direct Mapping

| EntropyHunter Category | Tier 2 Coverage |
|----------------------|-----------------|
| SPECO (component exergy) | Level C — η_II calculation (all 7 components) |
| Avoidable/Unavoidable | NOT in Tier 2 (requires ideal + real comparison → Tier 3) |
| Hotspot Detection | Implicit — which component has highest X_destroyed |
| Entropy Generation | Level B — s_gen calculation |
| Exergy of Heat | Level C Boiler — Carnot factor (1 - T₀/T_source) |
| Advanced Exergy | NOT in Tier 2 (endogenous/exogenous → Tier 4) |

### EntropyHunter v0.4 Expected Performance

Based on v0.4's 92.7% on its own test set:
- Level A (property lookups + energy): ~85-90% (Tier 1 baseline)
- Level B (entropy): ~90-95% (its specialty)
- Level C (exergy): ~85-90% (its specialty, but multi-step assembly harder)

**Hypothesis:** EntropyHunter should outperform frontier models on Level B+C despite being 8B parameters, because it's specifically fine-tuned for this. If it doesn't, the Tier 2 design needs adjustment.

---

## 14. Remaining Open Questions

Most design decisions are now resolved. Remaining items:

1. **Boiler T_source range:** Combustion gases typically 800–2000 K. Should we include nuclear (600 K) or solar (400–800 K) heat sources for variety? Lower T_source = higher exergy destruction = harder problem.

2. **HX fluid combinations:** Water-Water and Water-R134a(liquid). Any other combinations? Or keep it simple with just these two?

3. **Boiler: constant pressure assumption?** Real boilers have pressure drop, but Çengel textbooks assume constant P. Should we include 1-2 questions with ΔP to test if models handle it?

4. **EntropyHunter evaluation:** Run EntropyHunter v0.4 on Tier 2 before or after frontier models? Running it first could help calibrate question difficulty.
