"""
ThermoQA Tier 3 — Cycle State Generator

Generates physically valid state points for complete thermodynamic cycles.
Uses CoolProp for Water/R-134a, analytical equations for Air (ideal gas).

Each cycle generator returns a dict with:
  - states: {1: {T, P, h, s, ...}, 2: {...}, ...}
  - params: original input parameters
  - derived: component-level quantities (w_pump, q_in, etc.)
  - meta: {cycle_type, fluid, is_valid, validation_notes}
"""

import CoolProp.CoolProp as CP
import math
from dataclasses import dataclass, field
from typing import Optional

# =============================================================================
# Constants
# =============================================================================
T0_K = 298.15    # Dead state temperature (25°C)
P0_Pa = 100000   # Dead state pressure (0.1 MPa = 100 kPa)
P0_kPa = 100.0
P0_MPa = 0.1

# Air (ideal gas, constant specific heats)
AIR_CP = 1.005   # kJ/(kg·K)
AIR_CV = 0.718
AIR_K = 1.4
AIR_R = 0.287    # kJ/(kg·K)


# =============================================================================
# Dead state properties
# =============================================================================
def get_dead_state(fluid: str) -> dict:
    """Get dead state properties for a fluid."""
    if fluid == "Water":
        h0 = CP.PropsSI("H", "T", T0_K, "P", P0_Pa, "Water") / 1000  # kJ/kg
        s0 = CP.PropsSI("S", "T", T0_K, "P", P0_Pa, "Water") / 1000  # kJ/(kg·K)
        return {"h0": h0, "s0": s0, "T0_K": T0_K, "P0_kPa": P0_kPa}
    elif fluid == "Air":
        h0 = AIR_CP * T0_K  # kJ/kg
        s0 = 0.0  # reference
        return {"h0": h0, "s0": s0, "T0_K": T0_K, "P0_kPa": P0_kPa}
    elif fluid == "R-134a":
        h0 = CP.PropsSI("H", "T", T0_K, "P", P0_Pa, "R134a") / 1000
        s0 = CP.PropsSI("S", "T", T0_K, "P", P0_Pa, "R134a") / 1000
        return {"h0": h0, "s0": s0, "T0_K": T0_K, "P0_kPa": P0_kPa}
    else:
        raise ValueError(f"Unknown fluid: {fluid}")


def flow_exergy(h, s, h0, s0):
    """Specific flow exergy: ef = (h - h0) - T0*(s - s0) [kJ/kg]"""
    return (h - h0) - T0_K * (s - s0)


# =============================================================================
# CoolProp helpers
# =============================================================================
def water_props(T_C=None, P_kPa=None, s_kJkgK=None, h_kJkg=None, Q=None):
    """Get water properties from CoolProp. Returns dict with h, s, T, P, v, x."""
    P_Pa = P_kPa * 1000 if P_kPa is not None else None
    
    if T_C is not None and P_Pa is not None:
        T_K = T_C + 273.15
        h = CP.PropsSI("H", "T", T_K, "P", P_Pa, "Water") / 1000
        s = CP.PropsSI("S", "T", T_K, "P", P_Pa, "Water") / 1000
        v = 1.0 / CP.PropsSI("D", "T", T_K, "P", P_Pa, "Water")
        phase = CP.PhaseSI("T", T_K, "P", P_Pa, "Water")
        x = None if "two" not in phase.lower() else CP.PropsSI("Q", "T", T_K, "P", P_Pa, "Water")
        return {"T_C": T_C, "T_K": T_K, "P_kPa": P_kPa, "h": h, "s": s, "v": v, "x": x}
    
    elif s_kJkgK is not None and P_Pa is not None:
        s_SI = s_kJkgK * 1000
        h = CP.PropsSI("H", "S", s_SI, "P", P_Pa, "Water") / 1000
        T_K = CP.PropsSI("T", "S", s_SI, "P", P_Pa, "Water")
        v = 1.0 / CP.PropsSI("D", "S", s_SI, "P", P_Pa, "Water")
        phase = CP.PhaseSI("S", s_SI, "P", P_Pa, "Water")
        x = None
        if "two" in phase.lower():
            x = CP.PropsSI("Q", "S", s_SI, "P", P_Pa, "Water")
        return {"T_C": T_K - 273.15, "T_K": T_K, "P_kPa": P_kPa, "h": h, "s": s_kJkgK, "v": v, "x": x}
    
    elif Q is not None and P_Pa is not None:
        h = CP.PropsSI("H", "Q", Q, "P", P_Pa, "Water") / 1000
        s = CP.PropsSI("S", "Q", Q, "P", P_Pa, "Water") / 1000
        T_K = CP.PropsSI("T", "Q", Q, "P", P_Pa, "Water")
        v = 1.0 / CP.PropsSI("D", "Q", Q, "P", P_Pa, "Water")
        return {"T_C": T_K - 273.15, "T_K": T_K, "P_kPa": P_kPa, "h": h, "s": s, "v": v, "x": Q}
    
    elif h_kJkg is not None and P_Pa is not None:
        h_SI = h_kJkg * 1000
        s = CP.PropsSI("S", "H", h_SI, "P", P_Pa, "Water") / 1000
        T_K = CP.PropsSI("T", "H", h_SI, "P", P_Pa, "Water")
        v = 1.0 / CP.PropsSI("D", "H", h_SI, "P", P_Pa, "Water")
        phase = CP.PhaseSI("H", h_SI, "P", P_Pa, "Water")
        x = None
        if "two" in phase.lower():
            x = CP.PropsSI("Q", "H", h_SI, "P", P_Pa, "Water")
        return {"T_C": T_K - 273.15, "T_K": T_K, "P_kPa": P_kPa, "h": h_kJkg, "s": s, "v": v, "x": x}
    
    else:
        raise ValueError("Unsupported property combination for water_props")


