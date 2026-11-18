"""Translate model features into concise risk explanations."""

AMOUNT_BANDS = (
    (5000, "unusually large amount"),
    (1000, "very large amount"),
    (250, "above-average amount"),
)


def get_narrative(features: dict, probability: float) -> dict:
    triggers = []
    amount = float(features.get("Amount", 0))

    for limit, label in AMOUNT_BANDS:
        if amount >= limit:
            triggers.append(label)
            break

    for name in ("V17", "V14", "V12", "V10", "V16"):
        value = float(features.get(name, 0))
        if abs(value) >= 3:
            triggers.append(f"unusual {name} pattern")
            break

    for name in ("V3", "V7", "V11", "V4"):
        value = float(features.get(name, 0))
        if abs(value) >= 4:
            triggers.append(f"unusual {name} pattern")
            break

    if not triggers:
        if probability >= 0.75:
            triggers.append("model confidence is unusually high")
        elif probability >= 0.35:
            triggers.append("combination of transaction patterns is elevated")
        else:
            triggers.append("no strongly unusual transaction patterns detected")

    if probability >= 0.75:
        risk_level = "fraud"
        summary = "High likelihood of fraudulent activity"
    elif probability >= 0.35:
        risk_level = "review"
        summary = "Manual review is recommended"
    else:
        risk_level = "safe"
        summary = "No immediate fraud indicators detected"

    return {
        "summary": summary,
        "riskLevel": risk_level,
        "triggers": triggers[:4],
    }

