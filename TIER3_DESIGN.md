# ThermoQA — Tier 3 Design Document: Cycle Analysis
## Drafted 10 March 2026

---

## Executive Summary

Tier 3 extends ThermoQA from single-component analysis (Tier 2) to **complete thermodynamic cycle analysis**. The key distinction: models must now track multiple state points across connected components, maintain consistency (mass, energy, entropy balances), and compute cycle-level performance metrics.

**Target:** ~105 questions, 7 cycle types × 3 depths × ~5 questions each.

**What Tier 3 tests that Tier 1–2 don't:**
1. Multi-state-point consistency (6+ states with linked properties)
2. Cycle-level energy/entropy/exergy closure
3. Ideal vs actual comparison (isentropic efficiencies)
4. COP calculation (VCR — fundamentally different from η_th)
5. Phase change across cycle (condenser/evaporator back-work)
6. Throttle valve (isenthalpic, entropy-generating, within VCR context)

---

## Cycle Taxonomy

### 7 Cycle Types

```
POWER CYCLES (output: work)
├── RNK-I   Ideal Rankine Cycle ............. Water, 4 states
├── RNK-A   Actual Rankine Cycle ............ Water, 4 states (+ideal)
├── RNK-RH  Reheat Rankine Cycle ............ Water, 6 states
├── BRY-I   Ideal Brayton Cycle ............. Air, 4 states
├── BRY-A   Actual Brayton Cycle ............ Air, 4 states (+ideal)
└── BRY-RG  Regenerative Brayton Cycle ...... Air, 6 states

REFRIGERATION CYCLES (output: cooling)
└── VCR-A   Actual Vapor Compression ........ R-134a, 4 states (+ideal)
```

### Fluid Distribution
- **Water:** RNK-I, RNK-A, RNK-RH (power cycles with phase change)
- **Air (ideal gas):** BRY-I, BRY-A, BRY-RG (gas turbine cycles)
- **R-134a:** VCR-A (refrigeration — hardest due to Tier 2 findings)

### Depth Levels
- **A:** Energy balance → cycle efficiency (η_th or COP_R)
- **B:** + Entropy generation per component + total s_gen
- **C:** + Exergy destruction per component + second-law efficiency η_II

---

## State Numbering Convention

### Rankine (Simple): 4 states
```
        Q_in (boiler)
         ┌──────┐
    2 ───┤      ├─── 3
    │    └──────┘    │
  Pump              Turbine → W_turb
    │    ┌──────┐    │
    1 ───┤      ├─── 4
         └──────┘
        Q_out (condenser)
```
- State 1: Condenser exit / Pump inlet (saturated liquid at P_low)
- State 2: Pump exit / Boiler inlet (compressed liquid at P_high)
- State 3: Boiler exit / Turbine inlet (superheated vapor at P_high)
- State 4: Turbine exit / Condenser inlet (wet mixture or superheated at P_low)

For **actual** cycles: 2s, 4s = isentropic states; 2, 4 = actual states.

### Reheat Rankine: 6 states
```
        Q_in (boiler)    Q_reheat
         ┌──────┐        ┌──────┐
    2 ───┤      ├─── 3   4 ───┤      ├─── 5
    │    └──────┘    │   │    └──────┘    │
  Pump              HPT  │              LPT → W_turb
    │    ┌──────────────────────────────┐ │
    1 ───┤         condenser            ├─ 6
         └──────────────────────────────┘
```
- State 1: Condenser exit / Pump inlet (sat liquid at P_low)
- State 2: Pump exit / Boiler inlet (P_high)
- State 3: Boiler exit / HPT inlet (superheated at P_high)
- State 4: HPT exit / Reheat inlet (P_intermediate)
- State 5: Reheat exit / LPT inlet (superheated at P_intermediate)
- State 6: LPT exit / Condenser inlet (P_low)

### Brayton (Simple): 4 states
```
        Q_in (combustion chamber)
         ┌──────┐
    2 ───┤      ├─── 3
    │    └──────┘    │
  Comp ← W_comp    Turb → W_turb
    │    ┌──────┐    │
    1 ───┤      ├─── 4
         └──────┘
        Q_out (heat rejection)
```
- State 1: Compressor inlet (ambient air: T1, P1)
- State 2: Compressor exit / CC inlet (P2 = r_p × P1)
- State 3: CC exit / Turbine inlet (T3_max, P3 ≈ P2)
- State 4: Turbine exit (P4 ≈ P1)