def r134a_props(T_C=None, P_kPa=None, s_kJkgK=None, h_kJkg=None, Q=None):
    """Get R-134a properties from CoolProp. Same interface as water_props."""
    P_Pa = P_kPa * 1000 if P_kPa is not None else None
    
    if T_C is not None and P_Pa is not None:
        T_K = T_C + 273.15
        h = CP.PropsSI("H", "T", T_K, "P", P_Pa, "R134a") / 1000
        s = CP.PropsSI("S", "T", T_K, "P", P_Pa, "R134a") / 1000
        v = 1.0 / CP.PropsSI("D", "T", T_K, "P", P_Pa, "R134a")
        phase = CP.PhaseSI("T", T_K, "P", P_Pa, "R134a")
        x = None if "two" not in phase.lower() else CP.PropsSI("Q", "T", T_K, "P", P_Pa, "R134a")
        return {"T_C": T_C, "T_K": T_K, "P_kPa": P_kPa, "h": h, "s": s, "v": v, "x": x}
    
    elif s_kJkgK is not None and P_Pa is not None:
        s_SI = s_kJkgK * 1000
        h = CP.PropsSI("H", "S", s_SI, "P", P_Pa, "R134a") / 1000
        T_K = CP.PropsSI("T", "S", s_SI, "P", P_Pa, "R134a")
        v = 1.0 / CP.PropsSI("D", "S", s_SI, "P", P_Pa, "R134a")
        phase = CP.PhaseSI("S", s_SI, "P", P_Pa, "R134a")
        x = None
        if "two" in phase.lower():
            x = CP.PropsSI("Q", "S", s_SI, "P", P_Pa, "R134a")
        return {"T_C": T_K - 273.15, "T_K": T_K, "P_kPa": P_kPa, "h": h, "s": s_kJkgK, "v": v, "x": x}
    
    elif Q is not None and P_Pa is not None:
        h = CP.PropsSI("H", "Q", Q, "P", P_Pa, "R134a") / 1000
        s = CP.PropsSI("S", "Q", Q, "P", P_Pa, "R134a") / 1000
        T_K = CP.PropsSI("T", "Q", Q, "P", P_Pa, "R134a")
        v = 1.0 / CP.PropsSI("D", "Q", Q, "P", P_Pa, "R134a")
        return {"T_C": T_K - 273.15, "T_K": T_K, "P_kPa": P_kPa, "h": h, "s": s, "v": v, "x": Q}
    
    elif h_kJkg is not None and P_Pa is not None:
        h_SI = h_kJkg * 1000
        s = CP.PropsSI("S", "H", h_SI, "P", P_Pa, "R134a") / 1000
        T_K = CP.PropsSI("T", "H", h_SI, "P", P_Pa, "R134a")
        v = 1.0 / CP.PropsSI("D", "H", h_SI, "P", P_Pa, "R134a")
        phase = CP.PhaseSI("H", h_SI, "P", P_Pa, "R134a")
        x = None
        if "two" in phase.lower():
            x = CP.PropsSI("Q", "H", h_SI, "P", P_Pa, "R134a")
        return {"T_C": T_K - 273.15, "T_K": T_K, "P_kPa": P_kPa, "h": h_kJkg, "s": s, "v": v, "x": x}
    
    elif Q is not None and T_C is not None:
        T_K = T_C + 273.15
        P_Pa_sat = CP.PropsSI("P", "T", T_K, "Q", Q, "R134a")
        h = CP.PropsSI("H", "T", T_K, "Q", Q, "R134a") / 1000
        s = CP.PropsSI("S", "T", T_K, "Q", Q, "R134a") / 1000
        v = 1.0 / CP.PropsSI("D", "T", T_K, "Q", Q, "R134a")
        return {"T_C": T_C, "T_K": T_K, "P_kPa": P_Pa_sat / 1000, "h": h, "s": s, "v": v, "x": Q}
    
    else:
        raise ValueError("Unsupported property combination for r134a_props")


# =============================================================================
# Air (ideal gas) helpers
# =============================================================================
def air_state(T_K, P_kPa):
    """Air state from T and P (constant cp ideal gas)."""
    h = AIR_CP * T_K  # kJ/kg
    # s = cp*ln(T/T_ref) - R*ln(P/P_ref), using T_ref=T0, P_ref=P0
    s = AIR_CP * math.log(T_K / T0_K) - AIR_R * math.log(P_kPa / P0_kPa)
    return {"T_K": T_K, "T_C": T_K - 273.15, "P_kPa": P_kPa, "h": h, "s": s}


# =============================================================================
# RANKINE CYCLES
# =============================================================================

def generate_rankine_ideal(params: dict) -> dict:
    """
    Generate Ideal Rankine Cycle states.
    
    params: P_cond_kPa, P_boiler_MPa, T3_C, m_dot_kgs
    Optional for B/C: T_source_K, T_sink_K
    """
    P_low = params["P_cond_kPa"]           # kPa
    P_high = params["P_boiler_MPa"] * 1000  # kPa
    T3 = params["T3_C"]
    m_dot = params["m_dot_kgs"]
    
    # State 1: saturated liquid at P_low
    s1 = water_props(Q=0, P_kPa=P_low)
    s1["state"] = 1
    
    # State 2s = State 2 (ideal pump): isentropic compression
    # CoolProp exact: find h at (s=s1, P=P_high)
    s2 = water_props(s_kJkgK=s1["s"], P_kPa=P_high)
    s2["state"] = 2
    
    # State 3: superheated vapor at (T3, P_high)
    s3 = water_props(T_C=T3, P_kPa=P_high)
    s3["state"] = 3
    
    # State 4s = State 4 (ideal turbine): isentropic expansion
    s4 = water_props(s_kJkgK=s3["s"], P_kPa=P_low)
    s4["state"] = 4
    
    # Derived quantities
    w_pump = s2["h"] - s1["h"]      # kJ/kg (positive = work input)
    q_in = s3["h"] - s2["h"]        # kJ/kg
    w_turb = s3["h"] - s4["h"]      # kJ/kg (positive = work output)
    q_out = s4["h"] - s1["h"]       # kJ/kg (positive = heat rejection)
    w_net = w_turb - w_pump          # kJ/kg
    eta_th = w_net / q_in
    bwr = w_pump / w_turb            # back-work ratio
    
    W_dot_net = m_dot * w_net        # kW
    Q_dot_in = m_dot * q_in          # kW
    Q_dot_out = m_dot * q_out        # kW
    
    states = {1: s1, 2: s2, 3: s3, 4: s4}
    derived = {
        "w_pump": w_pump, "q_in": q_in, "w_turb": w_turb,
        "q_out": q_out, "w_net": w_net, "eta_th": eta_th, "bwr": bwr,
        "W_dot_net": W_dot_net, "Q_dot_in": Q_dot_in, "Q_dot_out": Q_dot_out,
    }
    
    # Entropy generation (ideal: internal components have s_gen=0)
    # External irreversibility at boiler and condenser
    if "T_source_K" in params:
        T_src = params["T_source_K"]
        T_sink = params.get("T_sink_K", s1["T_K"] - 10)  # default: T_sat - 10K (sink cooler than condenser)
        
        s_gen_pump = 0.0  # ideal
        s_gen_boiler = (s3["s"] - s2["s"]) - q_in / T_src
        s_gen_turb = 0.0  # ideal
        s_gen_cond = (s1["s"] - s4["s"]) + q_out / T_sink
        s_gen_total = s_gen_pump + s_gen_boiler + s_gen_turb + s_gen_cond
        
        derived.update({
            "s_gen_pump": s_gen_pump, "s_gen_boiler": s_gen_boiler,
            "s_gen_turb": s_gen_turb, "s_gen_cond": s_gen_cond,
            "s_gen_total": s_gen_total,
            "T_source_K": T_src, "T_sink_K": T_sink,
        })
        
        # Exergy (Depth C)
        ds = get_dead_state("Water")
        for st_key, st in states.items():
            st["ef"] = flow_exergy(st["h"], st["s"], ds["h0"], ds["s0"])
        
        x_dest_pump = T0_K * s_gen_pump
        x_dest_boiler = T0_K * s_gen_boiler
        x_dest_turb = T0_K * s_gen_turb
        x_dest_cond = T0_K * s_gen_cond
        x_dest_total = T0_K * s_gen_total
        
        X_in = Q_dot_in * (1 - T0_K / T_src)  # exergy of heat input
        eta_II = W_dot_net / X_in if X_in > 0 else 0
        
        derived.update({
            "x_dest_pump": x_dest_pump, "x_dest_boiler": x_dest_boiler,
            "x_dest_turb": x_dest_turb, "x_dest_cond": x_dest_cond,
            "x_dest_total": x_dest_total, "eta_II": eta_II,
            "X_dot_in": X_in,
            "X_dot_dest_total": m_dot * x_dest_total,
        })
    
    # Validation
    notes = []
    T_sat_boiler = CP.PropsSI("T", "Q", 0, "P", P_high * 1000, "Water") - 273.15
    if T3 < T_sat_boiler + 20:
        notes.append(f"T3={T3}°C too close to T_sat={T_sat_boiler:.1f}°C at P_boiler")
    if s4.get("x") is not None and s4["x"] < 0.85:
        notes.append(f"x4={s4['x']:.3f} < 0.85 — excessive wetness at turbine exit")
    if w_net <= 0:
        notes.append("w_net <= 0 — cycle produces no net work")
    
    return {
        "states": states,
        "params": params,
        "derived": derived,
        "meta": {
            "cycle_type": "RNK-I",
            "fluid": "Water",
            "is_valid": len(notes) == 0,
            "validation_notes": notes,
        }
    }


