#!/usr/bin/env python3
"""
CoolProp validation script for ThermoQA.

Verifies CoolProp installation by:
1. Computing superheated steam properties at 10 bar, 250°C
2. Comparing saturated steam properties against the EntropyHunter reference table
3. Verifying dead state properties (T₀=25°C, P₀=101.325 kPa)
"""

import CoolProp
from CoolProp.CoolProp import PropsSI


# Reference table from ~/entropy-hunter/taxonomy/fluid_properties.yaml
REFERENCE_TABLE = [
    {"P_bar": 1.0,   "T_sat_C": 99.6,  "h_f": 417.5,  "h_g": 2675, "s_f": 1.303, "s_g": 7.359},
    {"P_bar": 2.0,   "T_sat_C": 120.2, "h_f": 504.7,  "h_g": 2707, "s_f": 1.530, "s_g": 7.127},
    {"P_bar": 4.0,   "T_sat_C": 143.6, "h_f": 604.7,  "h_g": 2738, "s_f": 1.777, "s_g": 6.896},
    {"P_bar": 6.0,   "T_sat_C": 158.8, "h_f": 670.5,  "h_g": 2757, "s_f": 1.931, "s_g": 6.760},
    {"P_bar": 8.0,   "T_sat_C": 170.4, "h_f": 721.1,  "h_g": 2769, "s_f": 2.046, "s_g": 6.663},
    {"P_bar": 10.0,  "T_sat_C": 179.9, "h_f": 762.6,  "h_g": 2778, "s_f": 2.138, "s_g": 6.586},
    {"P_bar": 15.0,  "T_sat_C": 198.3, "h_f": 844.7,  "h_g": 2792, "s_f": 2.315, "s_g": 6.445},
    {"P_bar": 20.0,  "T_sat_C": 212.4, "h_f": 908.6,  "h_g": 2799, "s_f": 2.447, "s_g": 6.340},
    {"P_bar": 30.0,  "T_sat_C": 233.8, "h_f": 1008.3, "h_g": 2803, "s_f": 2.646, "s_g": 6.186},
    {"P_bar": 40.0,  "T_sat_C": 250.4, "h_f": 1087.4, "h_g": 2800, "s_f": 2.797, "s_g": 6.070},
    {"P_bar": 60.0,  "T_sat_C": 275.6, "h_f": 1213.7, "h_g": 2784, "s_f": 3.028, "s_g": 5.890},
    {"P_bar": 80.0,  "T_sat_C": 295.0, "h_f": 1317.1, "h_g": 2758, "s_f": 3.208, "s_g": 5.745},
    {"P_bar": 100.0, "T_sat_C": 311.0, "h_f": 1408.0, "h_g": 2725, "s_f": 3.361, "s_g": 5.615},
]


def pct_diff(computed, reference):
    """Percent difference: (computed - reference) / reference * 100."""
    if reference == 0:
        return 0.0 if computed == 0 else float("inf")
    return (computed - reference) / reference * 100


def validate_superheated():
    """Compute and display superheated steam properties at 10 bar, 250°C."""
    print("=" * 70)
    print("1. SUPERHEATED STEAM: 10 bar (1000 kPa), 250°C")
    print("=" * 70)

    T_K = 250 + 273.15  # K
    P_Pa = 10e5          # Pa (10 bar)

    h = PropsSI("H", "T", T_K, "P", P_Pa, "Water") / 1000   # kJ/kg
    s = PropsSI("S", "T", T_K, "P", P_Pa, "Water") / 1000   # kJ/(kg·K)
    v = 1.0 / PropsSI("D", "T", T_K, "P", P_Pa, "Water")    # m³/kg
    u = PropsSI("U", "T", T_K, "P", P_Pa, "Water") / 1000   # kJ/kg

    # Reference from YAML notes: h ≈ 2943 kJ/kg, s ≈ 6.926 kJ/(kg·K)
    h_ref, s_ref = 2943, 6.926

    print(f"  h = {h:.2f} kJ/kg       (ref ~{h_ref}, diff {pct_diff(h, h_ref):+.2f}%)")
    print(f"  s = {s:.4f} kJ/(kg·K)  (ref ~{s_ref}, diff {pct_diff(s, s_ref):+.2f}%)")
    print(f"  v = {v:.5f} m³/kg")
    print(f"  u = {u:.2f} kJ/kg")
    print()


