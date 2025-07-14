"""Console output formatting utilities."""

import sys
from typing import Any, Dict, List, Optional


class ConsoleFormatter:
    """Utilities for formatting console output."""

    @staticmethod
    def section_separator(char: str = "=", width: int = 80) -> str:
        """Create a section separator line."""
        return char * width

    @staticmethod
    def section_header(title: str, char: str = "=", width: int = 80) -> str:
        """Create a centered section header."""
        separator = char * width
        centered_title = title.center(width)
        return f"\n{separator}\n{centered_title}\n{separator}"

    @staticmethod
    def test_progress(current: int, total: int, test_name: str) -> str:
        """Format test progress indicator."""
        return f"\n[{current}/{total}] Testing: {test_name}"

    @staticmethod
    def success_message(message: str) -> str:
        """Format a success message with green color if supported."""
        if sys.stdout.isatty():
            return f"\033[92m✓ {message}\033[0m"
        return f"✓ {message}"

    @staticmethod
    def error_message(message: str) -> str:
        """Format an error message with red color if supported."""
        if sys.stdout.isatty():
            return f"\033[91m✗ {message}\033[0m"
        return f"✗ {message}"

    @staticmethod
    def warning_message(message: str) -> str:
        """Format a warning message with yellow color if supported."""
        if sys.stdout.isatty():
            return f"\033[93m⚠ {message}\033[0m"
        return f"⚠ {message}"

    @staticmethod
    def performance_bar(
        score: float, width: int = 50, filled_char: str = "█", empty_char: str = "░"
    ) -> str:
        """
        Create a visual performance bar.

        Args:
            score: Score between 0 and 1
            width: Width of the bar in characters
            filled_char: Character to use for filled portion
            empty_char: Character to use for empty portion

        Returns:
            Visual bar representation
        """
        filled_width = int(score * width)
        empty_width = width - filled_width
        bar = filled_char * filled_width + empty_char * empty_width
        percentage = score * 100
        return f"[{bar}] {percentage:.1f}%"

    @staticmethod
    def format_summary_table(
        data: Dict[str, Any], title: Optional[str] = None, width: int = 60
    ) -> str:
        """
        Format a summary table with key-value pairs.

        Args:
            data: Dictionary of data to display
            title: Optional title for the table
            width: Width of the table

        Returns:
            Formatted table string
        """
        lines = []

        if title:
            lines.append(ConsoleFormatter.section_header(title, "-", width))
        else:
            lines.append(ConsoleFormatter.section_separator("-", width))

        # Calculate max key width for alignment
        max_key_width = max(len(str(k)) for k in data.keys())

        for key, value in data.items():
            # Format value based on type
            if isinstance(value, float):
                if 0 <= value <= 1:
                    formatted_value = f"{value:.2%}"
                else:
                    formatted_value = f"{value:.2f}"
            elif isinstance(value, int):
                formatted_value = str(value)
            else:
                formatted_value = str(value)

            lines.append(f"{str(key).ljust(max_key_width)} : {formatted_value}")

        lines.append(ConsoleFormatter.section_separator("-", width))

        return "\n".join(lines)

    @staticmethod
    def format_metrics_summary(metrics: Dict[str, float]) -> List[str]:
        """
        Format evaluation metrics for display.

        Args:
            metrics: Dictionary containing precision, recall, f1_score

        Returns:
            List of formatted lines
        """
        lines = []

        if "precision" in metrics:
            lines.append(f"Precision: {metrics['precision']:.2f}")
        if "recall" in metrics:
            lines.append(f"Recall: {metrics['recall']:.2f}")
        if "f1_score" in metrics:
            lines.append(f"F1 Score: {metrics['f1_score']:.2f}")

        if metrics.get("is_perfect_match"):
            lines.append("✨ Perfect match!")

        return lines

    @staticmethod
    def format_tool_comparison(expected: List[str], actual: List[str]) -> List[str]:
        """
        Format tool comparison showing differences.

        Args:
            expected: Expected tools
            actual: Actual tools selected

        Returns:
            List of formatted lines
        """
        lines = []

        expected_set = set(expected)
        actual_set = set(actual)

        correct = expected_set & actual_set
        missed = expected_set - actual_set
        extra = actual_set - expected_set

        lines.append(f"Expected: {sorted(expected)}")
        lines.append(f"Actual: {sorted(actual)}")

        if correct:
            lines.append(f"✅ Correct: {sorted(correct)}")
        if missed:
            lines.append(f"❌ Missed: {sorted(missed)}")
        if extra:
            lines.append(f"➕ Extra: {sorted(extra)}")

        return lines
