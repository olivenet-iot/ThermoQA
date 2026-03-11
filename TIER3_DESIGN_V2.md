# ThermoQA — Tier 3 Design V2: Hardened Cycle Analysis
## Updated 11 March 2026

---

## Why V2

V1 Tier 3 evaluation revealed that frontier models score 93-96% — too easy for a benchmark meant to last 5+ years. Root causes:

1. **30/95 ideal cycle questions = free %100** (32% of benchmark is trivial)
2. **Air/Brayton with constant cp = no table lookup challenge** (pure formula following)
3. **R-134a absolute h/s removed from scoring** (eliminated the biggest penalty source)
4. **Weight structure inflated by state properties** (h1, s1, etc. = easy, high count, low weight but many)
5. **No cross-cycle or multi-fluid problems** (no Katman 4 future-proofing)

V1 scores (LLM re-extracted):
- Opus: 96.2%, Gemini: 95.4%, DeepSeek: 93.6%, GPT-5.4: 93.5%, MiniMax: 56.4%

Target: frontier models at 80-90%, with headroom for future models. Ceiling should be unreachable for years.

---

## 4-Layer Difficulty Architecture

The benchmark is designed with 4 difficulty layers. As models improve over years, discrimination shifts upward.

### Layer 1 — Baseline (2026: trivial, always ~100%)
- Ideal Rankine Depth A, Ideal Brayton Depth A
- Purpose: sanity check, pipeline validation
- **5 questions** (was 30 in V1)

### Layer 2 — Comfortable (2026: 90-100%, 2028: ~100%)
- Actual Rankine/Brayton with constant cp, Water properties
- Depth A and B
- **~25 questions**

### Layer 3 — Challenging (2026: 70-90%, 2028: 85-95%)
- Variable cp Air (air-standard analysis), R-134a with specified reference state
- Reheat/Regen Depth C, VCR Depth C with full absolute properties
- **~35 questions**

### Layer 4 — Expert (2026: 50-75%, 2030: maybe 85%)
- Combined cycle (Brayton topping + Rankine bottoming)
- Cross-cycle energy balance, dual-fluid, 8+ state points
- Consistency scoring (energy/entropy closure check)
- **~10-15 questions**

---

## 6 Changes from V1

### Change 1: Ideal Cycles 30 → 5

**Remove:** 25 ideal cycle questions (RNK-I and BRY-I)
**Keep:** 5 for sanity check:
- T3-RNK-I-WA-A-001 (Rankine ideal Depth A)
- T3-RNK-I-WA-C-001 (Rankine ideal Depth C — tests exergy on ideal cycle)
- T3-BRY-I-AR-A-001 (Brayton ideal Depth A)
- T3-BRY-I-AR-B-001 (Brayton ideal Depth B — tests s_gen=0 knowledge)
- T3-BRY-I-AR-C-001 (Brayton ideal Depth C)

Rationale: Ideal cycles are pipeline validation, not model discrimination. Every frontier model gets 100%. Keeping 5 (one per meaningful depth) ensures no regression.

### Change 2: Variable Specific Heats Air

**New cycle variants:**
- BRY-A-VAR: Actual Brayton with variable cp (CoolProp "Air")
- BRY-RG-VAR: Regenerative Brayton with variable cp

**Implementation:**
```python
# Constant cp (cold-air-standard) — existing
T2s = T1 * r_p ** ((k-1)/k)
h2s = cp * T2s

# Variable cp (air-standard) — NEW, via CoolProp
h1 = CP.PropsSI("H", "T", T1, "P", P1_Pa, "Air") / 1000  # kJ/kg
s1 = CP.PropsSI("S", "T", T1, "P", P1_Pa, "Air") / 1000  # kJ/(kg·K)
# Isentropic: find T2s such that s(T2s, P2) = s1
h2s = CP.PropsSI("H", "S", s1*1000, "P", P2_Pa, "Air") / 1000
```

**Question text distinction:**
- Constant cp: *"Assume cold-air-standard assumptions with constant specific heats: cp = 1.005 kJ/(kg·K), k = 1.4."*
- Variable cp: *"Use air-standard assumptions with variable specific heats (temperature-dependent properties)."*