def validate_saturation_table():
    """Compare CoolProp saturated properties against the reference table."""
    print("=" * 70)
    print("2. SATURATED STEAM TABLE COMPARISON (CoolProp vs Reference)")
    print("=" * 70)

    header = (
        f"{'P':>6s} {'T_sat':>7s} {'T_diff':>7s} "
        f"{'h_f':>8s} {'%diff':>6s} {'h_g':>8s} {'%diff':>6s} "
        f"{'s_f':>7s} {'%diff':>6s} {'s_g':>7s} {'%diff':>6s}"
    )
    units = (
        f"{'bar':>6s} {'°C':>7s} {'%':>7s} "
        f"{'kJ/kg':>8s} {'':>6s} {'kJ/kg':>8s} {'':>6s} "
        f"{'kJ/kgK':>7s} {'':>6s} {'kJ/kgK':>7s} {'':>6s}"
    )
    print(header)
    print(units)
    print("-" * len(header))

    max_diff = 0.0
    all_pass = True

    for row in REFERENCE_TABLE:
        P_Pa = row["P_bar"] * 1e5

        T_sat = PropsSI("T", "P", P_Pa, "Q", 0, "Water") - 273.15
        h_f = PropsSI("H", "P", P_Pa, "Q", 0, "Water") / 1000
        h_g = PropsSI("H", "P", P_Pa, "Q", 1, "Water") / 1000
        s_f = PropsSI("S", "P", P_Pa, "Q", 0, "Water") / 1000
        s_g = PropsSI("S", "P", P_Pa, "Q", 1, "Water") / 1000

        diffs = {
            "T_sat": pct_diff(T_sat, row["T_sat_C"]),
            "h_f": pct_diff(h_f, row["h_f"]),
            "h_g": pct_diff(h_g, row["h_g"]),
            "s_f": pct_diff(s_f, row["s_f"]),
            "s_g": pct_diff(s_g, row["s_g"]),
        }

        row_max = max(abs(d) for d in diffs.values())
        max_diff = max(max_diff, row_max)
        if row_max > 1.0:
            all_pass = False

        print(
            f"{row['P_bar']:6.1f} {T_sat:7.2f} {diffs['T_sat']:+7.3f} "
            f"{h_f:8.2f} {diffs['h_f']:+6.3f} {h_g:8.2f} {diffs['h_g']:+6.3f} "
            f"{s_f:7.4f} {diffs['s_f']:+6.3f} {s_g:7.4f} {diffs['s_g']:+6.3f}"
        )

    print("-" * len(header))
    print(f"  Max absolute % difference: {max_diff:.4f}%")
    status = "PASS" if all_pass else "FAIL"
    print(f"  All within ±1%: {status}")
    print()
    return all_pass


def validate_dead_state():
    """Verify dead state properties: T₀=298.15 K (25°C), P₀=101325 Pa."""
    print("=" * 70)
    print("3. DEAD STATE: T₀ = 25°C (298.15 K), P₀ = 101.325 kPa")
    print("=" * 70)

    T0 = 298.15    # K
    P0 = 101325.0  # Pa

    h0 = PropsSI("H", "T", T0, "P", P0, "Water") / 1000
    s0 = PropsSI("S", "T", T0, "P", P0, "Water") / 1000
    v0 = 1.0 / PropsSI("D", "T", T0, "P", P0, "Water")
    u0 = PropsSI("U", "T", T0, "P", P0, "Water") / 1000

    print(f"  h₀ = {h0:.4f} kJ/kg")
    print(f"  s₀ = {s0:.4f} kJ/(kg·K)")
    print(f"  v₀ = {v0:.6f} m³/kg")
    print(f"  u₀ = {u0:.4f} kJ/kg")
    print()


def validate_critical_point():
    """Display water critical point from CoolProp."""
    print("=" * 70)
    print("4. CRITICAL POINT")
    print("=" * 70)

    T_crit = PropsSI("Tcrit", "Water")
    P_crit = PropsSI("Pcrit", "Water")

    print(f"  T_crit = {T_crit:.3f} K  ({T_crit - 273.15:.2f} °C)")
    print(f"  P_crit = {P_crit:.0f} Pa  ({P_crit / 1e5:.3f} bar)")
    print()


def main():
    print(f"CoolProp version: {CoolProp.__version__}")
    print()

    validate_superheated()
    sat_pass = validate_saturation_table()
    validate_dead_state()
    validate_critical_point()

    print("=" * 70)
    if sat_pass:
        print("VALIDATION PASSED: CoolProp is working correctly.")
    else:
        print("VALIDATION FAILED: Some values exceed ±1% tolerance.")
    print("=" * 70)


if __name__ == "__main__":
    main()
