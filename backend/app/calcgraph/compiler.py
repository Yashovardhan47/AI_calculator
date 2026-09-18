from __future__ import annotations

import re
from datetime import date

from app.calculator.modules import age, finance, units
from app.calculator.parser import detect_calculator

from .formulas import formula_provenance
from .models import CalcGraph, CalcNode


class ClarificationNeeded(ValueError):
    def __init__(self, calculator: str, questions: list[str]):
        super().__init__(questions[0] if questions else "More information is required.")
        self.calculator = calculator
        self.questions = questions


def _extract_principal_value(query: str) -> float:
    currency_pattern = r"(?:₹|rs\.?|inr)\s*([\d,]+(?:\.\d+)?)\s*(crores?|lakhs?|million|thousand|k)?"
    loan_pattern = r"(?:loan|principal)\s*(?:amount\s*)?(?:of|is|=)?\s*(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d+)?)\s*(crores?|lakhs?|million|thousand|k)?"
    match = re.search(currency_pattern, query, re.IGNORECASE) or re.search(loan_pattern, query, re.IGNORECASE)
    if match:
        multiplier = finance.AMOUNT_MULTIPLIERS[(match.group(2) or "").lower()]
        return float(match.group(1).replace(",", "")) * multiplier
    return finance._extract_principal(query)


def _input(node_id: str, label: str, semantic_type: str, value, unit: str | None = None, **metadata) -> CalcNode:
    return CalcNode(
        id=node_id,
        label=label,
        kind="input",
        semantic_type=semantic_type,
        unit=unit,
        value=value,
        metadata=metadata,
    )


def _operation(node_id: str, label: str, semantic_type: str, operation: str, inputs: dict[str, str], unit: str | None = None, **metadata) -> CalcNode:
    formula = formula_provenance(operation)
    return CalcNode(
        id=node_id,
        label=label,
        kind="operation",
        semantic_type=semantic_type,
        unit=unit,
        operation=operation,
        inputs=inputs,
        metadata={"formula_id": formula["formula_id"], "formula_version": formula["version"], **metadata},
    )


def _compile_arithmetic(query: str) -> CalcGraph:
    expression = query.strip().replace("^", "**").replace("×", "*").replace("÷", "/")
    expression = re.sub(
        r"^(please\s+)?(calculate|compute|evaluate|solve|what\s+is)\s*[:=]?\s*",
        "",
        expression,
        flags=re.IGNORECASE,
    ).strip().rstrip("?")
    if not expression:
        raise ClarificationNeeded("arithmetic", ["Which numerical expression should I calculate?"])
    operation = "arithmetic.evaluate"
    nodes = [
        _input("expression", "Expression", "Text", expression),
        _operation("result", "Evaluated result", "Number", operation, {"expression": "expression"}),
    ]
    return CalcGraph(query, "arithmetic", nodes, ["result"], provenance=[formula_provenance(operation)])


def _compile_age(query: str) -> CalcGraph:
    try:
        dates = age._extract_dates(query)
    except ValueError as exc:
        raise ClarificationNeeded("age", ["Please provide a valid date of birth."]) from exc
    if not dates:
        raise ClarificationNeeded("age", ["What is the date of birth or starting date?"])
    start = dates[0]
    end = dates[1] if len(dates) > 1 else date.today()
    operation = "age.difference"
    nodes = [
        _input("start_date", "Starting date", "Date", start.isoformat(), source="user"),
        _input("end_date", "Comparison date", "Date", end.isoformat(), source="user" if len(dates) > 1 else "server_clock"),
        _operation("result", "Calendar difference", "Duration", operation, {"start_date": "start_date", "end_date": "end_date"}, unit="calendar duration"),
    ]
    assumptions = [] if len(dates) > 1 else ["The current server date is used as the comparison date."]
    return CalcGraph(query, "age", nodes, ["result"], assumptions=assumptions, provenance=[formula_provenance(operation)])