**cp variation magnitude:**
| T (K) | cp (kJ/(kg·K)) | Δ from 1.005 |
|-------|----------------|-------------|
| 300 | 1.005 | 0% |
| 500 | 1.030 | +2.5% |
| 800 | 1.099 | +9.4% |
| 1000 | 1.141 | +13.5% |
| 1300 | 1.197 | +19.1% |
| 1500 | 1.210 | +20.4% |

Impact on cycle: variable cp gives ~3-5pp lower η_th than constant cp. This difference is the discriminator — models that use constant cp formulas when variable is specified will be penalized.

**Question count:** 10 questions (5 BRY-A-VAR, 5 BRY-RG-VAR, spread across depths A/B/C)

**Parameter ranges:** Same as existing Brayton, but ground truth computed via CoolProp "Air" instead of constant cp.

### Change 3: R-134a Reference State — Specify + Restore Absolute Scoring

**Add to ALL VCR question text:**
> *"Use the IIR reference state for R-134a properties: h = 200.0 kJ/kg and s = 1.0000 kJ/(kg·K) for saturated liquid at 0°C."*

This is the standard used by CoolProp, NIST Webbook, and most European engineering references. Models that use ASHRAE reference will need to convert or use the correct one.

**Restore scored steps in VCR templates:**
- Depth A: restore h1, h2s, h2, h3, h4 (5 steps re-added)
- Depth B: restore s1, s2, s3, s4 (4 steps re-added)
- Depth C: restore ef1, ef2, ef3, ef4 (4 steps re-added)

**Updated VCR step counts:**
- Depth A: 7 → 12 (back to V1 original)
- Depth B: 12 → 21
- Depth C: 19 → 32

This is now fair because the question specifies which reference state to use. If a model still uses ASHRAE, that's a genuine failure to follow instructions — exactly what we want to test.

### Change 4: Weight Rebalancing

**Old weights:**
- State properties (h, s, ef): weight 1
- Component quantities (w_pump, q_in, s_gen): weight 2
- Cycle results (eta_th, COP, eta_II): weight 3
- VCR x4: weight 4

**New weights — emphasize engineering outcomes:**
- State properties (h, s): weight 1 (unchanged — building blocks)
- Flow exergy (ef): weight 2 (requires dead state + correct h,s → harder)
- Component quantities (w_pump, q_in, s_gen, x_dest): weight 3 (was 2)
- Cycle results (eta_th, COP, w_net, s_gen_total, x_dest_total): weight 5 (was 3)
- Second-law efficiency (eta_II): weight 6 (was 3 — ultimate integration test)
- VCR x4: weight 4 (unchanged)
- Consistency bonus: weight 3 (new — see Change 6)

**Impact:** A model getting all state properties right but eta_th wrong loses much more. Engineering results matter more than intermediate values.

### Change 5: Combined Cycle (NEW cycle type)

**CCGT: Combined Cycle Gas Turbine**
```
GAS SIDE (Air, variable cp):
  State 1 → Compressor → State 2
  State 2 → Combustion Chamber → State 3
  State 3 → Gas Turbine → State 4
  State 4 → HRSG hot side → State 5 (exhaust to atmosphere)

STEAM SIDE (Water):
  State 6 → Pump → State 7
  State 7 → HRSG cold side → State 8 (superheated steam)
  State 8 → Steam Turbine → State 9
  State 9 → Condenser → State 6
```

**9 state points** (5 Air + 4 Water), **2 fluids**, cross-cycle energy coupling.

**Key coupling equation (HRSG energy balance):**
ṁ_air × (h4 - h5) = ṁ_steam × (h8 - h7)

This means models must:
1. Solve Air Brayton topping cycle (variable cp)
2. Use exhaust heat to determine steam cycle conditions
3. Handle two different fluids with different property methods
4. Compute combined η_th = (W_gas + W_steam - W_comp - W_pump) / Q_combustion

**Anchors:**
- Air: T1, P1, r_p, T3 (TIT), η_comp, η_gas_turb, ṁ_air
- Steam: P_cond, P_steam, T8 (limited by T4 - pinch point), η_pump, η_steam_turb
- HRSG: T5 (stack temperature, ≥ 100°C), pinch point ΔT ≥ 10°C
- ṁ_steam derived from HRSG energy balance

**Depths:**
- A: All state properties + component work/heat + η_combined + ṁ_steam
- B: + entropy generation per component (7 components) + s_gen_total
- C: + exergy destruction per component + η_II_combined

