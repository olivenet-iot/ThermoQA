"""
Physics-valid parameter generation for ThermoQA Tier 1 and Tier 2 questions.

Generates parameter sets that satisfy thermodynamic constraints (e.g.,
superheated means T > T_sat(P) + margin). Uses stratified sampling to
ensure diverse coverage across parameter ranges.
"""

import numpy as np
from CoolProp.CoolProp import PropsSI

from generation.templates.tier1_properties import PropertyTemplate

# Critical point constants
T_CRIT_C = 373.946   # °C
P_CRIT_KPA = 22064.0  # kPa


def _t_sat_c(P_kPa: float) -> float:
    """Saturation temperature in °C for a given pressure in kPa."""
    return PropsSI("T", "P", P_kPa * 1000, "Q", 0, "Water") - 273.15


def _p_sat_kpa(T_C: float) -> float:
    """Saturation pressure in kPa for a given temperature in °C."""
    return PropsSI("P", "T", T_C + 273.15, "Q", 0, "Water") / 1000


def _stratified_sample(rng: np.random.Generator, low: float, high: float,
                        count: int, decimals: int = 0) -> list:
    """Sample `count` values spread across [low, high] using stratified bins."""
    if count == 0:
        return []
    bin_width = (high - low) / count
    values = []
    for i in range(count):
        bin_low = low + i * bin_width
        bin_high = bin_low + bin_width
        val = rng.uniform(bin_low, bin_high)
        values.append(round(val, decimals))
    rng.shuffle(values)
    return list(values)


def _round_pressure(val: float) -> float:
    """Round pressure to engineering-natural values."""
    if val < 200:
        return round(val / 10) * 10       # nearest 10
    elif val < 2000:
        return round(val / 25) * 25       # nearest 25
    elif val < 10000:
        return round(val / 50) * 50       # nearest 50
    else:
        return round(val / 100) * 100     # nearest 100


def _round_temperature(val: float) -> float:
    """Round temperature to nearest integer."""
    return round(val)


def _round_quality(val: float) -> float:
    """Round quality to 2 decimal places."""
    return round(val, 2)


def sample_subcooled(template: PropertyTemplate, count: int,
                     rng: np.random.Generator) -> list[dict]:
    """Sample subcooled liquid parameters: T < T_sat(P) - 5."""
    params = []
    pressures = _stratified_sample(rng, 500, 15000, count)
    for P in pressures:
        P = _round_pressure(P)
        try:
            T_sat = _t_sat_c(P)
        except Exception:
            continue
        T_max = T_sat - 5
        if T_max < 25:
            continue
        T_low = max(20, 20)
        T = _round_temperature(rng.uniform(T_low, T_max))
        # Re-validate after rounding
        if T >= T_sat - 5:
            T = _round_temperature(T_sat - 8)
        if T < 20:
            continue
        params.append({"T_C": float(T), "P_kPa": float(P)})
    return params[:count]


def sample_saturated_liquid_P(template: PropertyTemplate, count: int,
                               rng: np.random.Generator) -> list[dict]:
    """Sample pressures for saturated liquid (given P)."""
    pressures = _stratified_sample(rng, 100, 10000, count)
    return [{"P_kPa": float(_round_pressure(P))} for P in pressures]


def sample_saturated_liquid_T(template: PropertyTemplate, count: int,
                               rng: np.random.Generator) -> list[dict]:
    """Sample temperatures for saturated liquid (given T)."""
    temps = _stratified_sample(rng, 100, 310, count)
    return [{"T_C": float(_round_temperature(T))} for T in temps]


def sample_saturated_vapor_P(template: PropertyTemplate, count: int,
                              rng: np.random.Generator) -> list[dict]:
    """Sample pressures for saturated vapor (given P)."""
    pressures = _stratified_sample(rng, 100, 10000, count)
    return [{"P_kPa": float(_round_pressure(P))} for P in pressures]


def sample_saturated_vapor_T(template: PropertyTemplate, count: int,
                              rng: np.random.Generator) -> list[dict]:
    """Sample temperatures for saturated vapor (given T)."""
    temps = _stratified_sample(rng, 100, 310, count)
    return [{"T_C": float(_round_temperature(T))} for T in temps]


def sample_wet_steam_Px(template: PropertyTemplate, count: int,
                         rng: np.random.Generator) -> list[dict]:
    """Sample P and x for wet steam."""
    pressures = _stratified_sample(rng, 100, 8000, count)
    qualities = _stratified_sample(rng, 0.10, 0.95, count, decimals=2)
    params = []
    for P, x in zip(pressures, qualities):
        params.append({
            "P_kPa": float(_round_pressure(P)),
            "x": float(_round_quality(x)),
        })
    return params


def sample_wet_steam_Tx(template: PropertyTemplate, count: int,
                         rng: np.random.Generator) -> list[dict]:
    """Sample T and x for wet steam (given T on saturation curve)."""
    temps = _stratified_sample(rng, 100, 295, count)
    qualities = _stratified_sample(rng, 0.10, 0.95, count, decimals=2)
    params = []
    for T, x in zip(temps, qualities):
        params.append({
            "T_C": float(_round_temperature(T)),
            "x": float(_round_quality(x)),
        })
    return params


def sample_wet_steam_Ph_inverse(template: PropertyTemplate, count: int,
                                 rng: np.random.Generator) -> list[dict]:
    """Sample P, then compute h in the two-phase region for inverse problems."""
    pressures = _stratified_sample(rng, 100, 8000, count)
    qualities = _stratified_sample(rng, 0.15, 0.90, count, decimals=2)
    params = []
    for P, x in zip(pressures, qualities):
        P = _round_pressure(P)
        P_Pa = P * 1000
        try:
            h = PropsSI("H", "P", P_Pa, "Q", x, "Water") / 1000
        except Exception:
            continue
        params.append({
            "P_kPa": float(P),
            "h_kJ_kg": round(h, 1),
        })
    return params[:count]


