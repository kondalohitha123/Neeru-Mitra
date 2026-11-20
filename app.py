"""Neeru Mitra: Telangana Water Stress Early-Warning & Tanker Allocation Advisor."""
import pandas as pd
import streamlit as st

from src.advisor import get_advisory
from src.allocation import allocate_tankers, estimate_need
from src.scoring import compute_stress, stress_level
from src.weather import fetch_weather

st.set_page_config(page_title="Neeru Mitra", page_icon="💧", layout="wide")
st.title("💧 Neeru Mitra: Telangana Water Stress Advisor")
st.caption(
    "IDEA//FORGE | Track 2: Climate, Resource Infrastructure & Supply Resilience. "
    "Weather is live (Open-Meteo). Groundwater is from Telangana Groundwater Dept reports "
    "where tagged; reservoir levels and some districts are ESTIMATES."
)


@st.cache_data(ttl=3600)
def load_districts() -> pd.DataFrame:
    return pd.read_csv("data/districts.csv")


@st.cache_data(ttl=1800)
def build_dataset() -> pd.DataFrame:
    """Fetch weather per district, then compute stress score and tanker need."""
    df = load_districts()
    rows = []
    for _, d in df.iterrows():
        try:
            w = fetch_weather(d["lat"], d["lon"])
            live = True
        except Exception:
            # Fallback so the app still loads if the weather API is unreachable.
            w = {"rain_past_mm": 0.0, "rain_forecast_mm": 0.0, "avg_tmax_c": 32.0}
            live = False
        stress = compute_stress(
            w["rain_past_mm"], d["normal_rain_30d_mm"], w["avg_tmax_c"],
            d["groundwater_depth_m"], d["reservoir_pct"],
        )
        rows.append({
            "district": d["district"], "lat": d["lat"], "lon": d["lon"],
            "population": d["population"], **w,
            "stress": stress, "level": stress_level(stress),
            "tankers_needed": estimate_need(d["population"], stress),
            "data_quality": d["data_quality"],
            "live_weather": live,
        })
    return pd.DataFrame(rows)


with st.sidebar:
    st.header("Controls")
    fleet = st.slider("Available tankers (per day)", 10, 300, 60, step=10)
    language = st.radio("Advisory language", ["English", "Telugu"])
    if st.button("Refresh live data"):
        st.cache_data.clear()
        st.rerun()

data = build_dataset()
if not data["live_weather"].all():
    st.warning("Live weather was unavailable for some districts. Fallback values were used for those.")

result = allocate_tankers(data, fleet).sort_values("stress", ascending=False)

c1, c2, c3 = st.columns(3)
c1.metric("Most stressed district", result.iloc[0]["district"], f"{result.iloc[0]['stress']}/100")
c2.metric("Critical / High districts", int(result["level"].isin(["Critical", "High"]).sum()))
c3.metric("Unmet tanker need (per day)", int(result["unmet_need"].sum()))

left, right = st.columns(2)
with left:
    st.subheader("Stress map")
    st.map(result.rename(columns={"lon": "longitude", "lat": "latitude"}),
           latitude="latitude", longitude="longitude", size=15000)
with right:
    st.subheader("Water Stress Score by district")
    st.bar_chart(result.set_index("district")["stress"])

st.subheader("Tanker allocation plan")
table = result[["district", "level", "stress", "rain_past_mm", "rain_forecast_mm",
                "avg_tmax_c", "tankers_needed", "tankers_allocated", "unmet_need",
                "data_quality"]]
st.dataframe(table, hide_index=True)
st.download_button("Download plan (CSV)", table.to_csv(index=False),
                   "tanker_plan.csv", "text/csv")

st.subheader("AI advisory")
choice = st.selectbox("Select district", result["district"])
row = result[result["district"] == choice].iloc[0].to_dict()
st.info(get_advisory(row, language))

with st.expander("How the score works"):
    st.markdown("""
**Water Stress Score (0-100)** = 25% rainfall deficit + 20% forecast heat
+ 30% groundwater depth + 25% reservoir shortage.

**Tanker need** = population x 55 L/day x stress x 2% (share assumed to depend on tankers),
converted to 10,000 L tankers.

**Allocation** = fleet shared in proportion to need x stress, capped at each district's need.
Leftover tankers go to the most stressed districts.

**Data note:** weights, the 2% share and the reservoir values are adjustable assumptions.
Rows tagged `gw_estimate` use estimated groundwater depth.
""")