import re


CALCULATOR_ALIASES = {
    "arithmetic": "arithmetic",
    "math": "arithmetic",
    "age": "age",
    "date": "age",
    "emi": "emi",
    "loan": "emi",
    "finance": "emi",
    "statistics": "statistics",
    "stats": "statistics",
    "units": "units",
    "conversion": "units",
}


def detect_calculator(query: str, hint: str | None = None) -> str:
    if hint:
        normalized = CALCULATOR_ALIASES.get(hint.lower().strip())
        if normalized:
            return normalized

    text = query.lower()
    if any(word in text for word in ("emi", "loan", "monthly payment", "interest rate")):
        return "emi"
    if any(word in text for word in ("mean", "median", "standard deviation", "variance", "dataset")):
        return "statistics"
    if re.search(r"\b(convert|conversion)\b", text) or re.search(
        r"\b(km|kilometres?|kilometers?|miles?|kg|kilograms?|pounds?|celsius|fahrenheit)\b.*\b(to|into|in)\b",
        text,
    ):
        return "units"
    if any(word in text for word in ("age", "born", "birth", "date of birth")):
        return "age"
    return "arithmetic"