def sample_wet_steam_Ps_inverse(template: PropertyTemplate, count: int,
                                 rng: np.random.Generator) -> list[dict]:
    """Sample P, then compute s in the two-phase region for inverse problems."""
    pressures = _stratified_sample(rng, 100, 8000, count)
    qualities = _stratified_sample(rng, 0.15, 0.90, count, decimals=2)
    params = []
    for P, x in zip(pressures, qualities):
        P = _round_pressure(P)
        P_Pa = P * 1000
        try:
            s = PropsSI("S", "P", P_Pa, "Q", x, "Water") / 1000
        except Exception:
            continue
        params.append({
            "P_kPa": float(P),
            "s_kJ_kgK": round(s, 4),
        })
    return params[:count]


def sample_superheated(template: PropertyTemplate, count: int,
                        rng: np.random.Generator) -> list[dict]:
    """Sample superheated vapor: T > T_sat(P) + 10, P < P_crit."""
    params = []
    pressures = _stratified_sample(rng, 100, 15000, count)
    for P in pressures:
        P = _round_pressure(P)
        if P >= P_CRIT_KPA:
            P = _round_pressure(rng.uniform(100, 20000))
            if P >= P_CRIT_KPA:
                P = 15000.0
        try:
            T_sat = _t_sat_c(P)
        except Exception:
            continue
        T_min = T_sat + 10
        T_max = 600
        if T_min >= T_max:
            continue
        T = _round_temperature(rng.uniform(T_min, T_max))
        if T <= T_sat + 10:
            T = _round_temperature(T_sat + 15)
        params.append({"T_C": float(T), "P_kPa": float(P)})
    return params[:count]


def sample_supercritical(template: PropertyTemplate, count: int,
                          rng: np.random.Generator) -> list[dict]:
    """Sample supercritical: T > T_crit, P > P_crit."""
    temps = _stratified_sample(rng, 375, 600, count)
    pressures = _stratified_sample(rng, 22500, 35000, count)
    params = []
    for T, P in zip(temps, pressures):
        T = _round_temperature(T)
        P = _round_pressure(P)
        if T <= T_CRIT_C:
            T = 375.0
        if P <= P_CRIT_KPA:
            P = 22500.0
        params.append({"T_C": float(T), "P_kPa": float(P)})
    return params


