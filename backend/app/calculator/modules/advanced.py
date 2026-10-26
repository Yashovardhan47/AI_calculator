from __future__ import annotations

import math
import re
from typing import Callable


def _number(value: str) -> float:
    return float(value.replace(",", ""))


def _clean(value: float) -> int | float:
    if not math.isfinite(value):
        raise ValueError("The calculation did not produce a finite real number.")
    if value.is_integer():
        return int(value)
    return round(value, 8)


def _result(title: str, value: float, formula: str, steps: list[str], *, unit: str | None = None, assumptions: list[str] | None = None, metadata: dict | None = None) -> dict:
    clean = _clean(float(value))
    suffix = unit or ""
    if unit == "percent":
        answer = f"{clean}%"
    elif unit == "INR":
        answer = f"₹{float(value):,.2f}"
    elif unit:
        answer = f"{clean} {suffix}"
    else:
        answer = str(clean)
    return {
        "title": title,
        "answer": answer,
        "value": clean,
        "unit": unit,
        "formula": formula,
        "steps": steps,
        "assumptions": assumptions or [],
        "confidence": 1.0,
        "metadata": metadata or {},
    }


def _gcd(a: int, b: int) -> int:
    while b:
        a, b = b, a % b
    return abs(a)


def _factorial(n: int) -> int:
    if n < 0 or n > 170:
        raise ValueError("Factorial requires an integer from 0 through 170.")
    return math.factorial(n)