def generate_rankine_actual(params: dict) -> dict:
    """
    Generate Actual Rankine Cycle states.
    
    params: P_cond_kPa, P_boiler_MPa, T3_C, eta_pump, eta_turb, m_dot_kgs
    Optional: T_source_K, T_sink_K
    """
    P_low = params["P_cond_kPa"]
    P_high = params["P_boiler_MPa"] * 1000
    T3 = params["T3_C"]
    eta_p = params["eta_pump"]
    eta_t = params["eta_turb"]
    m_dot = params["m_dot_kgs"]
    
    # State 1: sat liquid at P_low
    s1 = water_props(Q=0, P_kPa=P_low)
    s1["state"] = 1
    
    # State 2s: isentropic pump exit
    s2s = water_props(s_kJkgK=s1["s"], P_kPa=P_high)
    s2s["state"] = "2s"
    
    # State 2: actual pump exit
    h2 = s1["h"] + (s2s["h"] - s1["h"]) / eta_p
    s2 = water_props(h_kJkg=h2, P_kPa=P_high)
    s2["state"] = 2
    
    # State 3: superheated at (T3, P_high)
    s3 = water_props(T_C=T3, P_kPa=P_high)
    s3["state"] = 3
    
    # State 4s: isentropic turbine exit
    s4s = water_props(s_kJkgK=s3["s"], P_kPa=P_low)
    s4s["state"] = "4s"
    
    # State 4: actual turbine exit
    h4 = s3["h"] - eta_t * (s3["h"] - s4s["h"])
    s4 = water_props(h_kJkg=h4, P_kPa=P_low)
    s4["state"] = 4
    
    # Derived
    w_pump = s2["h"] - s1["h"]
    w_pump_s = s2s["h"] - s1["h"]
    q_in = s3["h"] - s2["h"]
    w_turb = s3["h"] - s4["h"]
    w_turb_s = s3["h"] - s4s["h"]
    q_out = s4["h"] - s1["h"]
    w_net = w_turb - w_pump
    eta_th = w_net / q_in if q_in > 0 else 0
    bwr = w_pump / w_turb if w_turb > 0 else 0
    
    W_dot_net = m_dot * w_net
    Q_dot_in = m_dot * q_in
    Q_dot_out = m_dot * q_out
    
    states = {1: s1, "2s": s2s, 2: s2, 3: s3, "4s": s4s, 4: s4}
    derived = {
        "w_pump": w_pump, "w_pump_s": w_pump_s,
        "q_in": q_in, "w_turb": w_turb, "w_turb_s": w_turb_s,
        "q_out": q_out, "w_net": w_net, "eta_th": eta_th, "bwr": bwr,
        "W_dot_net": W_dot_net, "Q_dot_in": Q_dot_in, "Q_dot_out": Q_dot_out,
        "h2s": s2s["h"], "h4s": s4s["h"],
    }
    
    # Entropy/exergy analysis
    if "T_source_K" in params:
        T_src = params["T_source_K"]
        T_sink = params.get("T_sink_K", s1["T_K"] - 10)  # sink cooler than condenser

        s_gen_pump = s2["s"] - s1["s"]      # adiabatic pump
        s_gen_boiler = (s3["s"] - s2["s"]) - q_in / T_src
        s_gen_turb = s4["s"] - s3["s"]      # adiabatic turbine (note: s4 > s3)
        s_gen_cond = (s1["s"] - s4["s"]) + q_out / T_sink
        s_gen_total = s_gen_pump + s_gen_boiler + s_gen_turb + s_gen_cond
        
        derived.update({
            "s_gen_pump": s_gen_pump, "s_gen_boiler": s_gen_boiler,
            "s_gen_turb": s_gen_turb, "s_gen_cond": s_gen_cond,
            "s_gen_total": s_gen_total,
            "T_source_K": T_src, "T_sink_K": T_sink,
        })
        
        ds = get_dead_state("Water")
        for st_key, st in states.items():
            st["ef"] = flow_exergy(st["h"], st["s"], ds["h0"], ds["s0"])
        
        x_dest_pump = T0_K * s_gen_pump
        x_dest_boiler = T0_K * s_gen_boiler
        x_dest_turb = T0_K * s_gen_turb
        x_dest_cond = T0_K * s_gen_cond
        x_dest_total = T0_K * s_gen_total
        
        X_in = Q_dot_in * (1 - T0_K / T_src)
        eta_II = W_dot_net / X_in if X_in > 0 else 0
        
        derived.update({
            "x_dest_pump": x_dest_pump, "x_dest_boiler": x_dest_boiler,
            "x_dest_turb": x_dest_turb, "x_dest_cond": x_dest_cond,
            "x_dest_total": x_dest_total, "eta_II": eta_II,
            "X_dot_in": X_in,
            "X_dot_dest_total": m_dot * x_dest_total,
        })
    
    # Validation
    notes = []
    T_sat_boiler = CP.PropsSI("T", "Q", 0, "P", P_high * 1000, "Water") - 273.15
    if T3 < T_sat_boiler + 20:
        notes.append(f"T3={T3}°C too close to T_sat={T_sat_boiler:.1f}°C")
    if s4.get("x") is not None and s4["x"] < 0.85:
        notes.append(f"x4={s4['x']:.3f} < 0.85")
    if s4s.get("x") is not None and s4s["x"] < 0.80:
        notes.append(f"x4s={s4s['x']:.3f} < 0.80")
    if w_net <= 0:
        notes.append("w_net <= 0")
    
    return {
        "states": states,
        "params": params,
        "derived": derived,
        "meta": {
            "cycle_type": "RNK-A",
            "fluid": "Water",
            "is_valid": len(notes) == 0,
            "validation_notes": notes,
        }
    }


