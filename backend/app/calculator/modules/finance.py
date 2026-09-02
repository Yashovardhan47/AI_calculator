import math
import re


AMOUNT_MULTIPLIERS = {
    "": 1,
    "k": 1_000,
    "thousand": 1_000,
    "lakh": 100_000,
    "lakhs": 100_000,
    "crore": 10_000_000,
    "crores": 10_000_000,
    "million": 1_000_000,
}


def _extract_principal(text: str) -> float:
    pattern = r"(?:₹|rs\.?|inr|principal\s*(?:of|is|=)?|loan\s*(?:of|is|=)?)?\s*([\d,]+(?:\.\d+)?)\s*(crores?|lakhs?|million|thousand|k)?"
    for match in re.finditer(pattern, text, re.IGNORECASE):
        prefix = text[max(0, match.start() - 15):match.start()].lower()
        suffix = (match.group(2) or "").lower()
        if "%" in text[match.end():match.end() + 2] or "rate" in prefix:
            continue
        value = float(match.group(1).replace(",", "")) * AMOUNT_MULTIPLIERS[suffix]
        if value > 0:
            return value
    raise ValueError("Include the loan amount, for example ₹10 lakh.")


def calculate(query: str) -> dict:
    principal = _extract_principal(query)
    rate_match = re.search(r"(\d+(?:\.\d+)?)\s*%", query)
    if not rate_match:
        raise ValueError("Include the annual interest rate as a percentage.")
    annual_rate = float(rate_match.group(1))

    years_match = re.search(r"(?:for|over|tenure\s*(?:of|is|=)?)\s*(\d+(?:\.\d+)?)\s*years?", query, re.IGNORECASE)
    months_match = re.search(r"(?:for|over|tenure\s*(?:of|is|=)?)\s*(\d+)\s*months?", query, re.IGNORECASE)
    if years_match:
        months = int(round(float(years_match.group(1)) * 12))
    elif months_match:
        months = int(months_match.group(1))
    else:
        raise ValueError("Include the loan tenure, such as 5 years or 60 months.")
    if months <= 0 or annual_rate < 0:
        raise ValueError("The tenure must be positive and the interest rate cannot be negative.")

    monthly_rate = annual_rate / 12 / 100
    if monthly_rate == 0:
        emi = principal / months
    else:
        factor = math.pow(1 + monthly_rate, months)
        emi = principal * monthly_rate * factor / (factor - 1)
    total_payment = emi * months
    total_interest = total_payment - principal

    return {
        "title": "Loan EMI",
        "answer": f"₹{emi:,.2f} per month",
        "value": round(emi, 2),
        "unit": "INR/month",
        "formula": "EMI = P × r × (1+r)^n ÷ ((1+r)^n − 1)",
        "steps": [
            f"Principal P = ₹{principal:,.2f}",
            f"Monthly rate r = {annual_rate}% ÷ 12 = {monthly_rate:.8f}",
            f"Number of monthly payments n = {months}",
            f"Total payment = ₹{total_payment:,.2f}; total interest = ₹{total_interest:,.2f}",
        ],
        "assumptions": ["The rate remains fixed.", "Payments occur monthly with no fees or prepayments."],
        "confidence": 0.98,
        "metadata": {
            "principal": round(principal, 2),
            "annual_rate_percent": annual_rate,
            "months": months,
            "total_payment": round(total_payment, 2),
            "total_interest": round(total_interest, 2),
        },
    }