**Parameters:**
| Parameter | Range | Unit | Notes |
|-----------|-------|------|-------|
| T1 | 290-310 | K | Air inlet |
| P1 | 95-105 | kPa | Atmospheric |
| r_p | 10-18 | — | Gas turbine pressure ratio |
| T3 | 1200-1500 | K | Turbine inlet (TIT) |
| η_comp | 0.82-0.88 | — | |
| η_gas_turb | 0.85-0.92 | — | |
| P_cond | 10-30 | kPa | Steam condenser |
| P_steam | 4-12 | MPa | Steam pressure |
| T8_superheat | 30-100 | °C above T_sat | Steam turbine inlet superheat |
| η_pump | 0.80-0.90 | — | |
| η_steam_turb | 0.82-0.90 | — | |
| T5_stack | 100-150 | °C | Exhaust stack temperature |
| ṁ_air | 50-200 | kg/s | |

**Validation:**
- HRSG energy balance closure
- T5 > T7 + 10°C (pinch point)
- T8 < T4 - 20°C (realistic heat transfer)
- ṁ_steam > 0 (enough exhaust heat)
- Combined η_th typically 50-60% (realistic)

**Expected step counts:**
- Depth A: ~20 steps (9 state h's + ṁ_steam + component work/heat + η_combined)
- Depth B: ~30 steps (+ 9 s's + 7 s_gen + s_gen_total)
- Depth C: ~42 steps (+ 9 ef's + 7 x_dest + x_dest_total + η_II)

**Question count:** 12 questions (4 per depth)

**Difficulty prediction:** Frontier models 50-70%. This is the benchmark's ceiling — should remain discriminating for 5+ years.

### Change 6: Consistency Scoring (New Metric)

**Add consistency check steps to Depth B and C questions:**

For power cycles:
- `energy_balance_error`: |q_in - w_net - q_out| / q_in — should be < 0.001
- `entropy_check`: s_gen_total ≥ 0 — must be true

For VCR:
- `energy_balance_error`: |q_H - w_comp - q_L| / q_H — should be < 0.001

For combined cycle:
- `hrsg_balance_error`: |ṁ_air(h4-h5) - ṁ_steam(h8-h7)| / ṁ_air(h4-h5)
- `energy_balance_error_gas`: gas side closure
- `energy_balance_error_steam`: steam side closure

**Scoring:**
- Pass if error < 0.01 (1%) — model's own numbers are self-consistent
- This is NOT about matching ground truth — it's about internal consistency
- Weight: 3

**Implementation:** After extracting all step values, compute the balance from the MODEL's own reported values. This tests whether the model checks its own work.

**Key insight:** A model can get individual steps wrong but still be internally consistent (systematic error). Or get steps "close to right" but be inconsistent (random errors). Consistency scoring captures this second dimension.

---

## Revised Question Distribution

| Cycle | Layer | Fluid | cp | Depth A | Depth B | Depth C | Total |
|-------|-------|-------|----|---------|---------|---------|-------|
| RNK-I (Ideal Rankine) | 1 | Water | — | 1 | — | 1 | 2 |
| BRY-I (Ideal Brayton) | 1 | Air | const | 1 | 1 | 1 | 3 |
| RNK-A (Actual Rankine) | 2 | Water | — | 5 | 5 | 5 | 15 |
| BRY-A (Actual Brayton, const cp) | 2 | Air | const | 3 | 3 | 3 | 9 |
| RNK-RH (Reheat Rankine) | 3 | Water | — | 4 | 3 | 3 | 10 |
| BRY-A-VAR (Actual Brayton, var cp) | 3 | Air | **var** | 2 | 2 | 2 | 6 |
| BRY-RG (Regen Brayton, const cp) | 2-3 | Air | const | 2 | 2 | 2 | 6 |
| BRY-RG-VAR (Regen Brayton, var cp) | 3 | Air | **var** | 2 | 1 | 1 | 4 |
| VCR-A (Actual VCR) | 3 | R-134a | — | 5 | 5 | 5 | 15 |
| **CCGT (Combined Cycle)** | **4** | **Air+Water** | **var** | **4** | **4** | **4** | **12** |
| | | | | **29** | **26** | **27** | **~82** |

Notes:
- BRY-A const cp reduced from 15→9 (moved 6 to BRY-A-VAR)
- BRY-RG const cp reduced from 10→6 (moved 4 to BRY-RG-VAR)
- Ideal reduced 30→5
- VCR stays at 15 (now harder with restored absolute properties)
- CCGT adds 12 new questions
- **Total: ~82 questions** (was 95, but much harder per question)

### Layer Distribution
- Layer 1 (baseline): 5 questions (6%)
- Layer 2 (comfortable): ~24 questions (29%)
- Layer 3 (challenging): ~41 questions (50%)
- Layer 4 (expert): 12 questions (15%)

Over 65% of questions are Layer 3-4. This is a hard benchmark.

---

## New Question ID Convention

Same format but with `-VAR` suffix for variable cp:
- `T3-BRY-A-AR-A-001` — constant cp (existing)
- `T3-BRY-AV-AR-A-001` — variable cp (new, "AV" = Actual Variable)
- `T3-BRY-RV-AR-B-001` — regen variable cp ("RV")
- `T3-CCGT-MX-C-001` — combined cycle ("MX" = mixed fluid)

---

## Implementation Plan

### Phase 1: Quick Wins (no new physics)
1. Remove 25 ideal cycle questions from generation
2. Apply weight rebalancing to all existing templates
3. Add IIR reference state text to VCR questions + restore absolute h/s scoring
4. Regenerate questions, re-validate

### Phase 2: Variable cp Air
5. Add CoolProp "Air" backend to cycle_state_generator.py (new functions alongside existing constant cp)
6. Create BRY-AV and BRY-RV templates
7. Add variable cp samplers
8. Generate + validate variable cp questions

### Phase 3: Combined Cycle
9. Implement `generate_combined_cycle()` in cycle_state_generator.py
10. Create CCGT templates (3 depths)
11. Add CCGT sampler with HRSG coupling validation
12. Generate + validate CCGT questions

### Phase 4: Consistency Scoring
13. Add consistency check computation to scorer
14. Add consistency steps to Depth B and C templates
15. Update extractor for consistency step IDs

### Phase 5: Re-evaluate
16. Re-run all 5 models on new question set
17. Compare V1 vs V2 scores
18. Verify difficulty targets met (frontier 80-90%)
19. Publish updated dataset

---

## Expected V2 Scores (Prediction)

| Model | V1 Score | V2 Predicted | Primary Pain Point |
|-------|----------|-------------|-------------------|
| Opus 4.6 | 96.2% | 82-88% | CCGT coupling, variable cp |
| Gemini 3.1 | 95.4% | 80-86% | R-134a absolute, CCGT |
| GPT-5.4 | 93.5% | 78-85% | Variable cp, VCR absolute |
| DeepSeek-R1 | 93.6% | 75-82% | CCGT, Reheat exergy |
| MiniMax M2.5 | 56.4% | 30-45% | Everything |

Target: Top model ~85%, clear separation between tiers.

---

## Compatibility Notes

- V2 is a breaking change — question IDs and step definitions change
- V1 results stored separately in `results_tier3_v1/` for comparison
- HuggingFace: new config `tier3_cycles_v2` alongside existing `tier3_cycles`
- Paper reports both V1 and V2 with analysis of what changed

---

## Open Questions for Implementation

### Q1: CCGT — single or multiple HRSG configurations?
- Single pressure HRSG (simpler, 4 steam states) — recommended for V2
- Dual pressure HRSG (more realistic, 6+ steam states) — future extension

### Q2: Variable cp Air — CoolProp "Air" or "Air.mix"?
- "Air" is pseudo-pure fluid in CoolProp, should work for our ranges
- Test first: verify CoolProp Air gives reasonable cp(T) values at our P/T ranges

### Q3: Consistency scoring — separate metric or integrated?
- Integrated: consistency steps mixed into regular step list, same weighted scoring
- Separate: report as additional metric alongside main score
- Recommendation: integrated — simplest, consistent with existing pipeline

### Q4: Should variable cp Brayton questions also include T2, T4 as scored steps?
- With constant cp: T2 = h2/cp, trivial
- With variable cp: T2 from CoolProp, meaningful
- Recommendation: Yes, include temperatures as scored steps for variable cp (not for constant cp)
