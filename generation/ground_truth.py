"""
CoolProp ground truth computation for ThermoQA.

Computes thermodynamic properties from given parameters using CoolProp.
All input/output in engineering units; CoolProp called with SI internally.
"""

import CoolProp
from CoolProp.CoolProp import PropsSI

# CoolProp 7.2.0 phase index mapping (verified experimentally)
PHASE_MAP = {
    0: "subcooled_liquid",       # iphase_liquid
    1: "supercritical",          # iphase_supercritical (T>Tc AND P>Pc)
    2: "supercritical_gas",      # iphase_supercritical_gas (T>Tc, P<Pc)
    3: "supercritical_liquid",   # iphase_supercritical_liquid (T<Tc, P>Pc)
    5: "superheated_vapor",      # iphase_gas
    6: "wet_steam",              # iphase_twophase
    8: "not_imposed",
}

P_CRIT_PA = PropsSI("Pcrit", "Water")
T_CRIT_K = PropsSI("Tcrit", "Water")


def get_coolprop_version() -> str:
    return CoolProp.__version__


def get_phase(T_K: float, P_Pa: float) -> str:
    """Get normalized phase name from CoolProp."""
    phase_idx = int(PropsSI("Phase", "T", T_K, "P", P_Pa, "Water"))
    raw = PHASE_MAP.get(phase_idx, f"unknown_{phase_idx}")
    return _normalize_phase(raw)


def get_phase_from_PQ(P_Pa: float, Q: float) -> str:
    """Phase for a state specified by P and Q."""
    if 0 < Q < 1:
        return "wet_steam"
    if Q == 0:
        return "saturated_liquid"
    if Q == 1:
        return "saturated_vapor"
    return "unknown"


def _normalize_phase(raw_phase: str) -> str:
    """Normalize CoolProp phase names for scoring consistency."""
    if raw_phase == "supercritical_gas":
        return "superheated_vapor"
    if raw_phase == "supercritical_liquid":
        return "subcooled_liquid"
    return raw_phase


def _to_K(T_C: float) -> float:
    return T_C + 273.15


def _to_C(T_K: float) -> float:
    return T_K - 273.15


def _to_Pa(P_kPa: float) -> float:
    return P_kPa * 1000.0


def _to_kPa(P_Pa: float) -> float:
    return P_Pa / 1000.0


def compute_properties(given: dict, target_properties: list,
                        fluid: str = "Water") -> dict:
    """
    Compute target properties from given parameters using CoolProp.

    Args:
        given: dict with keys like T_C, P_kPa, x, h_kJ_kg, s_kJ_kgK
        target_properties: list of property keys to compute
        fluid: CoolProp fluid name

    Returns:
        dict mapping property key -> {"value": float, "unit": str}
    """
    # Determine the CoolProp input pair
    input1_name, input1_val, input2_name, input2_val = _resolve_inputs(given)

    results = {}
    for prop in target_properties:
        results[prop] = _compute_single(
            prop, input1_name, input1_val, input2_name, input2_val, fluid, given
        )
    return results


def _resolve_inputs(given: dict) -> tuple:
    """Convert given dict to CoolProp input pair (name1, val1, name2, val2) in SI."""
    keys = set(given.keys()) - {"fluid"}

    if "T_C" in given and "P_kPa" in given:
        return "T", _to_K(given["T_C"]), "P", _to_Pa(given["P_kPa"])

    if "P_kPa" in given and "x" in given:
        return "P", _to_Pa(given["P_kPa"]), "Q", given["x"]

    if "T_C" in given and "x" in given:
        return "T", _to_K(given["T_C"]), "Q", given["x"]

    if "P_kPa" in given and "h_kJ_kg" in given:
        return "P", _to_Pa(given["P_kPa"]), "H", given["h_kJ_kg"] * 1000

    if "P_kPa" in given and "s_kJ_kgK" in given:
        return "P", _to_Pa(given["P_kPa"]), "S", given["s_kJ_kgK"] * 1000

    if "T_C" in given and "h_kJ_kg" in given:
        return "T", _to_K(given["T_C"]), "H", given["h_kJ_kg"] * 1000

    if "h_kJ_kg" in given and "s_kJ_kgK" in given:
        return "H", given["h_kJ_kg"] * 1000, "S", given["s_kJ_kgK"] * 1000

    if "P_kPa" in given and len(keys) == 1:
        # Saturated, given P only — use Q=0 for liquid
        return "P", _to_Pa(given["P_kPa"]), "Q", 0

    if "T_C" in given and len(keys) == 1:
        # Saturated, given T only — use Q=0 for liquid
        return "T", _to_K(given["T_C"]), "Q", 0

    raise ValueError(f"Cannot resolve CoolProp inputs from: {given}")


