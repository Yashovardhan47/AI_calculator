from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


PRINCIPALS = [100_000, 250_000, 500_000, 1_000_000, 2_500_000]
ANNUAL_RATES = [0.0, 5.5, 8.5, 12.0]
TENURES = [12, 36, 60]
GOALS = {
    "emi": ("Calculate the EMI", ["emi"]),
    "payment": ("Calculate the EMI and total payment", ["emi", "total_payment"]),
    "interest": ("Calculate the EMI, total payment, and total interest", ["emi", "total_payment", "total_interest"]),
    "share": (
        "Calculate the EMI, total payment, total interest, and interest percentage",
        ["emi", "total_payment", "total_interest", "interest_share"],
    ),
}


def reference_values(principal: float, annual_rate: float, months: int) -> dict[str, float]:
    monthly_rate = annual_rate / 12 / 100
    if monthly_rate == 0:
        emi = principal / months
    else:
        factor = math.pow(1 + monthly_rate, months)
        emi = principal * monthly_rate * factor / (factor - 1)
    total_payment = emi * months
    total_interest = total_payment - principal
    interest_share = total_interest / total_payment * 100 if total_payment else 0.0
    return {
        "emi": round(emi, 2),
        "total_payment": round(total_payment, 2),
        "total_interest": round(total_interest, 2),
        "interest_share": round(interest_share, 4),
    }


def generate_cases() -> list[dict]:
    cases = []
    for principal in PRINCIPALS:
        for annual_rate in ANNUAL_RATES:
            for months in TENURES:
                reference = reference_values(principal, annual_rate, months)
                for goal_id, (prompt, outputs) in GOALS.items():
                    cases.append(
                        {
                            "id": f"finance-{principal}-{str(annual_rate).replace('.', '_')}-{months}-{goal_id}",
                            "query": f"{prompt} for a loan of INR {principal} at {annual_rate}% for {months} months",
                            "domain": "finance",
                            "difficulty": "multi_step" if len(outputs) > 1 else "single_step",
                            "source": "template",
                            "expected": {
                                "outcome": "success",
                                "calculator": "emi",
                                "output_values": {output: reference[output] for output in outputs},
                                "tolerance": 0.02,
                                "operation_count": len(outputs),
                                "graph_depth": len(outputs),
                            },
                        }
                    )
    return cases


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the deterministic CalcGraphBench finance suite.")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    cases = generate_cases()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(cases, indent=2) + "\n", encoding="utf-8")
    print(f"Generated {len(cases)} benchmark cases at {args.output}")


if __name__ == "__main__":
    main()
