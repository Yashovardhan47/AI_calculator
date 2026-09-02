import math
import re
import statistics


def calculate(query: str) -> dict:
    data_text = re.split(r"\bof\b|:", query, maxsplit=1, flags=re.IGNORECASE)[-1]
    numbers = [float(value) for value in re.findall(r"[-+]?\d+(?:\.\d+)?", data_text)]
    if len(numbers) < 2:
        raise ValueError("Provide at least two numbers separated by commas or spaces.")
    if len(numbers) > 10_000:
        raise ValueError("This interactive endpoint accepts at most 10,000 values.")

    mean = statistics.fmean(numbers)
    median = statistics.median(numbers)
    pstdev = statistics.pstdev(numbers)
    variance = statistics.pvariance(numbers)
    clean_mean = round(mean, 8)
    clean_median = round(median, 8)

    return {
        "title": "Dataset summary",
        "answer": f"Mean {clean_mean}; median {clean_median}; population SD {pstdev:.8g}",
        "value": clean_mean,
        "unit": None,
        "formula": "mean = Σx/n; population variance = Σ(x−μ)²/n",
        "steps": [
            f"Read {len(numbers)} values.",
            f"Sum = {math.fsum(numbers):.8g}; mean = {clean_mean}.",
            f"Sort the values to obtain median = {clean_median}.",
            f"Population variance = {variance:.8g}; population SD = {pstdev:.8g}.",
        ],
        "assumptions": ["The supplied values represent the full population, not a sample."],
        "confidence": 1.0,
        "metadata": {
            "count": len(numbers),
            "min": min(numbers),
            "max": max(numbers),
            "mean": clean_mean,
            "median": clean_median,
            "population_variance": round(variance, 8),
            "population_standard_deviation": round(pstdev, 8),
        },
    }