def _compute_single(prop: str, in1_name: str, in1_val: float,
                     in2_name: str, in2_val: float, fluid: str,
                     given: dict) -> dict:
    """Compute a single property value."""

    # Phase name (special case — not a CoolProp PropsSI call)
    if prop == "phase_name":
        phase = _get_phase_for_inputs(in1_name, in1_val, in2_name, in2_val, fluid)
        return {"value": phase, "unit": "phase", "type": "exact_match"}

    # Quality
    if prop == "x":
        Q = PropsSI("Q", in1_name, in1_val, in2_name, in2_val, fluid)
        return {"value": round(Q, 4), "unit": "dimensionless"}

    # Saturation temperature
    if prop in ("T_sat_C", "T_sat"):
        if in2_name == "Q":
            T_sat = PropsSI("T", in1_name, in1_val, "Q", 0, fluid)
        elif in1_name == "P":
            T_sat = PropsSI("T", "P", in1_val, "Q", 0, fluid)
        elif in1_name == "T":
            T_sat = in1_val  # T itself is T_sat for saturation states
        else:
            # Compute P first, then get T_sat
            P = PropsSI("P", in1_name, in1_val, in2_name, in2_val, fluid)
            T_sat = PropsSI("T", "P", P, "Q", 0, fluid)
        return {"value": round(_to_C(T_sat), 2), "unit": "C"}

    # Saturation pressure
    if prop in ("P_sat_kPa", "P_sat"):
        if in1_name == "T" and in2_name == "Q":
            P_sat = PropsSI("P", "T", in1_val, "Q", 0, fluid)
        elif in1_name == "P":
            P_sat = in1_val
        else:
            T = PropsSI("T", in1_name, in1_val, in2_name, in2_val, fluid)
            P_sat = PropsSI("P", "T", T, "Q", 0, fluid)
        return {"value": round(_to_kPa(P_sat), 2), "unit": "kPa"}

    # Temperature (for inverse lookups)
    if prop == "T_C":
        T_K = PropsSI("T", in1_name, in1_val, in2_name, in2_val, fluid)
        return {"value": round(_to_C(T_K), 2), "unit": "C"}

    # Pressure (for inverse lookups)
    if prop == "P_kPa":
        P_Pa = PropsSI("P", in1_name, in1_val, in2_name, in2_val, fluid)
        return {"value": round(_to_kPa(P_Pa), 2), "unit": "kPa"}

    # Saturated liquid properties
    if prop.startswith("h_f"):
        if in1_name == "P":
            val = PropsSI("H", "P", in1_val, "Q", 0, fluid) / 1000
        else:
            val = PropsSI("H", "T", in1_val, "Q", 0, fluid) / 1000
        return {"value": round(val, 2), "unit": "kJ/kg"}

    if prop.startswith("s_f"):
        if in1_name == "P":
            val = PropsSI("S", "P", in1_val, "Q", 0, fluid) / 1000
        else:
            val = PropsSI("S", "T", in1_val, "Q", 0, fluid) / 1000
        return {"value": round(val, 4), "unit": "kJ/(kg*K)"}

    if prop.startswith("v_f"):
        if in1_name == "P":
            val = 1.0 / PropsSI("D", "P", in1_val, "Q", 0, fluid)
        else:
            val = 1.0 / PropsSI("D", "T", in1_val, "Q", 0, fluid)
        return {"value": round(val, 6), "unit": "m3/kg"}

    if prop.startswith("u_f"):
        if in1_name == "P":
            val = PropsSI("U", "P", in1_val, "Q", 0, fluid) / 1000
        else:
            val = PropsSI("U", "T", in1_val, "Q", 0, fluid) / 1000
        return {"value": round(val, 2), "unit": "kJ/kg"}

    if prop.startswith("rho_f"):
        if in1_name == "P":
            val = PropsSI("D", "P", in1_val, "Q", 0, fluid)
        else:
            val = PropsSI("D", "T", in1_val, "Q", 0, fluid)
        return {"value": round(val, 3), "unit": "kg/m3"}

    # Saturated vapor properties
    if prop.startswith("h_g"):
        if in1_name == "P":
            val = PropsSI("H", "P", in1_val, "Q", 1, fluid) / 1000
        else:
            val = PropsSI("H", "T", in1_val, "Q", 1, fluid) / 1000
        return {"value": round(val, 2), "unit": "kJ/kg"}

    if prop.startswith("s_g"):
        if in1_name == "P":
            val = PropsSI("S", "P", in1_val, "Q", 1, fluid) / 1000
        else:
            val = PropsSI("S", "T", in1_val, "Q", 1, fluid) / 1000
        return {"value": round(val, 4), "unit": "kJ/(kg*K)"}

    if prop.startswith("v_g"):
        if in1_name == "P":
            val = 1.0 / PropsSI("D", "P", in1_val, "Q", 1, fluid)
        else:
            val = 1.0 / PropsSI("D", "T", in1_val, "Q", 1, fluid)
        return {"value": round(val, 5), "unit": "m3/kg"}

    if prop.startswith("u_g"):
        if in1_name == "P":
            val = PropsSI("U", "P", in1_val, "Q", 1, fluid) / 1000
        else:
            val = PropsSI("U", "T", in1_val, "Q", 1, fluid) / 1000
        return {"value": round(val, 2), "unit": "kJ/kg"}

    if prop.startswith("rho_g"):
        if in1_name == "P":
            val = PropsSI("D", "P", in1_val, "Q", 1, fluid)
        else:
            val = PropsSI("D", "T", in1_val, "Q", 1, fluid)
        return {"value": round(val, 4), "unit": "kg/m3"}

    # General properties (for any state: subcooled, superheated, wet, supercritical)
    if prop in ("h_kJ_kg", "h"):
        val = PropsSI("H", in1_name, in1_val, in2_name, in2_val, fluid) / 1000
        return {"value": round(val, 2), "unit": "kJ/kg"}

    if prop in ("s_kJ_kgK", "s"):
        val = PropsSI("S", in1_name, in1_val, in2_name, in2_val, fluid) / 1000
        return {"value": round(val, 4), "unit": "kJ/(kg*K)"}

    if prop in ("v_m3_kg", "v"):
        val = 1.0 / PropsSI("D", in1_name, in1_val, in2_name, in2_val, fluid)
        return {"value": round(val, 6), "unit": "m3/kg"}

    if prop in ("u_kJ_kg", "u"):
        val = PropsSI("U", in1_name, in1_val, in2_name, in2_val, fluid) / 1000
        return {"value": round(val, 2), "unit": "kJ/kg"}

    if prop in ("rho_kg_m3", "rho"):
        val = PropsSI("D", in1_name, in1_val, in2_name, in2_val, fluid)
        return {"value": round(val, 4), "unit": "kg/m3"}

    raise ValueError(f"Unknown property: {prop}")


