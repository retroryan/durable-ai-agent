"""Helper utilities for integration tests."""
from typing import Any, Dict


class WorkflowAssertions:
    """Assertions for workflow testing."""

    @staticmethod
    def assert_workflow_started(response: Dict[str, Any]) -> None:
        """
        Assert that a workflow was successfully started.

        Args:
            response: The API response
        """
        assert "workflow_id" in response
        assert response["workflow_id"].startswith("durable-agent-")
        assert "status" in response
        assert "query_count" in response

    @staticmethod
    def assert_workflow_completed(response: Dict[str, Any]) -> None:
        """
        Assert that a workflow completed successfully.

        Args:
            response: The API response
        """
        assert response["status"] == "completed"
        assert "last_response" in response

        # Check the response structure
        last_response = response["last_response"]
        assert "message" in last_response
        assert "event_count" in last_response
        assert "query_count" in last_response

    @staticmethod
    def assert_events_found(response: Dict[str, Any]) -> None:
        """
        Assert that events were found in the response.

        Args:
            response: The API response
        """
        last_response = response.get("last_response", {})
        assert last_response.get("event_count", 0) >= 0

        message = last_response.get("message", "")
        assert message.startswith("Found")
        assert "Melbourne" in message

    @staticmethod
    def assert_query_count_incremented(
        response1: Dict[str, Any],
        response2: Dict[str, Any],
    ) -> None:
        """
        Assert that query count was incremented between responses.

        Args:
            response1: First response
            response2: Second response
        """
        count1 = response1.get("query_count", 0)
        count2 = response2.get("query_count", 0)

        # If the responses have last_response, check that too
        if "last_response" in response1:
            count1 = response1["last_response"].get("query_count", count1)
        if "last_response" in response2:
            count2 = response2["last_response"].get("query_count", count2)

        assert count2 > count1, f"Expected count2 ({count2}) > count1 ({count1})"

    @staticmethod
    def get_workflow_id(response: Dict[str, Any]) -> str:
        """
        Extract workflow ID from response.

        Args:
            response: The API response

        Returns:
            The workflow ID
        """
        assert "workflow_id" in response
        return response["workflow_id"]

    @staticmethod
    def get_event_count(response: Dict[str, Any]) -> int:
        """
        Extract event count from response.

        Args:
            response: The API response

        Returns:
            The event count
        """
        if "last_response" in response:
            return response["last_response"].get("event_count", 0)
        return response.get("event_count", 0)

    @staticmethod
    def get_query_count(response: Dict[str, Any]) -> int:
        """
        Extract query count from response.

        Args:
            response: The API response

        Returns:
            The query count
        """
        if "last_response" in response:
            return response["last_response"].get("query_count", 0)
        return response.get("query_count", 0)
