import re


UNITS = {
    "m": ("length", 1.0, "metres"),
    "meter": ("length", 1.0, "metres"),
    "meters": ("length", 1.0, "metres"),
    "metre": ("length", 1.0, "metres"),
    "metres": ("length", 1.0, "metres"),
    "km": ("length", 1000.0, "kilometres"),
    "kilometer": ("length", 1000.0, "kilometres"),
    "kilometers": ("length", 1000.0, "kilometres"),
    "kilometre": ("length", 1000.0, "kilometres"),
    "kilometres": ("length", 1000.0, "kilometres"),
    "mile": ("length", 1609.344, "miles"),
    "miles": ("length", 1609.344, "miles"),
    "ft": ("length", 0.3048, "feet"),
    "foot": ("length", 0.3048, "feet"),
    "feet": ("length", 0.3048, "feet"),
    "kg": ("mass", 1.0, "kilograms"),
    "kilogram": ("mass", 1.0, "kilograms"),
    "kilograms": ("mass", 1.0, "kilograms"),
    "g": ("mass", 0.001, "grams"),
    "gram": ("mass", 0.001, "grams"),
    "grams": ("mass", 0.001, "grams"),
    "lb": ("mass", 0.45359237, "pounds"),
    "lbs": ("mass", 0.45359237, "pounds"),
    "pound": ("mass", 0.45359237, "pounds"),
    "pounds": ("mass", 0.45359237, "pounds"),
    "l": ("volume", 1.0, "litres"),
    "litre": ("volume", 1.0, "litres"),
    "litres": ("volume", 1.0, "litres"),
    "liter": ("volume", 1.0, "litres"),
    "liters": ("volume", 1.0, "litres"),
    "ml": ("volume", 0.001, "millilitres"),
    "millilitre": ("volume", 0.001, "millilitres"),
    "millilitres": ("volume", 0.001, "millilitres"),
}

TEMPERATURES = {"c", "celsius", "f", "fahrenheit", "k", "kelvin"}


def _convert_temperature(value: float, source: str, target: str) -> float:
    source = source[0]
    target = target[0]
    celsius = value if source == "c" else (value - 32) * 5 / 9 if source == "f" else value - 273.15
    return celsius if target == "c" else celsius * 9 / 5 + 32 if target == "f" else celsius + 273.15


def calculate(query: str) -> dict:
    match = re.search(r"([-+]?\d+(?:\.\d+)?)\s*([a-zA-Z]+)\s+(?:to|into|in)\s+([a-zA-Z]+)", query, re.IGNORECASE)
    if not match:
        raise ValueError("Use a request such as 'Convert 15 kilometres to miles'.")
    value = float(match.group(1))
    source = match.group(2).lower()
    target = match.group(3).lower()

    if source in TEMPERATURES and target in TEMPERATURES:
        result = _convert_temperature(value, source, target)
        formula = "Convert the source temperature to Celsius, then convert Celsius to the target scale."
        target_name = {"c": "Celsius", "celsius": "Celsius", "f": "Fahrenheit", "fahrenheit": "Fahrenheit", "k": "Kelvin", "kelvin": "Kelvin"}[target]
    else:
        if source not in UNITS or target not in UNITS:
            raise ValueError("One or both units are not supported yet.")
        source_dimension, source_factor, _ = UNITS[source]
        target_dimension, target_factor, target_name = UNITS[target]
        if source_dimension != target_dimension:
            raise ValueError(f"Cannot convert {source_dimension} to {target_dimension}; their dimensions are incompatible.")
        result = value * source_factor / target_factor
        formula = f"target value = source value × {source_factor} ÷ {target_factor}"

    rounded = round(result, 10)
    return {
        "title": "Unit conversion",
        "answer": f"{rounded:,} {target_name}",
        "value": rounded,
        "unit": target_name,
        "formula": formula,
        "steps": [f"Read the source value: {value} {source}.", f"Apply the verified conversion factor.", f"Return {rounded} {target_name}."],
        "assumptions": ["Standard international conversion factors are used."],
        "confidence": 1.0,
    }