### Regenerative Brayton: 6 states
```
    2 ──→ Regen(cold) ──→ 3 ──→ CC ──→ 4
    │                                   │
  Comp                                Turb
    │                                   │
    1                    6 ←── Regen(hot) ←── 5
```
- State 1: Compressor inlet (T1, P1)
- State 2: Compressor exit (P2)
- State 3: Regenerator cold exit / CC inlet (preheated)
- State 4: CC exit / Turbine inlet (T4_max, P4 ≈ P2)
- State 5: Turbine exit (P5 ≈ P1)
- State 6: Regenerator hot exit (cooled exhaust)

Regenerator effectiveness: ε = (T3 - T2) / (T5 - T2)

### VCR: 4 states
```
        Q_H (condenser)
         ┌──────┐
    2 ───┤      ├─── 3
    │    └──────┘    │
  Comp ← W_comp   Throttle (isenthalpic)
    │    ┌──────┐    │
    1 ───┤      ├─── 4
         └──────┘
        Q_L (evaporator)
```
- State 1: Evaporator exit / Compressor inlet (saturated vapor at P_evap)
- State 2: Compressor exit / Condenser inlet (superheated at P_cond)
- State 3: Condenser exit / Throttle inlet (saturated liquid at P_cond)
- State 4: Throttle exit / Evaporator inlet (wet mixture at P_evap, h4 = h3)

---

## Anchor-Derive State Generation

### Philosophy (from Tier 2)
Generate physically valid state points **forward**, never reverse-engineer. Every state must be derivable from anchor conditions + physics.

### Rankine Ideal (RNK-I)

**Given (anchors):**
- P_cond (condenser pressure, kPa) → determines T_sat, h_f, s_f
- P_boiler (boiler pressure, MPa)
- T3 (turbine inlet temperature, °C — must be superheated)
- ṁ (mass flow rate, kg/s)

**Derive sequence:**
```
State 1: sat liquid at P_cond → h1 = h_f, s1 = s_f, v1
State 2s: s2s = s1, P_boiler → h2s ≈ h1 + v1×(P_boiler - P_cond)  [compressed liquid approx]
State 2: h2 = h2s (ideal pump)
State 3: (T3, P_boiler) → h3, s3 from CoolProp
State 4s: s4s = s3, P_cond → h4s (may be wet: x4s = (s3 - s_f)/(s_g - s_f), h4s = h_f + x4s×h_fg)
State 4: h4 = h4s (ideal turbine)
```

**Validation checks:**
- T3 > T_sat(P_boiler) + 20°C (ensure well superheated)
- x4 > 0.85 (avoid excessive wetness at turbine exit — realistic operation)
- h3 > h2 (boiler adds energy)
- h3 > h4 (turbine extracts energy)

### Rankine Actual (RNK-A)

**Additional anchors:**
- η_pump (0.75–0.90)
- η_turb (0.80–0.92)

**Modified derive:**
```
State 2: h2 = h1 + (h2s - h1) / η_pump
State 4: h4 = h3 - η_turb × (h3 - h4s)
```

**Validation:** Same as ideal + h2_actual > h2s (pump irreversibility) + h4_actual > h4s (less expansion)

### Reheat Rankine (RNK-RH)

**Anchors:**
- P_cond (kPa), P_boiler (MPa), P_reheat (MPa, between P_cond and P_boiler)
- T3 (HPT inlet °C), T5 (LPT inlet °C — reheat temperature)
- η_pump, η_HPT, η_LPT
- ṁ (kg/s)

**Derive sequence:**
```
State 1: sat liquid at P_cond → h1, s1
State 2s: s2s = s1, P_boiler → h2s
State 2: h2 = h1 + (h2s - h1) / η_pump
State 3: (T3, P_boiler) → h3, s3
State 4s: s4s = s3, P_reheat → h4s
State 4: h4 = h3 - η_HPT × (h3 - h4s)
State 5: (T5, P_reheat) → h5, s5
State 6s: s6s = s5, P_cond → h6s
State 6: h6 = h5 - η_LPT × (h5 - h6s)
```

