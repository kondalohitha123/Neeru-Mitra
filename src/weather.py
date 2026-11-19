"""Fetch rainfall and temperature data from Open-Meteo (free, no API key)."""
import requests

API_URL = "https://api.open-meteo.com/v1/forecast"


def fetch_weather(lat: float, lon: float, past_days: int = 30, forecast_days: int = 7) -> dict:
    """Return past rainfall total plus forecast rain and heat for a location."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "temperature_2m_max,precipitation_sum",
        "past_days": past_days,
        "forecast_days": forecast_days,
        "timezone": "Asia/Kolkata",
    }
    response = requests.get(API_URL, params=params, timeout=15)
    response.raise_for_status()
    daily = response.json()["daily"]

    rain = daily["precipitation_sum"]
    tmax = daily["temperature_2m_max"]

    # The first `past_days` entries are history, the rest are the forecast.
    rain_past = sum(x or 0 for x in rain[:past_days])
    rain_forecast = sum(x or 0 for x in rain[past_days:])
    forecast_temps = [x for x in tmax[past_days:] if x is not None]
    avg_tmax = sum(forecast_temps) / len(forecast_temps) if forecast_temps else 0.0

    return {
        "rain_past_mm": round(rain_past, 1),
        "rain_forecast_mm": round(rain_forecast, 1),
        "avg_tmax_c": round(avg_tmax, 1),
    }