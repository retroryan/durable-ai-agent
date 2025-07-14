"""Performance metrics for tool selection evaluation."""

from typing import Dict, List, Set


def evaluate_tool_selection(expected: Set[str], actual: Set[str]) -> Dict[str, float]:
    """
    Evaluate tool selection performance using precision, recall, and F1 score.

    Args:
        expected: Set of expected tool names
        actual: Set of actual tool names selected

    Returns:
        Dictionary containing precision, recall, f1_score, and is_perfect_match
    """
    if not expected and not actual:
        return {
            "precision": 1.0,
            "recall": 1.0,
            "f1_score": 1.0,
            "is_perfect_match": True,
        }

    correct = expected & actual
    precision = len(correct) / len(actual) if actual else 0.0
    recall = len(correct) / len(expected) if expected else 0.0
    f1_score = (
        2 * (precision * recall) / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )

    return {
        "precision": precision,
        "recall": recall,
        "f1_score": f1_score,
        "is_perfect_match": expected == actual,
    }


class ToolSelectionMetrics:
    """Utilities for calculating and formatting tool selection metrics."""

    @staticmethod
    def evaluate_selection(expected: Set[str], actual: Set[str]) -> Dict[str, float]:
        """Evaluate tool selection performance."""
        return evaluate_tool_selection(expected, actual)

    @staticmethod
    def aggregate_metrics(evaluations: List[Dict[str, float]]) -> Dict[str, float]:
        """
        Calculate aggregate metrics from multiple evaluations.

        Args:
            evaluations: List of evaluation dictionaries

        Returns:
            Dictionary with average metrics and counts
        """
        if not evaluations:
            return {
                "avg_precision": 0.0,
                "avg_recall": 0.0,
                "avg_f1_score": 0.0,
                "perfect_matches": 0,
                "total_evaluations": 0,
            }

        total_precision = sum(e["precision"] for e in evaluations)
        total_recall = sum(e["recall"] for e in evaluations)
        total_f1 = sum(e["f1_score"] for e in evaluations)
        perfect_matches = sum(
            1 for e in evaluations if e.get("is_perfect_match", False)
        )

        n = len(evaluations)

        return {
            "avg_precision": total_precision / n,
            "avg_recall": total_recall / n,
            "avg_f1_score": total_f1 / n,
            "perfect_matches": perfect_matches,
            "total_evaluations": n,
        }

    @staticmethod
    def format_evaluation_result(
        expected: Set[str], actual: Set[str], evaluation: Dict[str, float]
    ) -> str:
        """
        Format evaluation results for console output.

        Args:
            expected: Expected tool set
            actual: Actual tool set
            evaluation: Evaluation metrics dictionary

        Returns:
            Formatted string for console output
        """
        lines = []

        # Show expected vs actual
        lines.append(f"Expected: {sorted(expected)}")
        lines.append(f"Actual: {sorted(actual)}")

        # Show what was right/wrong
        correct = expected & actual
        missed = expected - actual
        extra = actual - expected

        if correct:
            lines.append(f"✅ Correct: {sorted(correct)}")
        if missed:
            lines.append(f"❌ Missed: {sorted(missed)}")
        if extra:
            lines.append(f"➕ Extra: {sorted(extra)}")

        # Show metrics
        lines.append(
            f"Precision: {evaluation['precision']:.2f}, "
            f"Recall: {evaluation['recall']:.2f}, "
            f"F1: {evaluation['f1_score']:.2f}"
        )

        if evaluation.get("is_perfect_match"):
            lines.append("✨ Perfect match!")

        return "\n".join(lines)
