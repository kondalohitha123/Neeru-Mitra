"""Estimate tanker demand per district and share a limited fleet fairly."""
import math
import pandas as pd

LITRES_PER_PERSON_PER_DAY = 55   # drinking and domestic water norm (adjustable)
TANKER_CAPACITY_L = 10_000       # litres per tanker trip
MAX_TANKER_SHARE = 0.02          # at stress=100, 2% of daily demand needs tankers


def estimate_need(population: int, stress: float) -> int:
    """Tankers per day needed to cover the estimated shortfall."""
    demand = population * LITRES_PER_PERSON_PER_DAY
    shortfall = demand * (stress / 100) * MAX_TANKER_SHARE
    return math.ceil(shortfall / TANKER_CAPACITY_L)


def allocate_tankers(df: pd.DataFrame, fleet_size: int) -> pd.DataFrame:
    """Share the fleet in proportion to need x stress, never above a district's need.

    Tankers left over after rounding go to the most stressed districts
    that still have unmet need.
    """
    out = df.copy()
    out["priority"] = out["tankers_needed"] * out["stress"]
    total_priority = out["priority"].sum()

    if total_priority == 0:
        out["tankers_allocated"] = 0
    else:
        share = (out["priority"] / total_priority * fleet_size).astype(int)
        out["tankers_allocated"] = share.clip(upper=out["tankers_needed"])

    leftover = fleet_size - int(out["tankers_allocated"].sum())
    for idx in out.sort_values("stress", ascending=False).index:
        if leftover <= 0:
            break
        gap = int(out.loc[idx, "tankers_needed"] - out.loc[idx, "tankers_allocated"])
        give = min(gap, leftover)
        out.loc[idx, "tankers_allocated"] += give
        leftover -= give

    out["unmet_need"] = out["tankers_needed"] - out["tankers_allocated"]
    return out.drop(columns=["priority"])