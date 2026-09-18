FORMULA_REGISTRY = {
    "arithmetic.evaluate": {
        "formula_id": "math.arithmetic.expression.v1",
        "version": "1.0.0",
        "equation": "Evaluate expression using standard operator precedence",
        "inputs": {"expression": "Text"},
        "output": "Number",
        "source": "OmniCalc restricted AST evaluator",
    },
    "age.difference": {
        "formula_id": "date.calendar_difference.v1",
        "version": "1.0.0",
        "equation": "end_date − start_date with calendar borrowing",
        "inputs": {"start_date": "Date", "end_date": "Date"},
        "output": "Duration",
        "source": "Gregorian calendar arithmetic",
    },
    "finance.emi": {
        "formula_id": "finance.loan.emi.v1",
        "version": "1.0.0",
        "equation": "P × r × (1+r)^n ÷ ((1+r)^n − 1)",
        "inputs": {"principal": "Money", "annual_rate": "Rate", "tenure": "Duration"},
        "output": "MoneyPerMonth",
        "source": "Standard reducing-balance loan amortization formula",
    },
    "finance.total_payment": {
        "formula_id": "finance.loan.total_payment.v1",
        "version": "1.0.0",
        "equation": "total payment = monthly payment × number of monthly payments",
        "inputs": {"monthly_payment": "MoneyPerMonth", "tenure": "Duration"},
        "output": "Money",
        "source": "Deterministic loan cash-flow aggregation",
    },
    "finance.total_interest": {
        "formula_id": "finance.loan.total_interest.v1",
        "version": "1.0.0",
        "equation": "total interest = total payment − principal",
        "inputs": {"total_payment": "Money", "principal": "Money"},
        "output": "Money",
        "source": "Deterministic loan cash-flow decomposition",
    },
    "finance.interest_share": {
        "formula_id": "finance.loan.interest_share.v1",
        "version": "1.0.0",
        "equation": "interest share = total interest ÷ total payment × 100",
        "inputs": {"total_interest": "Money", "total_payment": "Money"},
        "output": "Percentage",
        "source": "Deterministic proportional analysis",
    },
    "statistics.summary": {
        "formula_id": "statistics.descriptive.population.v1",
        "version": "1.0.0",
        "equation": "mean, median, population variance and population standard deviation",
        "inputs": {"values": "NumberSeries"},
        "output": "StatisticsSummary",
        "source": "Population descriptive statistics",
    },
    "units.convert": {
        "formula_id": "units.linear_conversion.v1",
        "version": "1.0.0",
        "equation": "target = source × source_factor ÷ target_factor",
        "inputs": {"quantity": "Quantity"},
        "output": "Quantity",
        "source": "International standard conversion factors in the unit registry",
    },
}


def formula_provenance(operation: str) -> dict:
    formula = FORMULA_REGISTRY[operation]
    return {
        "formula_id": formula["formula_id"],
        "version": formula["version"],
        "operation": operation,
        "equation": formula["equation"],
        "source": formula["source"],
    }
