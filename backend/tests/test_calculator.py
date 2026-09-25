import math
import unittest
from datetime import date
from unittest.mock import patch

from app.calculator import CalculationError, calculate


class CalculatorEngineTests(unittest.TestCase):
    def test_arithmetic_obeys_precedence(self):
        result = calculate("Calculate (18 + 6) * 4 / 3")
        self.assertEqual(result["calculator"], "arithmetic")
        self.assertEqual(result["value"], 32)

    def test_arithmetic_rejects_code(self):
        with self.assertRaises(CalculationError):
            calculate("__import__('os').system('echo unsafe')")

    @patch("app.calculator.modules.age.date")
    def test_exact_age(self, mocked_date):
        mocked_date.today.return_value = date(2026, 9, 2)
        mocked_date.side_effect = lambda *args, **kwargs: date(*args, **kwargs)
        result = calculate("My date of birth is 2003-08-15. Calculate my age.")
        self.assertEqual(result["answer"], "23 years, 0 months, and 18 days")

    def test_emi(self):
        result = calculate("EMI for ₹10 lakh at 8.5% for 5 years")
        self.assertEqual(result["calculator"], "emi")
        self.assertTrue(math.isclose(result["value"], 20516.53, abs_tol=0.02))

    def test_statistics(self):
        result = calculate("Find mean, median and standard deviation of 12, 15, 18, 21")
        self.assertEqual(result["metadata"]["mean"], 16.5)
        self.assertEqual(result["metadata"]["median"], 16.5)

    def test_statistics_accepts_natural_language_and_separator(self):
        result = calculate("standard deviation of 12, 18, 21, 23 and 31")
        self.assertEqual(result["calculator"], "statistics")
        self.assertTrue(
            math.isclose(
                result["metadata"]["population_standard_deviation"],
                6.2289646,
                abs_tol=1e-7,
            )
        )

    def test_linear_equation(self):
        result = calculate("Solve 3x + 7 = 25")
        self.assertEqual(result["calculator"], "advanced")
        self.assertEqual(result["value"], 6)

    def test_geometry(self):
        result = calculate("Area of a circle with radius 12")
        self.assertTrue(math.isclose(result["value"], math.pi * 144, rel_tol=1e-8))

    def test_compound_interest(self):
        result = calculate("Calculate compound interest on 100000 at 8% for 5 years")
        self.assertEqual(result["unit"], "INR")
        self.assertTrue(math.isclose(result["value"], 46932.80768, abs_tol=1e-5))

    def test_number_theory_and_combinatorics(self):
        self.assertEqual(calculate("factorial of 6")["value"], 720)
        self.assertEqual(calculate("gcd of 48 and 18")["value"], 6)
        self.assertEqual(calculate("combination 10 choose 3")["value"], 120)

    def test_bmi_and_degree_trigonometry(self):
        self.assertTrue(math.isclose(calculate("BMI weight 70 kg height 175 cm")["value"], 22.85714286))
        self.assertTrue(math.isclose(calculate("sin 30 degrees")["value"], 0.5, abs_tol=1e-10))

    def test_unit_conversion(self):
        result = calculate("Convert 15 kilometres to miles")
        self.assertTrue(math.isclose(result["value"], 9.3205678836, rel_tol=1e-10))

    def test_incompatible_units(self):
        with self.assertRaises(CalculationError):
            calculate("Convert 5 kg to miles")


if __name__ == "__main__":
    unittest.main()
