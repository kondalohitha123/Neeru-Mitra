"""Water Stress Score: combines weather and ground conditions into 0-100."""

# How much each factor contributes (adds up to 1.0). Adjustable assumptions.
WEIGHTS = {"rain": 0.25, "heat": 0.20, "groundwater": 0.30, "reservoir": 0.25}

# Scales calibrated to Telangana groundwater data (depths of about 4-14 m).
GROUNDWATER_MAX_M = 15
HEAT_MIN_C, HEAT_MAX_C = 28, 42


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def stress_level(score: float) -> str:
    if score >= 70:
        return "Critical"
    if score >= 50:
        return "High"
    if score >= 30:
        return "Moderate"
    return "Low"


def compute_stress(rain_past_mm, normal_rain_mm, avg_tmax_c,
                   groundwater_depth_m, reservoir_pct) -> float:
    """Each factor is scaled to 0-100, then combined using WEIGHTS."""
    rain_deficit = _clamp(1 - rain_past_mm / normal_rain_mm) * 100 if normal_rain_mm else 0
    heat = _clamp((avg_tmax_c - HEAT_MIN_C) / (HEAT_MAX_C - HEAT_MIN_C)) * 100
    groundwater = _clamp(groundwater_depth_m / GROUNDWATER_MAX_M) * 100
    reservoir = _clamp((100 - reservoir_pct) / 100) * 100

    score = (
        WEIGHTS["rain"] * rain_deficit
        + WEIGHTS["heat"] * heat
        + WEIGHTS["groundwater"] * groundwater
        + WEIGHTS["reservoir"] * reservoir
    )
    return round(score, 1)