**Validation:**
- P_cond < P_reheat < P_boiler (pressure ordering)
- T5 > T_sat(P_reheat) + 20°C (superheated after reheat)
- x6 > 0.85 (LPT exit quality check — if wet)
- T3, T5 in realistic range (400–600°C for modern steam)

### Brayton Ideal (BRY-I)

**Given (anchors):**
- T1 (compressor inlet, K — typically 290–310 K)
- P1 (atmospheric, typically 100 kPa)
- r_p (pressure ratio, 6–18)
- T3 (turbine inlet, K — 1100–1600 K)
- ṁ (kg/s)

**Air properties (ideal gas):**
- cp = 1.005 kJ/(kg·K), cv = 0.718 kJ/(kg·K)
- k = cp/cv = 1.4, R = 0.287 kJ/(kg·K)

**Derive sequence:**
```
P2 = r_p × P1
State 1: (T1, P1) → h1 = cp×T1, s1 = cp×ln(T1/T_ref) - R×ln(P1/P_ref)
State 2s: T2s = T1 × r_p^((k-1)/k)  → h2s = cp×T2s
State 2: h2 = h2s (ideal compressor) → T2 = T2s
State 3: (T3, P2) → h3 = cp×T3
State 4s: T4s = T3 / r_p^((k-1)/k)  → h4s = cp×T4s
State 4: h4 = h4s (ideal turbine) → T4 = T4s
```

**Validation:**
- T3 > T2 (combustion adds energy)
- T4 > T1 (exhaust hotter than inlet)
- η_th = 1 - 1/r_p^((k-1)/k) > 0 (always true for r_p > 1)

### Brayton Actual (BRY-A)

**Additional anchors:**
- η_comp (0.78–0.88)
- η_turb (0.82–0.92)

**Modified derive:**
```
State 2: h2 = h1 + (h2s - h1) / η_comp → T2 = h2/cp
State 4: h4 = h3 - η_turb × (h3 - h4s) → T4 = h4/cp
```

### Brayton Regenerative (BRY-RG)

**Additional anchors:**
- ε_regen (regenerator effectiveness, 0.70–0.90)

**Modified derive (after actual compressor/turbine):**
```
State 2: actual compressor exit (T2, h2)
State 5: actual turbine exit (T5, h5)
State 3: T3 = T2 + ε_regen × (T5 - T2) → h3 = cp×T3
State 6: T6 = T5 - (T3 - T2)  [energy balance on regen] → h6 = cp×T6
```

