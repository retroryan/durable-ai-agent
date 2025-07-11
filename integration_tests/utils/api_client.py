"""API client for integration testing the durable AI agent."""
import asyncio
from typing import Any, Dict, Optional

import httpx


class DurableAgentAPIClient:
    """HTTP client wrapper for interacting with the durable AI agent API."""

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        timeout: int = 30,
    ):
        """
        Initialize the API client.

        Args:
            base_url: The base URL of the API server
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the API.

        Returns:
            Health status response
        """
        response = await self.client.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()

    async def chat(
        self,
        message: str,
        workflow_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send a chat message to start or continue a workflow.

        Args:
            message: The message to send
            workflow_id: Optional workflow ID to continue existing workflow

        Returns:
            Workflow state response
        """
        payload = {"message": message}
        if workflow_id:
            payload["workflow_id"] = workflow_id

        response = await self.client.post(
            f"{self.base_url}/chat",
            json=payload,
        )
        response.raise_for_status()
        return response.json()

    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """
        Get the status of a workflow.

        Args:
            workflow_id: The workflow ID

        Returns:
            Workflow status response
        """
        response = await self.client.get(
            f"{self.base_url}/workflow/{workflow_id}/status"
        )
        response.raise_for_status()
        return response.json()

    async def query_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """
        Query a workflow for its internal state.

        Args:
            workflow_id: The workflow ID

        Returns:
            Workflow query response
        """
        response = await self.client.get(
            f"{self.base_url}/workflow/{workflow_id}/query"
        )
        response.raise_for_status()
        return response.json()

    async def wait_for_workflow_completion(
        self,
        workflow_id: str,
        timeout: int = 30,
        poll_interval: float = 0.5,
    ) -> Dict[str, Any]:
        """
        Wait for a workflow to complete.

        Args:
            workflow_id: The workflow ID
            timeout: Maximum time to wait in seconds
            poll_interval: Time between status checks

        Returns:
            Final workflow status

        Raises:
            TimeoutError: If workflow doesn't complete within timeout
        """
        start_time = asyncio.get_event_loop().time()

        while asyncio.get_event_loop().time() - start_time < timeout:
            status = await self.get_workflow_status(workflow_id)

            if status.get("status") == "completed":
                return status

            await asyncio.sleep(poll_interval)

        raise TimeoutError(f"Workflow {workflow_id} did not complete within {timeout}s")

    async def create_and_wait(
        self,
        message: str,
        workflow_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a workflow and wait for it to complete.

        Args:
            message: The message to send
            workflow_id: Optional workflow ID

        Returns:
            Final workflow state
        """
        # Start workflow
        result = await self.chat(message, workflow_id)

        # Wait for completion (workflow completes immediately in our simple case)
        # In a real system, you might need to poll for completion
        return result