def sample_phase_obvious(template: PropertyTemplate, count: int,
                          rng: np.random.Generator) -> list[dict]:
    """Sample obviously subcooled, superheated, and supercritical states for phase determination.

    Guarantees phase diversity: ~1/3 subcooled, ~1/2 superheated, ~1/6 supercritical.
    Uses quota-based assembly so over-sampling doesn't skew the distribution.
    """
    # Fixed quotas based on desired count (not the over-sampled count)
    # For count=6: 2 subcooled, 3 superheated, 1 supercritical
    # For larger counts: roughly same proportions
    n_supercritical = max(1, count // 6)
    n_subcooled = max(1, count // 3)
    n_superheated = max(1, count - n_subcooled - n_supercritical)

    # Generate each bucket with +2 overshoot for CoolProp failures
    subcooled = []
    for P in _stratified_sample(rng, 200, 10000, n_subcooled + 2):
        P = _round_pressure(P)
        try:
            T_sat = _t_sat_c(P)
        except Exception:
            continue
        T = _round_temperature(rng.uniform(20, max(25, T_sat - 30)))
        subcooled.append({"T_C": float(T), "P_kPa": float(P)})

    superheated = []
    for P in _stratified_sample(rng, 100, 10000, n_superheated + 2):
        P = _round_pressure(P)
        try:
            T_sat = _t_sat_c(P)
        except Exception:
            continue
        T_min = T_sat + 30
        if T_min > 600:
            continue
        T = _round_temperature(rng.uniform(T_min, 600))
        superheated.append({"T_C": float(T), "P_kPa": float(P)})

    supercritical = []
    for T, P in zip(
        _stratified_sample(rng, 400, 550, n_supercritical + 2),
        _stratified_sample(rng, 25000, 35000, n_supercritical + 2),
    ):
        supercritical.append({
            "T_C": float(_round_temperature(T)),
            "P_kPa": float(_round_pressure(P)),
        })

    # Take exact quotas from each bucket
    params = subcooled[:n_subcooled] + superheated[:n_superheated] + supercritical[:n_supercritical]
    rng.shuffle(params)
    return params[:count]


def sample_phase_near_boundary(template: PropertyTemplate, count: int,
                                rng: np.random.Generator) -> list[dict]:
    """Sample states near the saturation boundary (within 2-5C of T_sat)."""
    params = []
    pressures = _stratified_sample(rng, 100, 15000, count)
    for i, P in enumerate(pressures):
        P = _round_pressure(P)
        if P >= P_CRIT_KPA:
            P = 15000.0
        try:
            T_sat = _t_sat_c(P)
        except Exception:
            continue
        # Alternate deterministically: even index → below (subcooled), odd → above (superheated)
        offset = rng.uniform(2, 5)
        if i % 2 == 0:
            T = round(T_sat - offset, 1)
        else:
            T = round(T_sat + offset, 1)
        params.append({"T_C": float(T), "P_kPa": float(P)})
    return params[:count]


def sample_phase_tricky(template: PropertyTemplate, count: int,
                         rng: np.random.Generator) -> list[dict]:
    """Sample tricky phase determination cases (supercritical, near-critical, high-P subcooled)."""
    params = []
    third = max(1, count // 3)

    # Supercritical
    for T, P in zip(
        _stratified_sample(rng, 375, 550, third),
        _stratified_sample(rng, 22500, 35000, third),
    ):
        params.append({
            "T_C": float(_round_temperature(T)),
            "P_kPa": float(_round_pressure(P)),
        })

    # High-pressure subcooled (P > P_crit, T < T_crit)
    for T, P in zip(
        _stratified_sample(rng, 100, 370, third),
        _stratified_sample(rng, 23000, 35000, third),
    ):
        params.append({
            "T_C": float(_round_temperature(T)),
            "P_kPa": float(_round_pressure(P)),
        })

    # Near-critical
    remainder = count - 2 * third
    for _ in range(remainder):
        T = _round_temperature(rng.uniform(360, 385))
        P = _round_pressure(rng.uniform(20000, 24000))
        params.append({"T_C": float(T), "P_kPa": float(P)})

    return params[:count]


def sample_inverse_Ph_T(template: PropertyTemplate, count: int,
                          rng: np.random.Generator) -> list[dict]:
    """Generate forward state, compute h, present as P,h -> T inverse problem."""
    params = []
    pressures = _stratified_sample(rng, 200, 12000, count)
    for i, P in enumerate(pressures):
        P = _round_pressure(P)
        P_Pa = P * 1000
        try:
            if P >= P_CRIT_KPA:
                T_C = _round_temperature(rng.uniform(380, 550))
            elif i % 4 == 0 and P < P_CRIT_KPA:
                # Subcooled state: T well below T_sat
                T_sat = _t_sat_c(P)
                T_max = T_sat - 10
                if T_max < 25:
                    T_sat = _t_sat_c(P)
                    T_C = _round_temperature(rng.uniform(T_sat + 20, min(600, T_sat + 300)))
                else:
                    T_C = _round_temperature(rng.uniform(25, T_max))
            else:
                T_sat = _t_sat_c(P)
                T_C = _round_temperature(rng.uniform(T_sat + 20, min(600, T_sat + 300)))
            T_K = T_C + 273.15
            h = PropsSI("H", "T", T_K, "P", P_Pa, "Water") / 1000
        except Exception:
            continue
        params.append({
            "P_kPa": float(P),
            "h_kJ_kg": round(h, 1),
        })
    return params[:count]


def sample_inverse_Ps_T(template: PropertyTemplate, count: int,
                          rng: np.random.Generator) -> list[dict]:
    """Generate forward state, compute s, present as P,s -> T inverse problem."""
    params = []
    pressures = _stratified_sample(rng, 200, 12000, count)
    for i, P in enumerate(pressures):
        P = _round_pressure(P)
        P_Pa = P * 1000
        try:
            if P >= P_CRIT_KPA:
                T_C = _round_temperature(rng.uniform(380, 550))
            elif i % 4 == 0 and P < P_CRIT_KPA:
                # Subcooled state: T well below T_sat
                T_sat = _t_sat_c(P)
                T_max = T_sat - 10
                if T_max < 25:
                    T_sat = _t_sat_c(P)
                    T_C = _round_temperature(rng.uniform(T_sat + 20, min(600, T_sat + 300)))
                else:
                    T_C = _round_temperature(rng.uniform(25, T_max))
            else:
                T_sat = _t_sat_c(P)
                T_C = _round_temperature(rng.uniform(T_sat + 20, min(600, T_sat + 300)))
            T_K = T_C + 273.15
            s = PropsSI("S", "T", T_K, "P", P_Pa, "Water") / 1000
        except Exception:
            continue
        params.append({
            "P_kPa": float(P),
            "s_kJ_kgK": round(s, 4),
        })
    return params[:count]


def sample_inverse_Ph_sv(template: PropertyTemplate, count: int,
                          rng: np.random.Generator) -> list[dict]:
    """Generate forward state (P,T), compute h, present as P,h -> s,v,T inverse."""
    return sample_inverse_Ph_T(template, count, rng)


def sample_inverse_hs_TP(template: PropertyTemplate, count: int,
                           rng: np.random.Generator) -> list[dict]:
    """Generate forward state, compute h and s, present as h,s -> T,P."""
    params = []

    # Superheated targets (T, P in kPa)
    sh_targets = [
        (400, 5000), (250, 1000), (500, 10000),
    ]
    # Subcooled target
    sl_targets = [
        (80, 5000),
    ]
    targets = sh_targets + sl_targets
    rng.shuffle(targets)
    for T_C, P in targets[:count]:
        P_Pa = P * 1000
        T_K = T_C + 273.15
        try:
            h = PropsSI("H", "T", T_K, "P", P_Pa, "Water") / 1000
            s = PropsSI("S", "T", T_K, "P", P_Pa, "Water") / 1000
        except Exception:
            continue
        params.append({
            "h_kJ_kg": round(h, 1),
            "s_kJ_kgK": round(s, 4),
        })
    return params[:count]


def sample_inverse_Ph_x(template: PropertyTemplate, count: int,
                          rng: np.random.Generator) -> list[dict]:
    """Sample P, compute h for a wet steam state, present as P,h -> x."""
    return sample_wet_steam_Ph_inverse(template, count, rng)


# Dispatcher: maps (category, subcategory) -> sampling function
_SAMPLERS = {
    ("subcooled_liquid", "multi_property"): sample_subcooled,
    ("subcooled_liquid", "u_and_rho"): sample_subcooled,
    ("subcooled_liquid", "single_property"): sample_subcooled,
    ("saturated_liquid", "given_P_all_props"): sample_saturated_liquid_P,
    ("saturated_liquid", "given_T_all_props"): sample_saturated_liquid_T,
    ("saturated_liquid", "given_P_single"): sample_saturated_liquid_P,
    ("saturated_liquid", "given_T_single"): sample_saturated_liquid_T,
    ("wet_steam", "given_P_x"): sample_wet_steam_Px,
    ("wet_steam", "given_T_x"): sample_wet_steam_Tx,
    ("wet_steam", "inverse_P_h"): sample_wet_steam_Ph_inverse,
    ("wet_steam", "inverse_P_s"): sample_wet_steam_Ps_inverse,
    ("wet_steam", "single_property"): sample_wet_steam_Px,
    ("saturated_vapor", "given_P_all_props"): sample_saturated_vapor_P,
    ("saturated_vapor", "given_T_all_props"): sample_saturated_vapor_T,
    ("saturated_vapor", "single_property"): sample_saturated_vapor_P,
    ("superheated_vapor", "multi_property"): sample_superheated,
    ("superheated_vapor", "h_only"): sample_superheated,
    ("superheated_vapor", "s_and_v"): sample_superheated,
    ("superheated_vapor", "u_rho_v"): sample_superheated,
    ("supercritical", "h_s_v"): sample_supercritical,
    ("supercritical", "all_props_phase"): sample_supercritical,
    ("phase_determination", "obvious"): sample_phase_obvious,
    ("phase_determination", "near_boundary"): sample_phase_near_boundary,
    ("phase_determination", "tricky"): sample_phase_tricky,
    ("inverse_lookups", "P_h_to_T"): sample_inverse_Ph_T,
    ("inverse_lookups", "P_s_to_T"): sample_inverse_Ps_T,
    ("inverse_lookups", "P_h_to_s_v"): sample_inverse_Ph_sv,
    ("inverse_lookups", "h_s_to_T_P"): sample_inverse_hs_TP,
    ("inverse_lookups", "P_h_to_x"): sample_inverse_Ph_x,
}


def sample_params(template: PropertyTemplate, count: int,
                   seed: int = 42) -> list[dict]:
    """
    Generate `count` physically valid parameter sets for the given template.

    Uses stratified sampling + physics constraints to produce diverse,
    valid parameter sets. Reproducible via seed.
    """
    rng = np.random.default_rng(seed)
    key = (template.category, template.subcategory)
    sampler = _SAMPLERS.get(key)
    if sampler is None:
        raise ValueError(f"No sampler for {key}")
    # Over-sample slightly then trim, in case some get filtered
    raw = sampler(template, count + 5, rng)
    return raw[:count]


# ══════════════════════════════════════════════════════════
# TIER 2 SAMPLERS — Component Analysis
# ══════════════════════════════════════════════════════════

def _round_mpa(val: float, decimals: int = 2) -> float:
    """Round MPa pressure to N decimal places."""
    return round(val, decimals)


def _round_mass_flow(val: float) -> float:
    """Round mass flow rate to 1 decimal."""
    return round(val, 1)


def _t_sat_c_mpa(P_MPa: float, fluid: str = "Water") -> float:
    """Saturation temperature (°C) from P in MPa."""
    return PropsSI("T", "P", P_MPa * 1e6, "Q", 0, fluid) - 273.15


def sample_turbine_water(count: int, rng: np.random.Generator) -> list[dict]:
    """Turbine with water: superheated inlet, expand to lower P."""
    params = []
    P1_vals = _stratified_sample(rng, 1.0, 15.0, count + 3, decimals=1)
    for P1 in P1_vals:
        P1 = _round_mpa(P1, 1)
        try:
            T_sat = _t_sat_c_mpa(P1)
        except Exception:
            continue
        T1 = round(rng.uniform(max(T_sat + 20, 300), 600))
        P2 = _round_mpa(rng.uniform(0.01, min(0.5 * P1, 1.0)), 2)
        if P2 <= 0.005:
            P2 = 0.01
        eta_s = round(rng.uniform(0.70, 0.95), 2)
        params.append({"T1_C": float(T1), "P1_MPa": float(P1),
                        "P2_MPa": float(P2), "eta_s": float(eta_s)})
    return params[:count]


def sample_turbine_air(count: int, rng: np.random.Generator) -> list[dict]:
    """Turbine with air (ideal gas): T1 in Kelvin."""
    params = []
    T1_vals = _stratified_sample(rng, 800, 1500, count + 2, decimals=0)
    for T1 in T1_vals:
        T1 = round(T1)
        P1 = _round_mpa(rng.uniform(0.5, 2.0), 2)
        P2 = _round_mpa(rng.uniform(0.1, min(0.5, P1 * 0.5)), 2)
        if P2 <= 0.05:
            P2 = 0.1
        eta_s = round(rng.uniform(0.80, 0.92), 2)
        params.append({"T1_C": float(T1), "P1_MPa": float(P1),
                        "P2_MPa": float(P2), "eta_s": float(eta_s)})
    return params[:count]


def sample_compressor_water(count: int, rng: np.random.Generator) -> list[dict]:
    """Compressor with steam: superheated vapor at low P, compress to higher P."""
    params = []
    P1_vals = _stratified_sample(rng, 0.01, 0.5, count + 3, decimals=2)
    for P1 in P1_vals:
        P1 = _round_mpa(P1, 2)
        if P1 < 0.01:
            P1 = 0.01
        try:
            T_sat = _t_sat_c_mpa(P1)
        except Exception:
            continue
        T1 = round(rng.uniform(max(T_sat + 20, 100), 300))
        P2 = _round_mpa(rng.uniform(max(P1 * 2, 0.5), 5.0), 1)
        eta_s = round(rng.uniform(0.75, 0.90), 2)
        params.append({"T1_C": float(T1), "P1_MPa": float(P1),
                        "P2_MPa": float(P2), "eta_s": float(eta_s)})
    return params[:count]


def sample_compressor_r134a(count: int, rng: np.random.Generator) -> list[dict]:
    """Compressor with R-134a: superheated vapor."""
    params = []
    P1_vals = _stratified_sample(rng, 0.1, 0.5, count + 3, decimals=2)
    for P1 in P1_vals:
        P1 = _round_mpa(P1, 2)
        try:
            T_sat = _t_sat_c_mpa(P1, "R134a")
        except Exception:
            continue
        T1 = round(rng.uniform(max(T_sat + 5, -10), 30))
        P2 = _round_mpa(rng.uniform(max(P1 * 2, 0.8), 2.0), 2)
        eta_s = round(rng.uniform(0.75, 0.88), 2)
        params.append({"T1_C": float(T1), "P1_MPa": float(P1),
                        "P2_MPa": float(P2), "eta_s": float(eta_s)})
    return params[:count]


def sample_compressor_air(count: int, rng: np.random.Generator) -> list[dict]:
    """Compressor with air: T1 in Kelvin."""
    params = []
    T1_vals = _stratified_sample(rng, 280, 350, count + 2, decimals=0)
    for T1 in T1_vals:
        T1 = round(T1)
        P1 = _round_mpa(rng.uniform(0.1, 0.2), 2)
        P2 = _round_mpa(rng.uniform(0.5, 2.0), 1)
        eta_s = round(rng.uniform(0.78, 0.90), 2)
        params.append({"T1_C": float(T1), "P1_MPa": float(P1),
                        "P2_MPa": float(P2), "eta_s": float(eta_s)})
    return params[:count]


def sample_pump_water(count: int, rng: np.random.Generator) -> list[dict]:
    """Pump with water: liquid inlet, large P increase."""
    params = []
    T1_vals = _stratified_sample(rng, 20, 80, count + 2, decimals=0)
    for T1 in T1_vals:
        T1 = round(T1)
        P1 = _round_mpa(rng.uniform(0.005, 0.1), 3)
        P2 = _round_mpa(rng.uniform(1.0, 15.0), 1)
        eta_s = round(rng.uniform(0.70, 0.90), 2)
        # Ensure liquid at inlet: T1 < T_sat(P1)
        try:
            T_sat = _t_sat_c_mpa(P1)
            if T1 >= T_sat - 2:
                # Increase P1 to keep liquid
                P1 = _round_mpa(max(0.1, _p_sat_kpa(T1 + 5) / 1000), 3)
        except Exception:
            pass
        params.append({"T1_C": float(T1), "P1_MPa": float(P1),
                        "P2_MPa": float(P2), "eta_s": float(eta_s)})
    return params[:count]


def sample_hx_water_water(count: int, rng: np.random.Generator) -> list[dict]:
    """Heat exchanger: both streams Water, liquid."""
    params = []
    for _ in range(count + 20):
        P_h = _round_mpa(rng.uniform(0.5, 5.0), 1)
        P_c = _round_mpa(rng.uniform(0.5, 5.0), 1)
        T_h_in = round(rng.uniform(60, 95))
        T_h_out = round(rng.uniform(30, min(70, T_h_in - 10)))
        T_c_in = round(rng.uniform(15, min(40, T_h_out - 5)))
        m_h = _round_mass_flow(rng.uniform(0.5, 10.0))
        m_c = _round_mass_flow(rng.uniform(0.5, 10.0))
        # Validate: all temps below T_sat at their pressures
        try:
            T_sat_h = _t_sat_c_mpa(P_h)
            T_sat_c = _t_sat_c_mpa(P_c)
            if T_h_in >= T_sat_h - 5:
                continue
            if T_c_in >= T_sat_c - 5:
                continue
        except Exception:
            continue
        if T_h_out <= T_c_in + 3:
            continue
        # Estimate T_c_out and ensure it stays liquid
        Q_est = m_h * 4.18 * (T_h_in - T_h_out)
        T_c_out_est = T_c_in + Q_est / (m_c * 4.18)
        if T_c_out_est >= T_sat_c - 10:
            continue
        if T_c_out_est >= T_h_in:
            continue
        params.append({
            "T_h_in": float(T_h_in), "T_h_out": float(T_h_out),
            "T_c_in": float(T_c_in), "P_h_MPa": float(P_h),
            "P_c_MPa": float(P_c), "m_h": float(m_h), "m_c": float(m_c),
        })
    return params[:count]


def sample_hx_water_r134a(count: int, rng: np.random.Generator) -> list[dict]:
    """Heat exchanger: hot Water, cold R-134a (both liquid)."""
    params = []
    for _ in range(count + 20):
        P_h = _round_mpa(rng.uniform(0.5, 5.0), 1)
        P_c = _round_mpa(rng.uniform(0.8, 1.5), 2)  # higher P_c for R-134a
        T_h_in = round(rng.uniform(60, 85))
        T_h_out = round(rng.uniform(35, min(60, T_h_in - 10)))
        T_c_in = round(rng.uniform(10, 25))
        m_h = _round_mass_flow(rng.uniform(1.0, 5.0))
        m_c = _round_mass_flow(rng.uniform(2.0, 10.0))  # larger cold flow to limit T rise
        # Validate liquid phases
        try:
            if T_h_in >= _t_sat_c_mpa(P_h) - 2:
                continue
            T_sat_r134a = _t_sat_c_mpa(P_c, "R134a")
            if T_c_in >= T_sat_r134a - 2:
                continue
        except Exception:
            continue
        if T_h_out <= T_c_in + 3:
            continue
        # Estimate T_c_out to ensure it stays liquid
        # Q ≈ m_h * cp_water * (T_h_in - T_h_out)
        # T_c_out ≈ T_c_in + Q / (m_c * cp_r134a)
        # cp_water ~ 4.2, cp_r134a ~ 1.4
        Q_est = m_h * 4.2 * (T_h_in - T_h_out)
        T_c_out_est = T_c_in + Q_est / (m_c * 1.4)
        try:
            if T_c_out_est >= T_sat_r134a - 5:
                continue
        except Exception:
            continue
        params.append({
            "T_h_in": float(T_h_in), "T_h_out": float(T_h_out),
            "T_c_in": float(T_c_in), "P_h_MPa": float(P_h),
            "P_c_MPa": float(P_c), "m_h": float(m_h), "m_c": float(m_c),
        })
    return params[:count]


def sample_boiler_water(count: int, rng: np.random.Generator) -> list[dict]:
    """Boiler: compressed liquid in, superheated steam out."""
    params = []
    P_vals = _stratified_sample(rng, 1.0, 15.0, count + 3, decimals=1)
    for P in P_vals:
        P = _round_mpa(P, 1)
        try:
            T_sat = _t_sat_c_mpa(P)
        except Exception:
            continue
        T_in = round(rng.uniform(30, min(80, T_sat - 10)))
        T_out = round(rng.uniform(max(T_sat + 20, 300), 600))
        T_source = round(rng.uniform(800, 2000))
        # Ensure T_source > T_out_K + 100
        T_out_K = T_out + 273.15
        if T_source < T_out_K + 100:
            T_source = round(T_out_K + 150)
        params.append({
            "T_in_C": float(T_in), "P_MPa": float(P),
            "T_out_C": float(T_out), "T_source_K": float(T_source),
        })
    return params[:count]


def sample_mixer_water(count: int, rng: np.random.Generator) -> list[dict]:
    """Mixing chamber: two water streams at same pressure."""
    params = []
    P_vals = _stratified_sample(rng, 0.1, 2.0, count + 3, decimals=1)
    for P in P_vals:
        P = _round_mpa(P, 1)
        if P < 0.1:
            P = 0.1
        try:
            T_sat = _t_sat_c_mpa(P)
        except Exception:
            continue
        # Stream 1: hotter (could be superheated or liquid)
        T1 = round(rng.uniform(100, min(300, T_sat + 50)))
        # Stream 2: cooler (liquid)
        T2 = round(rng.uniform(20, min(80, T1 - 20)))
        m1 = _round_mass_flow(rng.uniform(1.0, 10.0))
        m2 = _round_mass_flow(rng.uniform(1.0, 10.0))
        if T1 <= T2:
            continue
        params.append({
            "T1_C": float(T1), "T2_C": float(T2),
            "P_MPa": float(P), "m1": float(m1), "m2": float(m2),
        })
    return params[:count]


def sample_nozzle_water(count: int, rng: np.random.Generator) -> list[dict]:
    """Nozzle with steam: superheated inlet, expand."""
    params = []
    P1_vals = _stratified_sample(rng, 0.5, 5.0, count + 3, decimals=1)
    for P1 in P1_vals:
        P1 = _round_mpa(P1, 1)
        try:
            T_sat = _t_sat_c_mpa(P1)
        except Exception:
            continue
        T1 = round(rng.uniform(max(T_sat + 20, 200), 500))
        P2 = _round_mpa(rng.uniform(0.1, min(0.5 * P1, 1.0)), 2)
        if P2 < 0.05:
            P2 = 0.1
        V1 = round(rng.uniform(10, 80))
        eta_nozzle = round(rng.uniform(0.90, 0.98), 2)
        params.append({
            "T1_C": float(T1), "P1_MPa": float(P1),
            "P2_MPa": float(P2), "V1": float(V1),
            "eta_nozzle": float(eta_nozzle),
        })
    return params[:count]


def sample_nozzle_air(count: int, rng: np.random.Generator) -> list[dict]:
    """Nozzle with air: T1 in Kelvin."""
    params = []
    T1_vals = _stratified_sample(rng, 400, 900, count + 2, decimals=0)
    for T1 in T1_vals:
        T1 = round(T1)
        P1 = _round_mpa(rng.uniform(0.3, 1.0), 2)
        P2 = _round_mpa(rng.uniform(0.1, min(0.3, P1 * 0.5)), 2)
        if P2 < 0.05:
            P2 = 0.1
        V1 = round(rng.uniform(30, 100))
        eta_nozzle = round(rng.uniform(0.92, 0.98), 2)
        params.append({
            "T1_C": float(T1), "P1_MPa": float(P1),
            "P2_MPa": float(P2), "V1": float(V1),
            "eta_nozzle": float(eta_nozzle),
        })
    return params[:count]


# Tier 2 sampler dispatcher: maps template_id prefix → sampling function
_TIER2_SAMPLERS = {
    "TRB-AW": sample_turbine_water,
    "TRB-BW": sample_turbine_water,
    "TRB-CW": sample_turbine_water,
    "TRB-AA": sample_turbine_air,
    "TRB-BA": sample_turbine_air,
    "TRB-CA": sample_turbine_air,
    "CMP-AW": sample_compressor_water,
    "CMP-BW": sample_compressor_water,
    "CMP-CW": sample_compressor_water,
    "CMP-AR": sample_compressor_r134a,
    "CMP-BR": sample_compressor_r134a,
    "CMP-AA": sample_compressor_air,
    "CMP-BA": sample_compressor_air,
    "CMP-CA": sample_compressor_air,
    "PMP-AW": sample_pump_water,
    "PMP-BW": sample_pump_water,
    "PMP-CW": sample_pump_water,
    "HX-AW": sample_hx_water_water,
    "HX-BW": sample_hx_water_water,
    "HX-CW": sample_hx_water_water,
    "HX-AR": sample_hx_water_r134a,
    "HX-BR": sample_hx_water_r134a,
    "HX-CR": sample_hx_water_r134a,
    "BLR-AW": sample_boiler_water,
    "BLR-BW": sample_boiler_water,
    "BLR-CW": sample_boiler_water,
    "MIX-AW": sample_mixer_water,
    "MIX-BW": sample_mixer_water,
    "MIX-CW": sample_mixer_water,
    "NOZ-AW": sample_nozzle_water,
    "NOZ-BW": sample_nozzle_water,
    "NOZ-CW": sample_nozzle_water,
    "NOZ-AA": sample_nozzle_air,
    "NOZ-BA": sample_nozzle_air,
    "NOZ-CA": sample_nozzle_air,
}


def sample_tier2_params(template_id: str, count: int,
                         seed: int = 42) -> list[dict]:
    """
    Generate `count` physically valid parameter sets for a Tier 2 template.
    """
    rng = np.random.default_rng(seed)
    sampler = _TIER2_SAMPLERS.get(template_id)
    if sampler is None:
        raise ValueError(f"No Tier 2 sampler for template: {template_id}")
    raw = sampler(count + 5, rng)
    return raw[:count]


# ══════════════════════════════════════════════════════════
# TIER 3 SAMPLERS — Cycle Analysis
# ══════════════════════════════════════════════════════════

def _sample_rankine_ideal(count: int, rng: np.random.Generator, depth: str = "A") -> list[dict]:
    """Sample parameters for Ideal Rankine Cycle."""
    from generation.cycle_state_generator import generate_cycle
    params_list = []
    P_cond_vals = _stratified_sample(rng, 5, 50, count + 10, decimals=0)
    for P_cond in P_cond_vals:
        P_boiler = _round_mpa(rng.uniform(2, 15), 1)
        try:
            T_sat = _t_sat_c_mpa(P_boiler)
        except Exception:
            continue
        T3 = round(rng.uniform(max(350, T_sat + 30), 600))
        if T3 <= T_sat + 20:
            continue
        m_dot = round(rng.uniform(5, 100), 1)
        params = {"P_cond_kPa": float(P_cond), "P_boiler_MPa": float(P_boiler),
                  "T3_C": float(T3), "m_dot_kgs": float(m_dot)}
        if depth in ("B", "C"):
            T3_K = T3 + 273.15
            T_sat_cond_K = PropsSI("T", "Q", 0, "P", P_cond * 1000, "Water")
            params["T_source_K"] = round(T3_K + rng.uniform(50, 200), 1)
            params["T_sink_K"] = round(T_sat_cond_K - rng.uniform(5, 15), 1)
        try:
            result = generate_cycle("RNK-I", params)
            if result["meta"]["is_valid"]:
                params_list.append(params)
        except Exception:
            continue
        if len(params_list) >= count:
            break
    return params_list[:count]


def _sample_rankine_actual(count: int, rng: np.random.Generator, depth: str = "A") -> list[dict]:
    """Sample parameters for Actual Rankine Cycle."""
    from generation.cycle_state_generator import generate_cycle
    params_list = []
    P_cond_vals = _stratified_sample(rng, 5, 50, count + 10, decimals=0)
    for P_cond in P_cond_vals:
        P_boiler = _round_mpa(rng.uniform(2, 15), 1)
        try:
            T_sat = _t_sat_c_mpa(P_boiler)
        except Exception:
            continue
        T3 = round(rng.uniform(max(350, T_sat + 30), 600))
        if T3 <= T_sat + 20:
            continue
        eta_pump = round(rng.uniform(0.75, 0.90), 2)
        eta_turb = round(rng.uniform(0.80, 0.92), 2)
        m_dot = round(rng.uniform(5, 100), 1)
        params = {"P_cond_kPa": float(P_cond), "P_boiler_MPa": float(P_boiler),
                  "T3_C": float(T3), "eta_pump": float(eta_pump),
                  "eta_turb": float(eta_turb), "m_dot_kgs": float(m_dot)}
        if depth in ("B", "C"):
            T3_K = T3 + 273.15
            T_sat_cond_K = PropsSI("T", "Q", 0, "P", P_cond * 1000, "Water")
            params["T_source_K"] = round(T3_K + rng.uniform(50, 200), 1)
            params["T_sink_K"] = round(T_sat_cond_K - rng.uniform(5, 15), 1)
        try:
            result = generate_cycle("RNK-A", params)
            if result["meta"]["is_valid"]:
                params_list.append(params)
        except Exception:
            continue
        if len(params_list) >= count:
            break
    return params_list[:count]


def _sample_rankine_reheat(count: int, rng: np.random.Generator, depth: str = "A") -> list[dict]:
    """Sample parameters for Reheat Rankine Cycle."""
    from generation.cycle_state_generator import generate_cycle
    params_list = []
    for _ in range(count + 30):
        P_cond = float(round(rng.uniform(5, 50)))
        P_boiler = _round_mpa(rng.uniform(6, 15), 1)
        P_reheat = _round_mpa(rng.uniform(0.5, 3), 1)
        # Ensure P_cond < P_reheat < P_boiler
        if P_reheat * 1000 <= P_cond or P_reheat >= P_boiler:
            continue
        try:
            T_sat_boiler = _t_sat_c_mpa(P_boiler)
            T_sat_reheat = _t_sat_c_mpa(P_reheat)
        except Exception:
            continue
        T3 = round(rng.uniform(max(400, T_sat_boiler + 30), 600))
        T5 = round(rng.uniform(max(400, T_sat_reheat + 30), 600))
        eta_pump = round(rng.uniform(0.75, 0.90), 2)
        eta_HPT = round(rng.uniform(0.80, 0.92), 2)
        eta_LPT = round(rng.uniform(0.80, 0.92), 2)
        m_dot = round(rng.uniform(10, 100), 1)
        params = {
            "P_cond_kPa": float(P_cond), "P_boiler_MPa": float(P_boiler),
            "P_reheat_MPa": float(P_reheat), "T3_C": float(T3), "T5_C": float(T5),
            "eta_pump": float(eta_pump), "eta_HPT": float(eta_HPT),
            "eta_LPT": float(eta_LPT), "m_dot_kgs": float(m_dot),
        }
        if depth in ("B", "C"):
            T3_K = T3 + 273.15
            T_sat_cond_K = PropsSI("T", "Q", 0, "P", P_cond * 1000, "Water")
            params["T_source_K"] = round(T3_K + rng.uniform(50, 200), 1)
            params["T_sink_K"] = round(T_sat_cond_K - rng.uniform(5, 15), 1)
        try:
            result = generate_cycle("RNK-RH", params)
            if result["meta"]["is_valid"]:
                params_list.append(params)
        except Exception:
            continue
        if len(params_list) >= count:
            break
    return params_list[:count]


def _sample_brayton_ideal(count: int, rng: np.random.Generator, depth: str = "A") -> list[dict]:
    """Sample parameters for Ideal Brayton Cycle."""
    from generation.cycle_state_generator import generate_cycle
    params_list = []
    T1_vals = _stratified_sample(rng, 290, 310, count + 5, decimals=0)
    for T1 in T1_vals:
        T1 = round(T1)
        P1 = round(rng.uniform(95, 105))
        r_p = round(rng.uniform(6, 18))
        T3 = round(rng.uniform(1100, 1600))
        m_dot = round(rng.uniform(10, 200), 1)
        params = {"T1_K": float(T1), "P1_kPa": float(P1), "r_p": float(r_p),
                  "T3_K": float(T3), "m_dot_kgs": float(m_dot)}
        if depth in ("B", "C"):
            params["T_source_K"] = round(T3 + rng.uniform(100, 300), 1)
            params["T_sink_K"] = round(T1 + rng.uniform(5, 15), 1)
        try:
            result = generate_cycle("BRY-I", params)
            if result["meta"]["is_valid"]:
                params_list.append(params)
        except Exception:
            continue
        if len(params_list) >= count:
            break
    return params_list[:count]


def _sample_brayton_actual(count: int, rng: np.random.Generator, depth: str = "A") -> list[dict]:
    """Sample parameters for Actual Brayton Cycle."""
    from generation.cycle_state_generator import generate_cycle
    params_list = []
    T1_vals = _stratified_sample(rng, 290, 310, count + 5, decimals=0)
    for T1 in T1_vals:
        T1 = round(T1)
        P1 = round(rng.uniform(95, 105))
        r_p = round(rng.uniform(6, 18))
        T3 = round(rng.uniform(1100, 1600))
        eta_comp = round(rng.uniform(0.78, 0.88), 2)
        eta_turb = round(rng.uniform(0.82, 0.92), 2)
        m_dot = round(rng.uniform(10, 200), 1)
        params = {"T1_K": float(T1), "P1_kPa": float(P1), "r_p": float(r_p),
                  "T3_K": float(T3), "eta_comp": float(eta_comp),
                  "eta_turb": float(eta_turb), "m_dot_kgs": float(m_dot)}
        if depth in ("B", "C"):
            params["T_source_K"] = round(T3 + rng.uniform(100, 300), 1)
            params["T_sink_K"] = round(T1 + rng.uniform(5, 15), 1)
        try:
            result = generate_cycle("BRY-A", params)
            if result["meta"]["is_valid"]:
                params_list.append(params)
        except Exception:
            continue
        if len(params_list) >= count:
            break
    return params_list[:count]


def _sample_brayton_regenerative(count: int, rng: np.random.Generator, depth: str = "A") -> list[dict]:
    """Sample parameters for Regenerative Brayton Cycle."""
    from generation.cycle_state_generator import generate_cycle
    params_list = []
    for _ in range(count + 30):
        T1 = round(rng.uniform(290, 310))
        P1 = round(rng.uniform(95, 105))
        r_p = round(rng.uniform(6, 14))
        T4 = round(rng.uniform(1100, 1600))
        eta_comp = round(rng.uniform(0.78, 0.88), 2)
        eta_turb = round(rng.uniform(0.82, 0.92), 2)
        epsilon_regen = round(rng.uniform(0.70, 0.90), 2)
        m_dot = round(rng.uniform(10, 200), 1)
        params = {
            "T1_K": float(T1), "P1_kPa": float(P1), "r_p": float(r_p),
            "T4_K": float(T4), "eta_comp": float(eta_comp),
            "eta_turb": float(eta_turb), "epsilon_regen": float(epsilon_regen),
            "m_dot_kgs": float(m_dot),
        }
        if depth in ("B", "C"):
            params["T_source_K"] = round(T4 + rng.uniform(100, 300), 1)
            params["T_sink_K"] = round(T1 + rng.uniform(5, 15), 1)
        try:
            result = generate_cycle("BRY-RG", params)
            if result["meta"]["is_valid"]:
                params_list.append(params)
        except Exception:
            continue
        if len(params_list) >= count:
            break
    return params_list[:count]


def _sample_vcr_actual(count: int, rng: np.random.Generator, depth: str = "A") -> list[dict]:
    """Sample parameters for Actual VCR Cycle (R-134a)."""
    from generation.cycle_state_generator import generate_cycle
    params_list = []
    T_evap_vals = _stratified_sample(rng, -25, 5, count + 10, decimals=0)
    for T_evap in T_evap_vals:
        T_evap = round(T_evap)
        T_cond = round(rng.uniform(30, 50))
        if T_cond - T_evap < 20:
            continue
        eta_comp = round(rng.uniform(0.75, 0.88), 2)
        m_dot = round(rng.uniform(0.01, 0.5), 3)
        params = {"T_evap_C": float(T_evap), "T_cond_C": float(T_cond),
                  "eta_comp": float(eta_comp), "m_dot_kgs": float(m_dot)}
        if depth in ("B", "C"):
            T_cond_K = T_cond + 273.15
            T_evap_K = T_evap + 273.15
            params["T_H_K"] = round(T_cond_K - rng.uniform(5, 15), 1)
            params["T_L_K"] = round(T_evap_K + rng.uniform(5, 10), 1)
        try:
            result = generate_cycle("VCR-A", params)
            if result["meta"]["is_valid"]:
                params_list.append(params)
        except Exception:
            continue
        if len(params_list) >= count:
            break
    return params_list[:count]


_TIER3_SAMPLERS = {
    "RNK-I": _sample_rankine_ideal,
    "RNK-A": _sample_rankine_actual,
    "RNK-RH": _sample_rankine_reheat,
    "BRY-I": _sample_brayton_ideal,
    "BRY-A": _sample_brayton_actual,
    "BRY-RG": _sample_brayton_regenerative,
    "VCR-A": _sample_vcr_actual,
}


def sample_tier3_params(template_id: str, count: int,
                         seed: int = 42) -> list[dict]:
    """
    Generate `count` physically valid parameter sets for a Tier 3 template.

    Template IDs: "RNK-I-A", "RNK-RH-B", "VCR-A-C" etc.
    """
    # Parse: last char is depth, everything before is cycle_type
    depth = template_id[-1]
    cycle_type = template_id[:-2]  # "RNK-I-A" -> "RNK-I"
    rng = np.random.default_rng(seed)
    sampler = _TIER3_SAMPLERS.get(cycle_type)
    if sampler is None:
        raise ValueError(f"No Tier 3 sampler for cycle: {cycle_type} (template: {template_id})")
    raw = sampler(count + 5, rng, depth)
    return raw[:count]