def calculate(query: str) -> dict:
    text = query.strip()
    lowered = text.lower()
    match: re.Match[str] | None

    # Linear equation: solve 3x + 7 = 25
    compact = re.sub(r"\s+", "", lowered)
    match = re.fullmatch(r"solve(?:forx)?(?:(-?\d*\.?\d*)x)?([+-]\d+(?:\.\d+)?)?=(-?\d+(?:\.\d+)?)", compact)
    if match:
        coefficient_text = match.group(1)
        coefficient = 1.0 if coefficient_text in (None, "") else -1.0 if coefficient_text == "-" else float(coefficient_text)
        if coefficient == 0:
            raise ValueError("The coefficient of x must not be zero.")
        constant = float(match.group(2) or 0)
        right = float(match.group(3))
        value = (right - constant) / coefficient
        return _result("Linear equation solution", value, "x = (c − b) / a", [f"Read a={coefficient:g}, b={constant:g}, c={right:g}.", f"Subtract b and divide by a: x = {value:g}."])

    # Quadratic coefficients: quadratic a=1 b=-5 c=6
    match = re.search(r"quadratic.*?a\s*=\s*(-?[\d.]+).*?b\s*=\s*(-?[\d.]+).*?c\s*=\s*(-?[\d.]+)", lowered)
    if match:
        a, b, c = map(float, match.groups())
        if a == 0:
            raise ValueError("Quadratic coefficient a must not be zero.")
        discriminant = b * b - 4 * a * c
        if discriminant < 0:
            real = -b / (2 * a)
            imaginary = math.sqrt(-discriminant) / abs(2 * a)
            return {
                **_result("Quadratic roots", real, "x = (−b ± √(b²−4ac)) / 2a", [f"Discriminant = {discriminant:g}.", "The discriminant is negative, so the roots are complex."], metadata={"real": real, "imaginary": imaginary}),
                "answer": f"x₁ = {real:g} + {imaginary:g}i; x₂ = {real:g} − {imaginary:g}i",
            }
        root = math.sqrt(discriminant)
        x1, x2 = (-b + root) / (2 * a), (-b - root) / (2 * a)
        return {
            **_result("Quadratic roots", x1, "x = (−b ± √(b²−4ac)) / 2a", [f"Discriminant = {discriminant:g}.", "Apply the quadratic formula to obtain both roots."], metadata={"roots": [_clean(x1), _clean(x2)]}),
            "answer": f"x₁ = {_clean(x1)}; x₂ = {_clean(x2)}",
        }

    # Geometry.
    match = re.search(r"area.*circle.*?(?:radius|r)\s*(?:of|=)?\s*([\d.]+)", lowered)
    if match:
        radius = float(match.group(1))
        return _result("Circle area", math.pi * radius**2, "A = πr²", [f"Square radius {radius:g}.", "Multiply by π."], unit="square units")
    match = re.search(r"(?:circumference|perimeter).*circle.*?(?:radius|r)\s*(?:of|=)?\s*([\d.]+)", lowered)
    if match:
        radius = float(match.group(1))
        return _result("Circle circumference", 2 * math.pi * radius, "C = 2πr", [f"Double radius {radius:g}.", "Multiply by π."], unit="units")
    match = re.search(r"area.*rectangle.*?(?:length|l)\s*(?:of|=)?\s*([\d.]+).*?(?:width|w)\s*(?:of|=)?\s*([\d.]+)", lowered)
    if match:
        length, width = map(float, match.groups())
        return _result("Rectangle area", length * width, "A = length × width", [f"Multiply {length:g} by {width:g}."], unit="square units")
    match = re.search(r"area.*triangle.*?(?:base|b)\s*(?:of|=)?\s*([\d.]+).*?(?:height|h)\s*(?:of|=)?\s*([\d.]+)", lowered)
    if match:
        base, height = map(float, match.groups())
        return _result("Triangle area", base * height / 2, "A = ½ × base × height", [f"Multiply {base:g} by {height:g} and divide by two."], unit="square units")

    # Finance beyond loans.
    match = re.search(r"(compound|simple) interest.*?(?:on|principal)?\s*(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d+)?).*?([\d.]+)\s*%.*?(\d+(?:\.\d+)?)\s*years?", lowered)
    if match:
        kind, principal_text, rate_text, years_text = match.groups()
        principal, rate, years = _number(principal_text), float(rate_text) / 100, float(years_text)
        interest = principal * rate * years if kind == "simple" else principal * ((1 + rate) ** years - 1)
        formula = "I = P × r × t" if kind == "simple" else "I = P((1+r)^t − 1)"
        return _result(f"{kind.title()} interest", interest, formula, [f"Principal = ₹{principal:,.2f}; annual rate = {rate * 100:g}%; time = {years:g} years.", "Apply the registered interest formula."], unit="INR")
    match = re.search(r"(?:(?:discount|sale).*?(\d+(?:\.\d+)?)\s*%|(\d+(?:\.\d+)?)\s*%\s*(?:discount|off)).*?(?:on|of|price)?\s*(?:₹|rs\.?)?\s*([\d,.]+)\s*$", lowered)
    if match:
        percentage = float(match.group(1) or match.group(2))
        price = _number(match.group(3))
        saved = price * percentage / 100
        return _result("Discounted price", price - saved, "final price = price × (1 − discount/100)", [f"Discount amount = ₹{saved:,.2f}.", "Subtract the discount from the original price."], unit="INR", metadata={"savings": round(saved, 2)})

    # Number theory and combinatorics.
    match = re.search(r"factorial(?:\s+of)?\s+(\d+)", lowered)
    if match:
        n = int(match.group(1))
        return _result("Factorial", float(_factorial(n)), "n! = 1 × 2 × … × n", [f"Multiply the integers from 1 through {n}."])
    match = re.search(r"(?:gcd|greatest common divisor).*?(\d+)\D+(\d+)", lowered)
    if match:
        a, b = map(int, match.groups())
        return _result("Greatest common divisor", float(_gcd(a, b)), "Euclidean algorithm", [f"Apply repeated remainder to {a} and {b}."])
    match = re.search(r"(?:lcm|least common multiple).*?(\d+)\D+(\d+)", lowered)
    if match:
        a, b = map(int, match.groups())
        return _result("Least common multiple", float(abs(a * b) // _gcd(a, b)), "lcm(a,b) = |ab| / gcd(a,b)", ["Find the GCD, then divide the absolute product by it."])
    match = re.search(r"(?:combination|ncr|choose)\s*(\d+).*?(?:choose|,|\s)\s*(\d+)\s*$", lowered)
    if match:
        n, r = map(int, match.groups())
        if r > n:
            raise ValueError("For combinations, r cannot exceed n.")
        return _result("Combinations", float(math.comb(n, r)), "nCr = n! / (r!(n−r)!)", [f"Choose {r} items from {n} without order."])
    match = re.search(r"(?:permutation|npr)\s*(\d+)\D+(\d+)", lowered)
    if match:
        n, r = map(int, match.groups())
        if r > n:
            raise ValueError("For permutations, r cannot exceed n.")
        return _result("Permutations", float(math.perm(n, r)), "nPr = n! / (n−r)!", [f"Arrange {r} items selected from {n}."])

    # Health and basic physics.
    match = re.search(r"bmi.*?(?:weight)?\s*([\d.]+)\s*kg.*?(?:height)?\s*([\d.]+)\s*(cm|m)\b", lowered)
    if match:
        weight, height, unit = float(match.group(1)), float(match.group(2)), match.group(3)
        height_m = height / 100 if unit == "cm" else height
        if height_m <= 0:
            raise ValueError("Height must be greater than zero.")
        return _result("Body mass index", weight / height_m**2, "BMI = mass(kg) / height(m)²", [f"Convert height to {height_m:g} metres.", "Divide mass by squared height."], unit="kg/m²", assumptions=["BMI is a screening metric and is not medical advice."])
    match = re.search(r"speed.*?distance\s*(?:of|=)?\s*([\d.]+).*?time\s*(?:of|=)?\s*([\d.]+)", lowered)
    if match:
        distance, time = map(float, match.groups())
        if time == 0:
            raise ValueError("Time must be greater than zero.")
        return _result("Average speed", distance / time, "speed = distance / time", ["Divide distance by elapsed time."], unit="distance-units/time-unit")

    # Trigonometry in degrees.
    match = re.search(r"\b(sin|cos|tan)\s*(?:of)?\s*([\d.]+)\s*degrees?", lowered)
    if match:
        name, degrees_text = match.groups()
        degrees = float(degrees_text)
        radians = math.radians(degrees)
        function: Callable[[float], float] = getattr(math, name)
        return _result(f"{name}({degrees:g}°)", function(radians), f"{name}(degrees × π/180)", [f"Convert {degrees:g}° to {radians:.8g} radians.", f"Evaluate {name} using the standard library."])

    # Common word-form arithmetic.
    binary_patterns = [
        (r"(?:add|sum of)\s*(-?[\d,.]+)\s*(?:and|to|,)\s*(-?[\d,.]+)", "Sum", lambda a, b: a + b, "a + b"),
        (r"subtract\s*(-?[\d,.]+)\s*from\s*(-?[\d,.]+)", "Difference", lambda a, b: b - a, "second − first"),
        (r"(?:multiply|product of)\s*(-?[\d,.]+)\s*(?:and|by|,)\s*(-?[\d,.]+)", "Product", lambda a, b: a * b, "a × b"),
        (r"divide\s*(-?[\d,.]+)\s*by\s*(-?[\d,.]+)", "Quotient", lambda a, b: a / b, "a ÷ b"),
    ]
    for pattern, title, operation, formula in binary_patterns:
        match = re.search(pattern, lowered)
        if match:
            a, b = map(_number, match.groups())
            if title == "Quotient" and b == 0:
                raise ValueError("Cannot divide by zero.")
            return _result(title, operation(a, b), formula, [f"Use operands {a:g} and {b:g}.", f"Apply {formula}."])

    match = re.search(r"percentage\s+(increase|decrease).*?from\s*([\d,.]+)\s*to\s*([\d,.]+)", lowered)
    if match:
        kind, start_text, end_text = match.groups()
        start, end = _number(start_text), _number(end_text)
        if start == 0:
            raise ValueError("Percentage change is undefined when the original value is zero.")
        change = (end - start) / abs(start) * 100
        expected = change if kind == "increase" else -change
        return _result(f"Percentage {kind}", expected, "(new − original) / |original| × 100", [f"Change = {end:g} − {start:g}.", "Divide by the absolute original value and multiply by 100."], unit="percent")

    raise ValueError(
        "I could not map that request to a registered deterministic formula. "
        "Include the operation, numeric values, and units where applicable."
    )