def generate_rankine_reheat(params: dict) -> dict:
    """
    Generate Reheat Rankine Cycle states (6 states).
    
    params: P_cond_kPa, P_boiler_MPa, P_reheat_MPa, T3_C, T5_C,
            eta_pump, eta_HPT, eta_LPT, m_dot_kgs
    Optional: T_source_K, T_sink_K
    """
    P_low = params["P_cond_kPa"]
    P_high = params["P_boiler_MPa"] * 1000
    P_rh = params["P_reheat_MPa"] * 1000
    T3 = params["T3_C"]
    T5 = params["T5_C"]
    eta_p = params["eta_pump"]
    eta_hpt = params["eta_HPT"]
    eta_lpt = params["eta_LPT"]
    m_dot = params["m_dot_kgs"]
    
    # State 1: sat liquid at P_low
    s1 = water_props(Q=0, P_kPa=P_low)
    s1["state"] = 1
    
    # State 2s, 2: pump
    s2s = water_props(s_kJkgK=s1["s"], P_kPa=P_high)
    h2 = s1["h"] + (s2s["h"] - s1["h"]) / eta_p
    s2 = water_props(h_kJkg=h2, P_kPa=P_high)
    s2["state"] = 2
    s2s["state"] = "2s"
    
    # State 3: boiler exit / HPT inlet
    s3 = water_props(T_C=T3, P_kPa=P_high)
    s3["state"] = 3
    
    # State 4s, 4: HPT exit
    s4s = water_props(s_kJkgK=s3["s"], P_kPa=P_rh)
    h4 = s3["h"] - eta_hpt * (s3["h"] - s4s["h"])
    s4 = water_props(h_kJkg=h4, P_kPa=P_rh)
    s4["state"] = 4
    s4s["state"] = "4s"
    
    # State 5: reheat exit / LPT inlet
    s5 = water_props(T_C=T5, P_kPa=P_rh)
    s5["state"] = 5
    
    # State 6s, 6: LPT exit
    s6s = water_props(s_kJkgK=s5["s"], P_kPa=P_low)
    h6 = s5["h"] - eta_lpt * (s5["h"] - s6s["h"])
    s6 = water_props(h_kJkg=h6, P_kPa=P_low)
    s6["state"] = 6
    s6s["state"] = "6s"
    
    # Derived
    w_pump = s2["h"] - s1["h"]
    q_in = (s3["h"] - s2["h"]) + (s5["h"] - s4["h"])  # boiler + reheater
    q_boiler = s3["h"] - s2["h"]
    q_reheat = s5["h"] - s4["h"]
    w_HPT = s3["h"] - s4["h"]
    w_LPT = s5["h"] - s6["h"]
    w_turb = w_HPT + w_LPT
    q_out = s6["h"] - s1["h"]
    w_net = w_turb - w_pump
    eta_th = w_net / q_in if q_in > 0 else 0
    
    W_dot_net = m_dot * w_net
    Q_dot_in = m_dot * q_in
    
    states = {1: s1, "2s": s2s, 2: s2, 3: s3, "4s": s4s, 4: s4,
              5: s5, "6s": s6s, 6: s6}
    derived = {
        "w_pump": w_pump, "q_boiler": q_boiler, "q_reheat": q_reheat,
        "q_in": q_in, "w_HPT": w_HPT, "w_LPT": w_LPT, "w_turb": w_turb,
        "q_out": q_out, "w_net": w_net, "eta_th": eta_th,
        "W_dot_net": W_dot_net, "Q_dot_in": Q_dot_in,
        "h2s": s2s["h"], "h4s": s4s["h"], "h6s": s6s["h"],
    }
    
    # Entropy/exergy
    if "T_source_K" in params:
        T_src = params["T_source_K"]
        T_sink = params.get("T_sink_K", s1["T_K"] - 10)  # sink cooler than condenser

        s_gen_pump = s2["s"] - s1["s"]
        s_gen_boiler = (s3["s"] - s2["s"]) - q_boiler / T_src
        s_gen_HPT = s4["s"] - s3["s"]
        s_gen_reheater = (s5["s"] - s4["s"]) - q_reheat / T_src  # same source
        s_gen_LPT = s6["s"] - s5["s"]
        s_gen_cond = (s1["s"] - s6["s"]) + q_out / T_sink
        s_gen_total = (s_gen_pump + s_gen_boiler + s_gen_HPT +
                       s_gen_reheater + s_gen_LPT + s_gen_cond)
        
        derived.update({
            "s_gen_pump": s_gen_pump, "s_gen_boiler": s_gen_boiler,
            "s_gen_HPT": s_gen_HPT, "s_gen_reheater": s_gen_reheater,
            "s_gen_LPT": s_gen_LPT, "s_gen_cond": s_gen_cond,
            "s_gen_total": s_gen_total,
            "T_source_K": T_src, "T_sink_K": T_sink,
        })
        
        ds = get_dead_state("Water")
        for st_key, st in states.items():
            st["ef"] = flow_exergy(st["h"], st["s"], ds["h0"], ds["s0"])
        
        x_dest_pump = T0_K * s_gen_pump
        x_dest_boiler = T0_K * s_gen_boiler
        x_dest_HPT = T0_K * s_gen_HPT
        x_dest_reheater = T0_K * s_gen_reheater
        x_dest_LPT = T0_K * s_gen_LPT
        x_dest_cond = T0_K * s_gen_cond
        x_dest_total = T0_K * s_gen_total
        
        X_in = Q_dot_in * (1 - T0_K / T_src)
        eta_II = W_dot_net / X_in if X_in > 0 else 0
        
        derived.update({
            "x_dest_pump": x_dest_pump, "x_dest_boiler": x_dest_boiler,
            "x_dest_HPT": x_dest_HPT, "x_dest_reheater": x_dest_reheater,
            "x_dest_LPT": x_dest_LPT, "x_dest_cond": x_dest_cond,
            "x_dest_total": x_dest_total, "eta_II": eta_II,
            "X_dot_in": X_in,
            "X_dot_dest_total": m_dot * x_dest_total,
        })
    
    # Validation
    notes = []
    T_sat_boiler = CP.PropsSI("T", "Q", 0, "P", P_high * 1000, "Water") - 273.15
    T_sat_reheat = CP.PropsSI("T", "Q", 0, "P", P_rh * 1000, "Water") - 273.15
    if T3 < T_sat_boiler + 20:
        notes.append(f"T3={T3}°C too close to T_sat={T_sat_boiler:.1f}°C")
    if T5 < T_sat_reheat + 20:
        notes.append(f"T5={T5}°C too close to T_sat(P_rh)={T_sat_reheat:.1f}°C")
    if P_rh >= P_high:
        notes.append(f"P_reheat={P_rh} kPa >= P_boiler={P_high} kPa")
    if P_rh <= P_low:
        notes.append(f"P_reheat={P_rh} kPa <= P_cond={P_low} kPa")
    if s6.get("x") is not None and s6["x"] < 0.85:
        notes.append(f"x6={s6['x']:.3f} < 0.85")
    if w_net <= 0:
        notes.append("w_net <= 0")
    
    return {
        "states": states, "params": params, "derived": derived,
        "meta": {
            "cycle_type": "RNK-RH", "fluid": "Water",
            "is_valid": len(notes) == 0, "validation_notes": notes,
        }
    }


