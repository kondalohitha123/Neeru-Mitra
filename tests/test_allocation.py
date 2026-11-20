import pandas as pd
from src.allocation import allocate_tankers, estimate_need


def _sample_df():
    rows = [("A", 1_000_000, 80), ("B", 1_000_000, 20), ("C", 500_000, 50)]
    df = pd.DataFrame(rows, columns=["district", "population", "stress"])
    df["tankers_needed"] = [estimate_need(p, s) for p, s in zip(df["population"], df["stress"])]
    return df


def test_fleet_never_exceeded_and_need_never_overserved():
    df = _sample_df()
    out = allocate_tankers(df, fleet_size=50)
    assert out["tankers_allocated"].sum() == min(50, df["tankers_needed"].sum())
    assert (out["tankers_allocated"] <= out["tankers_needed"]).all()


def test_most_stressed_district_gets_more():
    out = allocate_tankers(_sample_df(), fleet_size=50).set_index("district")
    assert out.loc["A", "tankers_allocated"] > out.loc["B", "tankers_allocated"]