def _compile_emi(query: str) -> CalcGraph:
    questions = []
    try:
        principal = _extract_principal_value(query)
    except ValueError:
        principal = None
        questions.append("What is the loan principal and currency?")

    rate_match = re.search(r"(\d+(?:\.\d+)?)\s*%", query)
    annual_rate = float(rate_match.group(1)) if rate_match else None
    if annual_rate is None:
        questions.append("What is the annual interest rate?")

    years_match = re.search(r"(?:for|over|tenure\s*(?:of|is|=)?)\s*(\d+(?:\.\d+)?)\s*years?", query, re.IGNORECASE)
    months_match = re.search(r"(?:for|over|tenure\s*(?:of|is|=)?)\s*(\d+)\s*months?", query, re.IGNORECASE)
    months = int(round(float(years_match.group(1)) * 12)) if years_match else int(months_match.group(1)) if months_match else None
    if months is None:
        questions.append("What is the loan tenure in years or months?")
    if questions:
        raise ClarificationNeeded("emi", questions)

    normalized = query.lower()
    wants_interest_share = any(
        phrase in normalized
        for phrase in ("interest percentage", "interest share", "percentage is interest", "percentage of the payment")
    )
    wants_total_interest = wants_interest_share or any(
        phrase in normalized for phrase in ("total interest", "interest amount", "interest paid")
    )
    wants_total_payment = wants_total_interest or any(
        phrase in normalized for phrase in ("total payment", "total amount", "total repayment")
    )

    operations = ["finance.emi"]
    nodes = [
        _input("principal", "Loan principal", "Money", principal, unit="INR"),
        _input("annual_rate", "Annual interest rate", "Rate", annual_rate, unit="percent/year"),
        _input("tenure", "Loan tenure", "Duration", months, unit="month"),
        _operation(
            "emi",
            "Monthly payment",
            "MoneyPerMonth",
            "finance.emi",
            {"principal": "principal", "annual_rate": "annual_rate", "tenure": "tenure"},
            unit="INR/month",
        ),
    ]
    output_node_ids = ["emi"]
    if wants_total_payment:
        operations.append("finance.total_payment")
        nodes.append(
            _operation(
                "total_payment",
                "Total loan payment",
                "Money",
                "finance.total_payment",
                {"monthly_payment": "emi", "tenure": "tenure"},
                unit="INR",
            )
        )
        output_node_ids.append("total_payment")
    if wants_total_interest:
        operations.append("finance.total_interest")
        nodes.append(
            _operation(
                "total_interest",
                "Total loan interest",
                "Money",
                "finance.total_interest",
                {"total_payment": "total_payment", "principal": "principal"},
                unit="INR",
            )
        )
        output_node_ids.append("total_interest")
    if wants_interest_share:
        operations.append("finance.interest_share")
        nodes.append(
            _operation(
                "interest_share",
                "Interest share of repayment",
                "Percentage",
                "finance.interest_share",
                {"total_interest": "total_interest", "total_payment": "total_payment"},
                unit="percent",
            )
        )
        output_node_ids.append("interest_share")
    return CalcGraph(
        query,
        "emi",
        nodes,
        output_node_ids,
        assumptions=["The rate is fixed and payments occur monthly without fees or prepayments."],
        provenance=[formula_provenance(operation) for operation in operations],
    )


def _compile_statistics(query: str) -> CalcGraph:
    data_text = re.split(r"\bof\b|:", query, maxsplit=1, flags=re.IGNORECASE)[-1]
    values = [float(value) for value in re.findall(r"[-+]?\d+(?:\.\d+)?", data_text)]
    if len(values) < 2:
        raise ClarificationNeeded("statistics", ["Please provide at least two numeric values."])
    operation = "statistics.summary"
    nodes = [
        _input("values", "Dataset", "NumberSeries", values),
        _operation("result", "Population summary", "StatisticsSummary", operation, {"values": "values"}),
    ]
    return CalcGraph(
        query,
        "statistics",
        nodes,
        ["result"],
        assumptions=["The values are treated as the complete population."],
        provenance=[formula_provenance(operation)],
    )


def _compile_units(query: str) -> CalcGraph:
    match = re.search(r"([-+]?\d+(?:\.\d+)?)\s*([a-zA-Z]+)\s+(?:to|into|in)\s+([a-zA-Z]+)", query, re.IGNORECASE)
    if not match:
        raise ClarificationNeeded("units", ["Which value, source unit, and target unit should be converted?"])
    value = float(match.group(1))
    source = match.group(2).lower()
    target = match.group(3).lower()

    temperature = source in units.TEMPERATURES and target in units.TEMPERATURES
    if temperature:
        dimension = "temperature"
    elif source in units.UNITS and target in units.UNITS:
        dimension = units.UNITS[source][0]
    else:
        raise ClarificationNeeded("units", [f"The conversion from {source} to {target} is not registered. Which supported units should be used?"])

    operation = "units.convert"
    nodes = [
        _input("quantity", "Source quantity", "Quantity", value, unit=source, dimension=dimension),
        _operation("result", "Converted quantity", "Quantity", operation, {"quantity": "quantity"}, unit=target, target_unit=target, dimension=dimension),
    ]
    return CalcGraph(query, "units", nodes, ["result"], provenance=[formula_provenance(operation)])


COMPILERS = {
    "arithmetic": _compile_arithmetic,
    "age": _compile_age,
    "emi": _compile_emi,
    "statistics": _compile_statistics,
    "units": _compile_units,
}


def compile_query(query: str, calculator_hint: str | None = None) -> CalcGraph:
    normalized = query.strip()
    if not normalized:
        raise ClarificationNeeded("unknown", ["What outcome should I calculate?"])
    calculator = detect_calculator(normalized, calculator_hint)
    compiler = COMPILERS.get(calculator)
    if compiler is None:
        raise ClarificationNeeded(calculator, ["That domain pack is not registered yet."])
    return compiler(normalized)