# =============================================================================
# BRAYTON CYCLES
# =============================================================================

def generate_brayton_ideal(params: dict) -> dict:
    """
    Ideal Brayton Cycle (constant cp air).
    
    params: T1_K, P1_kPa, r_p, T3_K, m_dot_kgs
    Optional: T_source_K, T_sink_K
    """
    T1 = params["T1_K"]
    P1 = params["P1_kPa"]
    r_p = params["r_p"]
    T3 = params["T3_K"]
    m_dot = params["m_dot_kgs"]
    
    P2 = P1 * r_p
    
    # State 1: compressor inlet
    s1_d = air_state(T1, P1)
    s1_d["state"] = 1
    
    # State 2: isentropic compression
    T2 = T1 * r_p ** ((AIR_K - 1) / AIR_K)
    s2_d = air_state(T2, P2)
    s2_d["state"] = 2
    
    # State 3: turbine inlet (after combustion)
    s3_d = air_state(T3, P2)
    s3_d["state"] = 3
    
    # State 4: isentropic expansion
    T4 = T3 / r_p ** ((AIR_K - 1) / AIR_K)
    s4_d = air_state(T4, P1)
    s4_d["state"] = 4
    
    # Derived
    w_comp = s2_d["h"] - s1_d["h"]      # = cp*(T2-T1)
    q_in = s3_d["h"] - s2_d["h"]        # = cp*(T3-T2)
    w_turb = s3_d["h"] - s4_d["h"]      # = cp*(T3-T4)
    q_out = s4_d["h"] - s1_d["h"]       # = cp*(T4-T1)
    w_net = w_turb - w_comp
    eta_th = w_net / q_in if q_in > 0 else 0
    # Also: eta_th = 1 - 1/r_p^((k-1)/k)
    eta_th_formula = 1 - 1 / r_p ** ((AIR_K - 1) / AIR_K)
    bwr = w_comp / w_turb
    
    W_dot_net = m_dot * w_net
    Q_dot_in = m_dot * q_in
    
    states = {1: s1_d, 2: s2_d, 3: s3_d, 4: s4_d}
    derived = {
        "w_comp": w_comp, "q_in": q_in, "w_turb": w_turb,
        "q_out": q_out, "w_net": w_net, "eta_th": eta_th,
        "eta_th_formula": eta_th_formula, "bwr": bwr,
        "W_dot_net": W_dot_net, "Q_dot_in": Q_dot_in,
        "P2_kPa": P2, "T2_K": T2, "T4_K": T4,
    }
    
    # Entropy/exergy
    if "T_source_K" in params:
        T_src = params["T_source_K"]
        T_sink = params.get("T_sink_K", T1 + 10)
        
        s_gen_comp = 0.0  # ideal
        s_gen_cc = (s3_d["s"] - s2_d["s"]) - q_in / T_src
        s_gen_turb = 0.0  # ideal
        s_gen_hr = (s1_d["s"] - s4_d["s"]) + q_out / T_sink  # heat rejection
        s_gen_total = s_gen_comp + s_gen_cc + s_gen_turb + s_gen_hr
        
        derived.update({
            "s_gen_comp": s_gen_comp, "s_gen_cc": s_gen_cc,
            "s_gen_turb": s_gen_turb, "s_gen_hr": s_gen_hr,
            "s_gen_total": s_gen_total,
            "T_source_K": T_src, "T_sink_K": T_sink,
        })
        
        ds = get_dead_state("Air")
        for st_key, st in states.items():
            st["ef"] = flow_exergy(st["h"], st["s"], ds["h0"], ds["s0"])
        
        x_dest_comp = T0_K * s_gen_comp
        x_dest_cc = T0_K * s_gen_cc
        x_dest_turb = T0_K * s_gen_turb
        x_dest_hr = T0_K * s_gen_hr
        x_dest_total = T0_K * s_gen_total
        
        X_in = Q_dot_in * (1 - T0_K / T_src)
        eta_II = W_dot_net / X_in if X_in > 0 else 0
        
        derived.update({
            "x_dest_comp": x_dest_comp, "x_dest_cc": x_dest_cc,
            "x_dest_turb": x_dest_turb, "x_dest_hr": x_dest_hr,
            "x_dest_total": x_dest_total, "eta_II": eta_II,
            "X_dot_in": X_in,
        })
    
    notes = []
    if T3 <= T2:
        notes.append(f"T3={T3}K <= T2={T2:.1f}K — no combustion possible")
    if T4 <= T1:
        notes.append(f"T4={T4:.1f}K <= T1={T1}K")
    if w_net <= 0:
        notes.append("w_net <= 0")
    
    return {
        "states": states, "params": params, "derived": derived,
        "meta": {
            "cycle_type": "BRY-I", "fluid": "Air",
            "is_valid": len(notes) == 0, "validation_notes": notes,
        }
    }


