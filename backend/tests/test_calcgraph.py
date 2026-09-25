import math
import unittest

from app.calcgraph import (
    ClarificationNeeded,
    GraphVerificationError,
    compile_query,
    execute_graph,
    verify_graph,
)


class CalcGraphTests(unittest.TestCase):
    def test_emi_compiles_to_typed_graph(self):
        graph = compile_query("EMI for ₹10 lakh at 8.5% for 5 years")
        self.assertEqual(graph.calculator, "emi")
        self.assertEqual([node.semantic_type for node in graph.nodes], ["Money", "Rate", "Duration", "MoneyPerMonth"])
        self.assertEqual(graph.nodes[-1].operation, "finance.emi")
        self.assertEqual(graph.nodes[-1].inputs["principal"], "principal")

    def test_incomplete_goal_produces_structured_questions(self):
        with self.assertRaises(ClarificationNeeded) as context:
            compile_query("Calculate my loan EMI")
        self.assertEqual(context.exception.calculator, "emi")
        self.assertGreaterEqual(len(context.exception.questions), 3)

    def test_valid_graph_passes_static_verification(self):
        report = verify_graph(compile_query("Calculate (18 + 6) * 4 / 3"))
        self.assertTrue(report.valid)
        self.assertEqual(report.topological_order, ["expression", "result"])
        self.assertTrue(all(check.status == "pass" for check in report.checks))

    def test_unknown_operation_is_rejected(self):
        graph = compile_query("Calculate 2 + 2")
        graph.nodes[-1].operation = "python.exec"
        report = verify_graph(graph)
        self.assertFalse(report.valid)
        self.assertTrue(any(check.id == "operation.allowlist" and check.status == "fail" for check in report.checks))
        with self.assertRaises(GraphVerificationError):
            execute_graph(graph)

    def test_formula_identity_and_domain_cannot_be_forged(self):
        graph = compile_query("Calculate 2 + 2")
        graph.calculator = "statistics"
        graph.nodes[-1].metadata["formula_version"] = "999.0.0"
        report = verify_graph(graph)
        self.assertFalse(report.valid)
        failed = {check.id for check in report.checks if check.status == "fail"}
        self.assertIn("operation.domain", failed)
        self.assertIn("operation.formula_version", failed)

    def test_input_node_cannot_be_a_declared_result(self):
        graph = compile_query("Calculate 2 + 2")
        graph.output_node_ids = ["expression"]
        report = verify_graph(graph)
        self.assertFalse(report.valid)
        self.assertTrue(any(check.id == "graph.output_kinds" and check.status == "fail" for check in report.checks))

    def test_cycle_is_rejected(self):
        graph = compile_query("Calculate 2 + 2")
        graph.nodes[-1].inputs["expression"] = "result"
        report = verify_graph(graph)
        self.assertFalse(report.valid)
        self.assertTrue(any("Cycle detected" in error for error in report.errors))

    def test_incompatible_unit_dimensions_are_rejected(self):
        graph = compile_query("Convert 5 kg to miles")
        report = verify_graph(graph)
        self.assertFalse(report.valid)
        self.assertTrue(any(check.id == "units.dimension" and check.status == "fail" for check in report.checks))

    def test_execution_returns_result_and_evidence_receipt(self):
        execution = execute_graph(compile_query("EMI for ₹10 lakh at 8.5% for 5 years"))
        self.assertTrue(math.isclose(execution["calculation"]["value"], 20516.53, abs_tol=0.02))
        self.assertTrue(execution["verification"]["valid"])
        self.assertEqual(len(execution["receipt"]["graph_fingerprint"]), 64)
        self.assertEqual(len(execution["receipt"]["reproducibility_hash"]), 64)

    def test_multi_operation_finance_goal_builds_depth_four_graph(self):
        graph = compile_query(
            "Calculate the EMI, total payment, total interest, and interest percentage "
            "for a loan of INR 1000000 at 8.5% for 5 years"
        )
        operations = [node.operation for node in graph.nodes if node.kind == "operation"]
        self.assertEqual(
            operations,
            [
                "finance.emi",
                "finance.total_payment",
                "finance.total_interest",
                "finance.interest_share",
            ],
        )
        execution = execute_graph(graph)
        self.assertEqual(execution["receipt"]["graph_metrics"]["graph_depth"], 4)
        self.assertEqual(execution["receipt"]["graph_metrics"]["operation_count"], 4)
        self.assertEqual(len(execution["calculation"]["value"]), 4)
        self.assertIn("Interest share", execution["calculation"]["answer"])

    def test_input_value_must_conform_to_registered_semantic_type(self):
        graph = compile_query("EMI for INR 1000000 at 8.5% for 5 years")
        graph.nodes[0].value = "ten lakh"
        report = verify_graph(graph)
        self.assertFalse(report.valid)
        self.assertTrue(any(check.id == "input.value_type" and check.status == "fail" for check in report.checks))

    def test_unknown_semantic_type_is_rejected(self):
        graph = compile_query("Calculate 2 + 2")
        graph.nodes[0].semantic_type = "MysteryScalar"
        report = verify_graph(graph)
        self.assertFalse(report.valid)
        self.assertTrue(
            any(check.id == "node.semantic_type_registered" and check.status == "fail" for check in report.checks)
        )

    def test_same_graph_and_result_are_reproducible(self):
        query = "Find mean, median and standard deviation of 12, 15, 18, 21"
        first = execute_graph(compile_query(query))
        second = execute_graph(compile_query(query))
        self.assertNotEqual(first["receipt"]["receipt_id"], second["receipt"]["receipt_id"])
        self.assertEqual(first["receipt"]["graph_fingerprint"], second["receipt"]["graph_fingerprint"])
        self.assertEqual(first["receipt"]["reproducibility_hash"], second["receipt"]["reproducibility_hash"])

    def test_advanced_domain_is_typed_verified_and_executed(self):
        graph = compile_query("Solve 3x + 7 = 25")
        self.assertEqual(graph.calculator, "advanced")
        self.assertEqual(graph.nodes[-1].semantic_type, "CalculationResult")
        report = verify_graph(graph)
        self.assertTrue(report.valid, report.errors)
        execution = execute_graph(graph)
        self.assertEqual(execution["calculation"]["value"], 6)
        self.assertTrue(execution["receipt"]["verification_summary"]["valid"])


if __name__ == "__main__":
    unittest.main()