def _get_phase_for_inputs(in1_name: str, in1_val: float,
                           in2_name: str, in2_val: float, fluid: str) -> str:
    """Determine phase from CoolProp inputs."""
    # Saturation inputs (Q specified)
    if in2_name == "Q":
        if in2_val == 0:
            return "saturated_liquid"
        if in2_val == 1:
            return "saturated_vapor"
        if 0 < in2_val < 1:
            return "wet_steam"

    # For T,P or property-based inputs, ask CoolProp
    # Need T and P to determine phase
    try:
        T_K = PropsSI("T", in1_name, in1_val, in2_name, in2_val, fluid)
        P_Pa = PropsSI("P", in1_name, in1_val, in2_name, in2_val, fluid)
        phase_idx = int(PropsSI("Phase", "T", T_K, "P", P_Pa, fluid))
        raw = PHASE_MAP.get(phase_idx, f"unknown_{phase_idx}")
        return _normalize_phase(raw)
    except Exception:
        # Fallback: check if in two-phase region
        try:
            Q = PropsSI("Q", in1_name, in1_val, in2_name, in2_val, fluid)
            if 0 < Q < 1:
                return "wet_steam"
        except Exception:
            pass
        return "unknown"


def cross_verify(given: dict, computed: dict, fluid: str = "Water",
                  tol_pct: float = 0.01) -> bool:
    """
    Cross-verify computed properties by inverse lookup.
    Returns True if all verifications pass within tolerance.
    """
    # For states with T and P, verify h by computing from T,P
    if "T_C" in computed and "P_kPa" in computed:
        T_K = _to_K(computed["T_C"]["value"])
        P_Pa = _to_Pa(computed["P_kPa"]["value"])
        if "h_kJ_kg" in computed:
            h_check = PropsSI("H", "T", T_K, "P", P_Pa, fluid) / 1000
            if abs(h_check - computed["h_kJ_kg"]["value"]) / max(abs(h_check), 1) > tol_pct / 100:
                return False

    # For states with known h, verify temperature
    if "h_kJ_kg" in given and "T_C" in computed:
        in1, v1, in2, v2 = _resolve_inputs(given)
        T_check = PropsSI("T", in1, v1, in2, v2, fluid)
        if abs(_to_C(T_check) - computed["T_C"]["value"]) > 0.5:
            return False

    return True