def generate_brayton_actual(params: dict) -> dict:
    """
    Actual Brayton Cycle (constant cp air with isentropic efficiencies).
    
    params: T1_K, P1_kPa, r_p, T3_K, eta_comp, eta_turb, m_dot_kgs
    """
    T1 = params["T1_K"]
    P1 = params["P1_kPa"]
    r_p = params["r_p"]
    T3 = params["T3_K"]
    eta_c = params["eta_comp"]
    eta_t = params["eta_turb"]
    m_dot = params["m_dot_kgs"]
    
    P2 = P1 * r_p
    
    # State 1
    s1_d = air_state(T1, P1)
    s1_d["state"] = 1
    
    # State 2s: isentropic
    T2s = T1 * r_p ** ((AIR_K - 1) / AIR_K)
    s2s_d = air_state(T2s, P2)
    s2s_d["state"] = "2s"
    
    # State 2: actual compressor
    h2 = s1_d["h"] + (s2s_d["h"] - s1_d["h"]) / eta_c
    T2 = h2 / AIR_CP
    s2_d = air_state(T2, P2)
    s2_d["state"] = 2
    
    # State 3
    s3_d = air_state(T3, P2)
    s3_d["state"] = 3
    
    # State 4s: isentropic
    T4s = T3 / r_p ** ((AIR_K - 1) / AIR_K)
    s4s_d = air_state(T4s, P1)
    s4s_d["state"] = "4s"
    
    # State 4: actual turbine
    h4 = s3_d["h"] - eta_t * (s3_d["h"] - s4s_d["h"])
    T4 = h4 / AIR_CP
    s4_d = air_state(T4, P1)
    s4_d["state"] = 4
    
    # Derived
    w_comp = s2_d["h"] - s1_d["h"]
    w_comp_s = s2s_d["h"] - s1_d["h"]
    q_in = s3_d["h"] - s2_d["h"]
    w_turb = s3_d["h"] - s4_d["h"]
    w_turb_s = s3_d["h"] - s4s_d["h"]
    q_out = s4_d["h"] - s1_d["h"]
    w_net = w_turb - w_comp
    eta_th = w_net / q_in if q_in > 0 else 0
    bwr = w_comp / w_turb if w_turb > 0 else 0
    
    W_dot_net = m_dot * w_net
    Q_dot_in = m_dot * q_in
    
    states = {1: s1_d, "2s": s2s_d, 2: s2_d, 3: s3_d, "4s": s4s_d, 4: s4_d}
    derived = {
        "w_comp": w_comp, "w_comp_s": w_comp_s,
        "q_in": q_in, "w_turb": w_turb, "w_turb_s": w_turb_s,
        "q_out": q_out, "w_net": w_net, "eta_th": eta_th, "bwr": bwr,
        "W_dot_net": W_dot_net, "Q_dot_in": Q_dot_in,
        "P2_kPa": P2, "T2s_K": T2s, "T2_K": T2, "T4s_K": T4s, "T4_K": T4,
        "h2s": s2s_d["h"], "h4s": s4s_d["h"],
    }
    
    # Entropy/exergy
    if "T_source_K" in params:
        T_src = params["T_source_K"]
        T_sink = params.get("T_sink_K", T1 + 10)
        
        s_gen_comp = s2_d["s"] - s1_d["s"]  # >0 for actual
        s_gen_cc = (s3_d["s"] - s2_d["s"]) - q_in / T_src
        s_gen_turb = s4_d["s"] - s3_d["s"]  # >0 for actual
        s_gen_hr = (s1_d["s"] - s4_d["s"]) + q_out / T_sink
        s_gen_total = s_gen_comp + s_gen_cc + s_gen_turb + s_gen_hr
        
        derived.update({
            "s_gen_comp": s_gen_comp, "s_gen_cc": s_gen_cc,
            "s_gen_turb": s_gen_turb, "s_gen_hr": s_gen_hr,
            "s_gen_total": s_gen_total,
            "T_source_K": T_src, "T_sink_K": T_sink,
        })
        
        ds = get_dead_state("Air")
        for st_key, st in states.items():
            st["ef"] = flow_exergy(st["h"], st["s"], ds["h0"], ds["s0"])
        
        x_dest_comp = T0_K * s_gen_comp
        x_dest_cc = T0_K * s_gen_cc
        x_dest_turb = T0_K * s_gen_turb
        x_dest_hr = T0_K * s_gen_hr
        x_dest_total = T0_K * s_gen_total
        
        X_in = Q_dot_in * (1 - T0_K / T_src)
        eta_II = W_dot_net / X_in if X_in > 0 else 0
        
        derived.update({
            "x_dest_comp": x_dest_comp, "x_dest_cc": x_dest_cc,
            "x_dest_turb": x_dest_turb, "x_dest_hr": x_dest_hr,
            "x_dest_total": x_dest_total, "eta_II": eta_II,
            "X_dot_in": X_in,
        })
    
    notes = []
    if T3 <= T2:
        notes.append(f"T3={T3}K <= T2={T2:.1f}K")
    if w_net <= 0:
        notes.append("w_net <= 0 — turbine work doesn't exceed compressor work")
    
    return {
        "states": states, "params": params, "derived": derived,
        "meta": {
            "cycle_type": "BRY-A", "fluid": "Air",
            "is_valid": len(notes) == 0, "validation_notes": notes,
        }
    }


