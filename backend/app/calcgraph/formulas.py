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