**Validation:**
- T3 < T5 (cold side can't exceed hot side)
- T6 > T2 (hot side can't go below cold inlet)
- T6 > T1 (exhaust still hotter than ambient — waste heat)

### VCR Actual (VCR-A)

**Given (anchors):**
- T_evap (evaporator temperature, °C, -25 to 5°C)
- T_cond (condenser temperature, °C, 30 to 50°C)
- η_comp (0.75–0.88)
- ṁ (kg/s) or Q̇_L (cooling capacity, kW)

**Derive sequence:**
```
P_evap = P_sat(T_evap) for R-134a → CoolProp
P_cond = P_sat(T_cond) for R-134a → CoolProp

State 1: sat vapor at T_evap → h1, s1 (CoolProp: Q=1)
State 2s: (s2s = s1, P_cond) → h2s (CoolProp: superheated R-134a)
State 2: h2 = h1 + (h2s - h1) / η_comp
State 3: sat liquid at T_cond → h3, s3 (CoolProp: Q=0)
State 4: h4 = h3 (isenthalpic throttle), P4 = P_evap
         x4 = (h4 - h_f@P_evap) / (h_fg@P_evap)
         s4 = s_f + x4 × (s_g - s_f) at P_evap
```

**Validation:**
- T_cond > T_evap + 20°C (realistic temperature lift)
- h2 > h1 (compressor adds energy)
- h2s from CoolProp valid (not beyond R-134a critical point: T_c = 101.06°C, P_c = 4.059 MPa)
- x4 ∈ (0, 1) — must be wet mixture after throttle
- P_cond < 3.5 MPa (stay within standard table range — avoid Tier 2's 1.98 MPa problem unless intentional)

**COP calculation:**
- COP_R = Q̇_L / Ẇ_comp = (h1 - h4) / (h2 - h1)
- COP_Carnot = T_L / (T_H - T_L) [in Kelvin]

---

## Depth Definitions

### Depth A — Energy Analysis

**Power cycles (Rankine, Brayton):**

| Step ID | Description | Weight | Formula |
|---------|-------------|--------|---------|
| h1…hN | Enthalpy at each state point | 1 | CoolProp / ideal gas |
| w_pump | Specific pump work | 2 | h2 - h1 |
| w_comp | Specific compressor work | 2 | h2 - h1 |
| q_in | Specific heat input | 2 | h3 - h2 (or h3-h2 + h5-h4 for reheat) |
| w_turb | Specific turbine work | 2 | h3 - h4 (or h3-h4 + h5-h6 for reheat) |
| w_net | Net specific work | 2 | w_turb - w_pump (or w_turb - w_comp) |
| q_out | Heat rejection | 2 | h4 - h1 (or h6 - h1 for reheat) |
| eta_th | Thermal efficiency | 3 | w_net / q_in |
| W_dot_net | Net power output | 2 | ṁ × w_net |
| Q_dot_in | Heat input rate | 2 | ṁ × q_in |

**Refrigeration cycle (VCR):**

| Step ID | Description | Weight | Formula |
|---------|-------------|--------|---------|
| h1…h4 | Enthalpy at each state | 1 | CoolProp |
| x4 | Quality after throttle | 2 | (h4 - h_f) / h_fg |
| w_comp | Specific compressor work | 2 | h2 - h1 |
| q_L | Specific cooling effect | 2 | h1 - h4 |
| q_H | Specific heat rejection | 2 | h2 - h3 |
| COP_R | Coefficient of performance | 3 | q_L / w_comp |
| W_dot_comp | Compressor power | 2 | ṁ × w_comp |
| Q_dot_L | Cooling capacity | 2 | ṁ × q_L |

### Depth B — Entropy Analysis (includes all of A, plus)

| Step ID | Description | Weight | Formula |
|---------|-------------|--------|---------|
| s1…sN | Entropy at each state point | 1 | CoolProp / ideal gas |
| s_gen_pump | Pump entropy generation | 2 | s2 - s1 |
| s_gen_boiler | Boiler entropy gen | 2 | (s3-s2) - q_in/T_source |
| s_gen_turb | Turbine entropy gen | 2 | s4 - s3 (for adiabatic) |
| s_gen_cond | Condenser entropy gen | 2 | (s1-s4) + q_out/T_sink |
| s_gen_total | Total cycle entropy gen | 3 | Σ s_gen_component |

**VCR-specific:**

| Step ID | Description | Weight | Formula |
|---------|-------------|--------|---------|
| s_gen_comp | Compressor entropy gen | 2 | s2 - s1 |
| s_gen_cond | Condenser entropy gen | 2 | (s3-s2) + q_H/T_H |
| s_gen_throttle | Throttle entropy gen | 2 | s4 - s3 |
| s_gen_evap | Evaporator entropy gen | 2 | (s1-s4) - q_L/T_L |
| s_gen_total | Total | 3 | Σ all |

**Note on heat source/sink temperatures:**
- Boiler/CC: T_source given in question (e.g., furnace gas temperature)
- Condenser: T_sink given (e.g., cooling water temperature, or T_cond + ΔT)
- For ideal internal components (pump, compressor, turbine): s_gen = 0 for ideal, s_gen = Δs for actual adiabatic
- External irreversibility (boiler, condenser) requires T_source/T_sink

### Depth C — Exergy Analysis (includes all of B, plus)

| Step ID | Description | Weight | Formula |
|---------|-------------|--------|---------|
| ef1…efN | Specific flow exergy at each state | 1 | (h - h0) - T0×(s - s0) |
| x_dest_pump | Pump exergy destruction | 2 | T0 × s_gen_pump |
| x_dest_boiler | Boiler exergy destruction | 2 | T0 × s_gen_boiler |
| x_dest_turb | Turbine exergy destruction | 2 | T0 × s_gen_turb |
| x_dest_cond | Condenser exergy destruction | 2 | T0 × s_gen_cond |
| x_dest_total | Total exergy destruction | 3 | Σ x_dest_component |
| eta_II | Second-law efficiency | 3 | W_net / X_in (or COP/COP_rev for VCR) |

**Second-law efficiency definitions:**
- Power cycles: η_II = Ẇ_net / Ẋ_in, where Ẋ_in = Q̇_in × (1 - T₀/T_source) [exergy of heat input]
- Alternatively: η_II = Ẇ_net / (Ẋ_fuel) but T_source approach is cleaner for our scope
- VCR: η_II = COP_R / COP_Carnot, where COP_Carnot = T_L / (T_H - T_L) [Kelvin]

---

## Dead State
- T₀ = 25°C (298.15 K), P₀ = 0.1 MPa (same as Tier 2)
- Water: h₀ = CoolProp(T=298.15, P=100000), s₀ = CoolProp(T=298.15, P=100000)
- Air: h₀ = cp × T₀ = 1.005 × 298.15 = 299.64 kJ/kg, s₀ = 0 (reference)
- R-134a: h₀ = CoolProp(T=298.15, P=100000), s₀ = CoolProp(T=298.15, P=100000)

---

## Question ID Convention

Format: `{CYCLE}-{FLUID}-{DEPTH}-{SEQ}`

Examples:
- `RNK-I-WA-A-001` — Ideal Rankine, Water, Depth A, question 1
- `RNK-A-WA-C-003` — Actual Rankine, Water, Depth C, question 3
- `BRY-RG-AR-B-002` — Regenerative Brayton, Air, Depth B, question 2
- `VCR-A-RF-C-001` — Actual VCR, R-134a, Depth C, question 1

Fluid codes: WA = Water, AR = Air, RF = R-134a

---

## Parameter Ranges

### Rankine Cycles (Water)

| Parameter | Range | Unit | Notes |
|-----------|-------|------|-------|
| P_cond | 5–50 | kPa | Subatmospheric (vacuum condenser) |
| P_boiler | 2–15 | MPa | Avoid supercritical (max ~20 MPa) |
| T3 (turbine inlet) | 350–600 | °C | Must be > T_sat(P_boiler) + 20°C |
| T5 (reheat) | 400–600 | °C | For RNK-RH only |
| P_reheat | 0.5–3 | MPa | Between P_cond and P_boiler |
| η_pump | 0.75–0.90 | — | For actual cycles |
| η_turb | 0.80–0.92 | — | For actual cycles |
| ṁ | 5–100 | kg/s | Reasonable plant scale |

### Brayton Cycles (Air)

| Parameter | Range | Unit | Notes |
|-----------|-------|------|-------|
| T1 | 290–310 | K | Ambient temperature |
| P1 | 95–105 | kPa | Near atmospheric |
| r_p | 6–18 | — | Pressure ratio |
| T3 (turbine inlet) | 1100–1600 | K | TIT — metallurgical limit |
| η_comp | 0.78–0.88 | — | For actual cycles |
| η_turb | 0.82–0.92 | — | For actual cycles |
| ε_regen | 0.70–0.90 | — | Regenerator effectiveness |
| ṁ | 10–200 | kg/s | Gas turbine scale |

### VCR Cycle (R-134a)

| Parameter | Range | Unit | Notes |
|-----------|-------|------|-------|
| T_evap | -25 to 5 | °C | Evaporator temperature |
| T_cond | 30–50 | °C | Condenser temperature |
| η_comp | 0.75–0.88 | — | Compressor isentropic efficiency |
| ṁ | 0.01–0.5 | kg/s | Refrigeration scale |

**R-134a pressure constraints:**
- P_evap = P_sat(T_evap): ranges ~132 kPa (−25°C) to ~350 kPa (5°C)
- P_cond = P_sat(T_cond): ranges ~770 kPa (30°C) to ~1318 kPa (50°C)
- Max P_cond ≈ 1.4 MPa — safely within CoolProp range, avoids Tier 2's 1.98 MPa problem
- Critical point: T_c = 101.06°C, P_c = 4.059 MPa — all states well below

### Heat Source/Sink Temperatures (for entropy/exergy analysis)

| Parameter | Range | Cycle | Notes |
|-----------|-------|-------|-------|
| T_source | T3 + 50 to T3 + 200 | K | Rankine boiler: combustion gas temp |
| T_source | T3 + 100 to T3 + 300 | K | Brayton CC: flame temperature |
| T_sink_power | T_cond_sat + 5 to + 15 | K | Rankine/Brayton condenser cooling water |
| T_H_vcr | T_cond - 15 to - 5 | K | VCR: environment temp (must be < T_cond for heat rejection) |
| T_L_vcr | T_evap + 5 to + 10 | K | VCR: cooled space temperature (must be > T_evap for heat absorption) |

---

## Question Count Targets

| Cycle | Depth A | Depth B | Depth C | Total |
|-------|---------|---------|---------|-------|
| RNK-I (Ideal Rankine) | 5 | 5 | 5 | 15 |
| RNK-A (Actual Rankine) | 5 | 5 | 5 | 15 |
| RNK-RH (Reheat Rankine) | 4 | 3 | 3 | 10 |
| BRY-I (Ideal Brayton) | 5 | 5 | 5 | 15 |
| BRY-A (Actual Brayton) | 5 | 5 | 5 | 15 |
| BRY-RG (Regen Brayton) | 4 | 3 | 3 | 10 |
| VCR-A (Actual VCR) | 5 | 5 | 5 | 15 |
| **Total** | **33** | **31** | **31** | **~95** |

Rationale for fewer reheat/regen: these have more steps per question (15-20 at Depth C), so evaluation is more expensive per question. 10 questions still provides statistical signal.

---

## Steps per Cycle × Depth

### RNK-I, Depth A (~10 steps)
h1, h2, h3, h4, w_pump, q_in, w_turb, w_net, eta_th, W_dot_net

### RNK-I, Depth B (~15 steps)
All of A + s1, s2, s3, s4, s_gen_cond (only external — internal all zero for ideal)

### RNK-I, Depth C (~20 steps)
All of B + ef1, ef2, ef3, ef4, x_dest_boiler, x_dest_cond, x_dest_total, eta_II

### RNK-A, Depth A (~12 steps)
h1, h2s, h2, h3, h4s, h4, w_pump, q_in, w_turb, w_net, eta_th, W_dot_net

### RNK-A, Depth C (~25 steps)
All state props (h, s at 4 actual + 2 ideal states) + component work/heat + s_gen per component (pump, boiler, turbine, condenser) + x_dest per component + eta_II

### VCR-A, Depth A (~10 steps)
h1, h2s, h2, h3, h4, x4, w_comp, q_L, q_H, COP_R

### VCR-A, Depth C (~22 steps)
All of A + s at each state + s_gen per component (comp, cond, throttle, evap) + ef at each state + x_dest per component + x_dest_total + COP_Carnot + eta_II

---

## Expected Step Counts

| Cycle | Depth A | Depth B | Depth C |
|-------|---------|---------|---------|
| RNK-I | 10 | 15 | 20 |
| RNK-A | 12 | 18 | 25 |
| RNK-RH | 16 | 22 | 30 |
| BRY-I | 10 | 14 | 18 |
| BRY-A | 12 | 17 | 22 |
| BRY-RG | 16 | 22 | 28 |
| VCR-A | 10 | 16 | 22 |

**Total steps estimate:** ~95 questions × ~16 steps avg ≈ **~1500 steps** (vs 748 in Tier 2)

---

## Scoring Design

### Same tolerance as Tier 1/2
- ±2% relative OR ±0.5 absolute (whichever more lenient)
- Step-level weighted scoring: score = Σ(w_i × passed_i) / Σ(w_i)

### Weight hierarchy (Tier 3 specific)
- **Weight 1:** State properties (h, s, ef at individual points) — building blocks
- **Weight 2:** Component-level quantities (w_pump, q_in, s_gen_turb, x_dest_boiler) — require correct state usage
- **Weight 3:** Cycle-level results (eta_th, COP_R, w_net, s_gen_total, x_dest_total, eta_II) — ultimate integration test
- **Weight 4 (NEW):** Quality after throttle x4 in VCR — critical discriminator from Tier 2

### Cross-check steps (optional — for insight, not scoring)
- Energy balance closure: |Q_in - W_net - Q_out| / Q_in < 0.001
- Entropy check: s_gen_total ≥ 0
- These can be logged for diagnostic but don't affect score

---

## Hypotheses

Based on Tier 1 + Tier 2 findings, predictions for Tier 3:

### H1: VCR will be the hardest cycle
R-134a properties (Tier 2 discriminator) + throttle valve (new for Tier 3) + COP instead of η_th + compressor division formula (Tier 2's hardest component). Predicted: frontier models 50-70%, MiniMax <40%.

### H2: Tier 2 → Tier 3 drop will be larger than Tier 1 → Tier 2
More states to track, consistency requirements, error propagation across cycle. Predicted: 5-10pp drop for frontier models, 15+pp for MiniMax.

### H3: Ideal cycles will be significantly easier than actual cycles
Fewer states (no ideal + actual), no efficiency correction formulas. Predicted: 10-15pp gap between ideal and actual.

### H4: Reheat/Regen will test state management more than thermodynamic skill
The extra states (6 vs 4) test whether models can keep track of which state point goes where. Predicted: models that do well on simple actual cycles may stumble on reheat purely from bookkeeping errors.

### H5: Depth C will again outperform Depth A for frontier models
Same Tier 2 mechanism: more steps = more self-correction opportunity. But the gap may narrow because Depth C in Tier 3 has 25+ steps — diminishing returns on self-correction.

### H6: eta_II computation will be the key discriminator at Depth C
Second-law efficiency requires both correct exergy destruction AND correct exergy input. For VCR: COP_R/COP_Carnot — requires two different COP calculations to be correct. For power cycles: W_net/(Q_in × (1 - T0/T_source)) — requires both W_net and Carnot factor.

---

## Implementation Plan

### Phase 1: Infrastructure (~Day 1)
1. `taxonomy/tier3_cycles.yaml` — cycle definitions, parameter ranges, step IDs + weights
2. `generation/cycle_state_generator.py` — full cycle state generation (builds on state_generator.py)
3. Extend `generation/param_sampler.py` — 7 new cycle samplers
4. Extend `generation/ground_truth.py` — tier3 dispatch

### Phase 2: Templates + Generation (~Day 1-2)
5. `generation/templates/tier3_cycles.py` — 21 CycleTemplate dataclasses (7 cycles × 3 depths)
6. Extend `generation/question_generator.py` — `generate_tier3_questions()`
7. `scripts/generate_tier3.py` — CLI entry point
8. Generate + validate all ~95 questions against CoolProp

### Phase 3: Evaluation Pipeline (~Day 2)
9. `scripts/run_evaluation_tier3.py` — sequential runner (incremental save)
10. `scripts/run_batch_anthropic_tier3.py` — batch evaluation
11. `scripts/run_batch_openai_tier3.py` — batch evaluation
12. Extend `evaluation/extractor.py` — `extract_tier3_properties()`
13. Extend `evaluation/llm_extractor.py` — `extract_tier3()`
14. Extend `evaluation/scorer.py` — `score_tier3_question()`
15. `scripts/reextract_tier3.py` — LLM re-extraction

### Phase 4: Publish
16. Update `scripts/publish_huggingface.py` — add tier3_cycles config
17. Update README with Tier 3 leaderboard + findings
18. Update HANDOFF document

---

## Resolved Decisions

| Question | Decision | Reasoning |
|----------|----------|-----------|
| Q1: Pump work ground truth | **CoolProp exact** | h(s=s1, P=P_high) - h1. ±2% tolerance covers models using compressed liquid approx (v_f×ΔP). Usually <1% difference for water. |
| Q2: Supercritical Rankine | **No — subcritical only** | Supercritical already tested in Tier 1. Tier 3 focuses on cycle-level reasoning, not property lookup edge cases. |
| Q3: Isentropic efficiency convention | **State explicitly in question text** | Avoids ambiguity. Models sometimes confuse compressor (division) vs turbine (multiplication) — Tier 2 finding. |
| Q4: Air specific heats | **Constant cp = 1.005 kJ/(kg·K)** | Consistent with Tier 2. Variable cp requires air tables models don't have memorized. Phase 4 extension with tool use. |
| Q5: VCR R-134a pressure range | **Conservative (T_cond ≤ 50°C)** | P_cond(50°C) ≈ 1.3 MPa — safely within CoolProp and Çengel tables. Avoids Tier 2's 1.98 MPa beyond-table problem. |
| Q6: Question text length | **Standardized template per cycle type** | Longer than Tier 2 but structured. Keep <500 words. Clear numbered state convention. |

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| ~1500 steps to validate | Automated CoolProp validation for all. Spot-check 10% manually. |
| Question text too long → models lose info | Keep question text <500 words. Use clear numbered state convention. |
| Too many steps → extractor fails | Group related steps. Extend LLM extractor prompt with cycle-specific guidance. |
| VCR too hard → no discrimination among frontier | Include mix of easy (Ideal Rankine A) and hard (VCR C). Range matters. |
| Reheat/Regen step count explodes | Cap at 30 steps maximum per question. Merge redundant steps if needed. |
| CoolProp R-134a at unusual states | Pre-validate all R-134a states. Stay well within subcritical range. |

---

## Example Question (RNK-A, Depth A)

> **An actual Rankine cycle** operates with the following conditions:
>
> - Condenser pressure: P₁ = 10 kPa
> - Boiler pressure: P₂ = 8 MPa
> - Turbine inlet temperature: T₃ = 500°C
> - Pump isentropic efficiency: η_pump = 0.85
> - Turbine isentropic efficiency: η_turb = 0.87
> - Mass flow rate: ṁ = 20 kg/s
>
> Determine:
> (a) The specific enthalpy at each state point (h₁, h₂, h₃, h₄) in kJ/kg
> (b) The pump work input (w_pump) and turbine work output (w_turb) in kJ/kg
> (c) The heat input in the boiler (q_in) in kJ/kg
> (d) The net specific work output (w_net) in kJ/kg
> (e) The thermal efficiency (η_th)
> (f) The net power output (Ẇ_net) in kW

---

## Example Question (VCR-A, Depth C)

> **An actual vapor-compression refrigeration cycle** using R-134a operates between:
>
> - Evaporator temperature: T_evap = −10°C
> - Condenser temperature: T_cond = 40°C
> - Compressor isentropic efficiency: η_comp = 0.82
> - Mass flow rate: ṁ = 0.05 kg/s
> - Cooled space temperature: T_L = −5°C
> - Warm environment temperature: T_H = 30°C
> - Dead state: T₀ = 25°C, P₀ = 0.1 MPa
>
> Determine:
> (a) The specific enthalpy and entropy at each state point (h₁, s₁, h₂, s₂, h₃, s₃, h₄, s₄)
> (b) The quality after the throttle valve (x₄)
> (c) The compressor work (w_comp), cooling effect (q_L), and heat rejection (q_H) in kJ/kg
> (d) The COP of the cycle
> (e) The entropy generation in each component (s_gen_comp, s_gen_cond, s_gen_throttle, s_gen_evap) in kJ/(kg·K)
> (f) The specific flow exergy at each state (ef₁, ef₂, ef₃, ef₄) in kJ/kg
> (g) The exergy destruction in each component in kJ/kg
> (h) The total exergy destruction rate (Ẋ_dest_total) in kW
> (i) The second-law efficiency (η_II)

---

## References for Parameter Realism
- Çengel & Boles, Thermodynamics: An Engineering Approach (8th ed.) — Chapters 9, 10, 11
- ExergyLab knowledge base: `~/exergy-lab/knowledge/formulas.md`, `benchmarks.md`, `case_studies.md`
- Moran & Shapiro, Fundamentals of Engineering Thermodynamics
- Typical power plant parameters: η_turb ≈ 0.85-0.90, P_boiler ≈ 3-16 MPa, TIT ≈ 1200-1500 K