def generate_brayton_regenerative(params: dict) -> dict:
    """
    Regenerative Brayton Cycle (constant cp air).
    States: 1-comp inlet, 2-comp exit, 3-regen cold exit, 4-turb inlet, 5-turb exit, 6-regen hot exit
    
    params: T1_K, P1_kPa, r_p, T4_K, eta_comp, eta_turb, epsilon_regen, m_dot_kgs
    """
    T1 = params["T1_K"]
    P1 = params["P1_kPa"]
    r_p = params["r_p"]
    T4 = params["T4_K"]      # turbine inlet temp (state 4 in regen numbering)
    eta_c = params["eta_comp"]
    eta_t = params["eta_turb"]
    eps = params["epsilon_regen"]
    m_dot = params["m_dot_kgs"]
    
    P2 = P1 * r_p
    
    # State 1: compressor inlet
    s1_d = air_state(T1, P1)
    s1_d["state"] = 1
    
    # State 2s: isentropic compressor
    T2s = T1 * r_p ** ((AIR_K - 1) / AIR_K)
    s2s_d = air_state(T2s, P2)
    s2s_d["state"] = "2s"
    
    # State 2: actual compressor
    h2 = s1_d["h"] + (s2s_d["h"] - s1_d["h"]) / eta_c
    T2 = h2 / AIR_CP
    s2_d = air_state(T2, P2)
    s2_d["state"] = 2
    
    # State 4: turbine inlet (CC exit)
    s4_d = air_state(T4, P2)
    s4_d["state"] = 4
    
    # State 5s: isentropic turbine
    T5s = T4 / r_p ** ((AIR_K - 1) / AIR_K)
    s5s_d = air_state(T5s, P1)
    s5s_d["state"] = "5s"
    
    # State 5: actual turbine exit
    h5 = s4_d["h"] - eta_t * (s4_d["h"] - s5s_d["h"])
    T5 = h5 / AIR_CP
    s5_d = air_state(T5, P1)
    s5_d["state"] = 5
    
    # State 3: regenerator cold exit (preheated air to CC)
    # ε = (T3 - T2) / (T5 - T2)
    T3 = T2 + eps * (T5 - T2)
    s3_d = air_state(T3, P2)  # ~P2 (slight pressure drop ignored)
    s3_d["state"] = 3
    
    # State 6: regenerator hot exit (cooled exhaust)
    # Energy balance: T6 = T5 - (T3 - T2)
    T6 = T5 - (T3 - T2)
    s6_d = air_state(T6, P1)
    s6_d["state"] = 6
    
    # Derived
    w_comp = s2_d["h"] - s1_d["h"]
    q_in = s4_d["h"] - s3_d["h"]      # CC heat input (reduced by regen)
    q_regen = s3_d["h"] - s2_d["h"]   # heat recovered in regen
    w_turb = s4_d["h"] - s5_d["h"]
    q_out = s6_d["h"] - s1_d["h"]     # heat rejection (reduced by regen)
    w_net = w_turb - w_comp
    eta_th = w_net / q_in if q_in > 0 else 0
    bwr = w_comp / w_turb if w_turb > 0 else 0
    
    W_dot_net = m_dot * w_net
    Q_dot_in = m_dot * q_in
    
    states = {1: s1_d, "2s": s2s_d, 2: s2_d, 3: s3_d, 4: s4_d,
              "5s": s5s_d, 5: s5_d, 6: s6_d}
    derived = {
        "w_comp": w_comp, "q_in": q_in, "q_regen": q_regen,
        "w_turb": w_turb, "q_out": q_out, "w_net": w_net,
        "eta_th": eta_th, "bwr": bwr,
        "W_dot_net": W_dot_net, "Q_dot_in": Q_dot_in,
        "P2_kPa": P2, "T2s_K": T2s, "T2_K": T2, "T3_K": T3,
        "T5s_K": T5s, "T5_K": T5, "T6_K": T6,
        "h2s": s2s_d["h"], "h5s": s5s_d["h"],
    }
    
    # Entropy/exergy
    if "T_source_K" in params:
        T_src = params["T_source_K"]
        T_sink = params.get("T_sink_K", T1 + 10)
        
        s_gen_comp = s2_d["s"] - s1_d["s"]
        s_gen_regen = (s3_d["s"] - s2_d["s"]) + (s6_d["s"] - s5_d["s"])  # both sides
        s_gen_cc = (s4_d["s"] - s3_d["s"]) - q_in / T_src
        s_gen_turb = s5_d["s"] - s4_d["s"]
        s_gen_hr = (s1_d["s"] - s6_d["s"]) + q_out / T_sink
        s_gen_total = s_gen_comp + s_gen_regen + s_gen_cc + s_gen_turb + s_gen_hr
        
        derived.update({
            "s_gen_comp": s_gen_comp, "s_gen_regen": s_gen_regen,
            "s_gen_cc": s_gen_cc, "s_gen_turb": s_gen_turb,
            "s_gen_hr": s_gen_hr, "s_gen_total": s_gen_total,
            "T_source_K": T_src, "T_sink_K": T_sink,
        })
        
        ds = get_dead_state("Air")
        for st_key, st in states.items():
            st["ef"] = flow_exergy(st["h"], st["s"], ds["h0"], ds["s0"])
        
        x_dest_comp = T0_K * s_gen_comp
        x_dest_regen = T0_K * s_gen_regen
        x_dest_cc = T0_K * s_gen_cc
        x_dest_turb = T0_K * s_gen_turb
        x_dest_hr = T0_K * s_gen_hr
        x_dest_total = T0_K * s_gen_total
        
        X_in = Q_dot_in * (1 - T0_K / T_src)
        eta_II = W_dot_net / X_in if X_in > 0 else 0
        
        derived.update({
            "x_dest_comp": x_dest_comp, "x_dest_regen": x_dest_regen,
            "x_dest_cc": x_dest_cc, "x_dest_turb": x_dest_turb,
            "x_dest_hr": x_dest_hr, "x_dest_total": x_dest_total,
            "eta_II": eta_II, "X_dot_in": X_in,
        })
    
    notes = []
    if T5 <= T2:
        notes.append(f"T5={T5:.1f}K <= T2={T2:.1f}K — regenerator impossible (exhaust cooler than compressor exit)")
    if T3 > T5:
        notes.append(f"T3={T3:.1f}K > T5={T5:.1f}K — violates second law")
    if T6 < T2:
        notes.append(f"T6={T6:.1f}K < T2={T2:.1f}K — violates energy balance")
    if T6 < T1:
        notes.append(f"T6={T6:.1f}K < T1={T1}K — exhaust below ambient")
    if w_net <= 0:
        notes.append("w_net <= 0")
    
    return {
        "states": states, "params": params, "derived": derived,
        "meta": {
            "cycle_type": "BRY-RG", "fluid": "Air",
            "is_valid": len(notes) == 0, "validation_notes": notes,
        }
    }


# =============================================================================
# VCR CYCLE
# =============================================================================

