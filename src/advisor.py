"""Plain-language advisory in English or Telugu. Uses Claude if a key exists."""
import os
from dotenv import load_dotenv

load_dotenv()

TELUGU_LEVELS = {
    "Critical": "తీవ్రమైన",
    "High": "అధిక",
    "Moderate": "మధ్యస్థ",
    "Low": "తక్కువ",
}

FACT_KEYS = ["district", "level", "stress", "rain_past_mm", "rain_forecast_mm",
             "avg_tmax_c", "tankers_needed", "tankers_allocated", "unmet_need"]


def _fallback(row: dict, language: str) -> str:
    """Rule-based advisory used when there is no API key or the call fails."""
    if language == "Telugu":
        return (
            f"{row['district']} జిల్లాలో నీటి ఒత్తిడి స్థాయి {TELUGU_LEVELS[row['level']]} "
            f"(స్కోరు {row['stress']}). నీటిని పొదుపుగా వాడండి, వర్షపు నీటిని నిల్వ చేయండి, "
            f"ట్యాంకర్ సమాచారం కోసం స్థానిక అధికారులను సంప్రదించండి."
        )
    tips = {
        "Critical": "Use water only for essentials, expect tanker supply, and report leaks immediately.",
        "High": "Cut non-essential use, fix leaks, and store water where safe.",
        "Moderate": "Use water wisely and watch for updates as the forecast changes.",
        "Low": "Supply looks stable. Continue normal conservation habits.",
    }
    return (
        f"{row['district']}: water stress is {row['level']} (score {row['stress']}/100). "
        f"Past 30-day rain {row['rain_past_mm']} mm, next 7 days {row['rain_forecast_mm']} mm, "
        f"average max temperature {row['avg_tmax_c']}°C. {tips[row['level']]}"
    )


def get_advisory(row: dict, language: str = "English") -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return _fallback(row, language)

    try:
        import anthropic

        facts = {k: row.get(k) for k in FACT_KEYS}
        client = anthropic.Anthropic(api_key=api_key)
        prompt = (
            f"You advise Telangana citizens about water scarcity. Write a short, simple, "
            f"practical advisory (max 90 words) in {language} for this district. "
            f"Use only these facts, do not invent numbers.\n\n{facts}"
        )
        message = client.messages.create(
            model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5-5"),
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text
    except Exception:
        return _fallback(row, language)