def generate_vcr_actual(params: dict) -> dict:
    """
    Actual Vapor-Compression Refrigeration Cycle (R-134a).
    
    params: T_evap_C, T_cond_C, eta_comp, m_dot_kgs
    Optional for B/C: T_H_K, T_L_K
    """
    T_evap = params["T_evap_C"]
    T_cond = params["T_cond_C"]
    eta_c = params["eta_comp"]
    m_dot = params["m_dot_kgs"]
    
    # Saturation pressures
    P_evap_Pa = CP.PropsSI("P", "T", T_evap + 273.15, "Q", 0, "R134a")
    P_cond_Pa = CP.PropsSI("P", "T", T_cond + 273.15, "Q", 0, "R134a")
    P_evap = P_evap_Pa / 1000  # kPa
    P_cond = P_cond_Pa / 1000  # kPa
    
    # State 1: sat vapor at evaporator
    s1 = r134a_props(Q=1, T_C=T_evap)
    s1["state"] = 1
    
    # State 2s: isentropic compression
    s2s = r134a_props(s_kJkgK=s1["s"], P_kPa=P_cond)
    s2s["state"] = "2s"
    
    # State 2: actual compression
    h2 = s1["h"] + (s2s["h"] - s1["h"]) / eta_c
    s2 = r134a_props(h_kJkg=h2, P_kPa=P_cond)
    s2["state"] = 2
    
    # State 3: sat liquid at condenser
    s3 = r134a_props(Q=0, T_C=T_cond)
    s3["state"] = 3
    
    # State 4: throttle exit (isenthalpic, h4 = h3)
    h4 = s3["h"]
    # At P_evap, this is a wet mixture
    s4 = r134a_props(h_kJkg=h4, P_kPa=P_evap)
    s4["state"] = 4
    
    # Calculate x4 explicitly
    h_f_evap = CP.PropsSI("H", "Q", 0, "P", P_evap_Pa, "R134a") / 1000
    h_g_evap = CP.PropsSI("H", "Q", 1, "P", P_evap_Pa, "R134a") / 1000
    h_fg = h_g_evap - h_f_evap
    x4 = (h4 - h_f_evap) / h_fg
    s4["x"] = x4
    
    # Derived
    w_comp = s2["h"] - s1["h"]       # kJ/kg (work input to compressor)
    w_comp_s = s2s["h"] - s1["h"]
    q_L = s1["h"] - s4["h"]          # kJ/kg (cooling effect = evaporator heat)
    q_H = s2["h"] - s3["h"]          # kJ/kg (condenser heat rejection)
    COP_R = q_L / w_comp if w_comp > 0 else 0
    
    W_dot_comp = m_dot * w_comp      # kW
    Q_dot_L = m_dot * q_L            # kW
    Q_dot_H = m_dot * q_H            # kW
    
    states = {1: s1, "2s": s2s, 2: s2, 3: s3, 4: s4}
    derived = {
        "P_evap_kPa": P_evap, "P_cond_kPa": P_cond,
        "w_comp": w_comp, "w_comp_s": w_comp_s,
        "q_L": q_L, "q_H": q_H, "x4": x4,
        "COP_R": COP_R,
        "W_dot_comp": W_dot_comp, "Q_dot_L": Q_dot_L, "Q_dot_H": Q_dot_H,
        "h2s": s2s["h"],
    }
    
    # Entropy/exergy
    if "T_H_K" in params or "T_L_K" in params:
        T_H = params.get("T_H_K", T_cond + 273.15 + 10)
        T_L = params.get("T_L_K", T_evap + 273.15 + 5)
        
        # Entropy gen per component (all specific, kJ/(kg·K))
        s_gen_comp = s2["s"] - s1["s"]          # adiabatic compressor
        s_gen_cond = (s3["s"] - s2["s"]) + q_H / T_H    # heat rejection to T_H
        s_gen_throttle = s4["s"] - s3["s"]       # isenthalpic, no heat transfer
        s_gen_evap = (s1["s"] - s4["s"]) - q_L / T_L    # heat absorption from T_L
        s_gen_total = s_gen_comp + s_gen_cond + s_gen_throttle + s_gen_evap
        
        derived.update({
            "s_gen_comp": s_gen_comp, "s_gen_cond": s_gen_cond,
            "s_gen_throttle": s_gen_throttle, "s_gen_evap": s_gen_evap,
            "s_gen_total": s_gen_total,
            "T_H_K": T_H, "T_L_K": T_L,
        })
        
        # Exergy
        ds = get_dead_state("R-134a")
        for st_key, st in states.items():
            st["ef"] = flow_exergy(st["h"], st["s"], ds["h0"], ds["s0"])
        
        x_dest_comp = T0_K * s_gen_comp
        x_dest_cond = T0_K * s_gen_cond
        x_dest_throttle = T0_K * s_gen_throttle
        x_dest_evap = T0_K * s_gen_evap
        x_dest_total = T0_K * s_gen_total
        
        # COP_Carnot for VCR
        COP_Carnot = T_L / (T_H - T_L) if T_H > T_L else 0
        eta_II = COP_R / COP_Carnot if COP_Carnot > 0 else 0
        
        X_dot_dest_total = m_dot * x_dest_total
        
        derived.update({
            "x_dest_comp": x_dest_comp, "x_dest_cond": x_dest_cond,
            "x_dest_throttle": x_dest_throttle, "x_dest_evap": x_dest_evap,
            "x_dest_total": x_dest_total,
            "COP_Carnot": COP_Carnot, "eta_II": eta_II,
            "X_dot_dest_total": X_dot_dest_total,
        })
    
    # Validation
    notes = []
    if T_cond <= T_evap + 20:
        notes.append(f"T_cond={T_cond}°C - T_evap={T_evap}°C = {T_cond-T_evap}°C < 20°C — too small lift")
    if x4 <= 0 or x4 >= 1:
        notes.append(f"x4={x4:.3f} outside (0,1) — throttle exit not wet mixture")
    if w_comp <= 0:
        notes.append("w_comp <= 0")
    if P_cond > 3500:
        notes.append(f"P_cond={P_cond:.0f} kPa > 3500 — near R-134a critical pressure")
    # Check compressor exit temperature is reasonable
    if s2["T_C"] > 90:
        notes.append(f"T2={s2['T_C']:.1f}°C > 90°C — very high compressor discharge (near R-134a Tc=101°C)")
    
    return {
        "states": states, "params": params, "derived": derived,
        "meta": {
            "cycle_type": "VCR-A", "fluid": "R-134a",
            "is_valid": len(notes) == 0, "validation_notes": notes,
        }
    }


# =============================================================================
# DISPATCH
# =============================================================================

CYCLE_GENERATORS = {
    "RNK-I": generate_rankine_ideal,
    "RNK-A": generate_rankine_actual,
    "RNK-RH": generate_rankine_reheat,
    "BRY-I": generate_brayton_ideal,
    "BRY-A": generate_brayton_actual,
    "BRY-RG": generate_brayton_regenerative,
    "VCR-A": generate_vcr_actual,
}


def generate_cycle(cycle_type: str, params: dict) -> dict:
    """Generate a complete cycle with all state points and derived quantities."""
    if cycle_type not in CYCLE_GENERATORS:
        raise ValueError(f"Unknown cycle type: {cycle_type}. Available: {list(CYCLE_GENERATORS.keys())}")
    return CYCLE_GENERATORS[cycle_type](params)
