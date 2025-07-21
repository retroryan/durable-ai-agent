"""
Monty Python Workflow - Demonstrates infinite loop workflow with streaming updates.
"""
from datetime import timedelta
import asyncio
from temporalio import workflow
from temporalio.common import RetryPolicy
from dataclasses import dataclass
from typing import Dict, Optional
from activities.monty_python_quote_activity import get_random_monty_python_quote, QuoteResult


@dataclass
class MontyPythonResult:
    """Result of the Monty Python workflow."""
    final_status: str
    total_iterations: int
    total_quotes_delivered: int
    workflow_id: str
    total_runtime: float


@workflow.defn
class MontyPythonWorkflow:
    """Infinite loop workflow that continuously quotes Monty Python."""
    
    def __init__(self):
        self.start_time: Optional[float] = None
        self.current_sleep_duration: Optional[int] = None
        self.progress: int = 0
        self.status: str = "initializing"
        self.selected_quote: Optional[str] = None
        self.iteration_count: int = 0
        self.total_quotes_delivered: int = 0
        self.should_exit: bool = False
        self.current_iteration_start: Optional[float] = None
    
    @workflow.run
    async def run(self) -> MontyPythonResult:
        """Execute infinite loop workflow calling activity for quotes."""
        self.start_time = workflow.now().timestamp()
        
        # Infinite loop - will run until cancelled or signaled to stop
        while not self.should_exit:
            self.iteration_count += 1
            self.current_iteration_start = workflow.now().timestamp()
            self.status = f"iteration_{self.iteration_count}_fetching_quote"
            
            # Call activity to get random quote
            quote_result: QuoteResult = await workflow.execute_activity(
                get_random_monty_python_quote,
                start_to_close_timeout=timedelta(seconds=10),
                retry_policy=RetryPolicy(
                    maximum_attempts=3,
                    initial_interval=timedelta(seconds=1)
                )
            )
            
            # Update state with the quote
            self.selected_quote = quote_result.quote
            self.total_quotes_delivered += 1
            self.status = f"delivered_quote_{self.total_quotes_delivered}"
            
            # Random sleep between quotes (simulating streaming interval)
            self.current_sleep_duration = workflow.random().randint(2, 5)
            self.progress = 0
            
            # Sleep with progress updates
            start = workflow.now()
            while True:
                elapsed = (workflow.now() - start).total_seconds()
                self.progress = min(int((elapsed / self.current_sleep_duration) * 100), 100)
                
                if elapsed >= self.current_sleep_duration:
                    break
                
                # Check for exit signal during sleep
                if self.should_exit:
                    break
                    
                await asyncio.sleep(0.5)
        
        # Workflow exits gracefully when signaled
        return MontyPythonResult(
            final_status="gracefully_terminated",
            total_iterations=self.iteration_count,
            total_quotes_delivered=self.total_quotes_delivered,
            workflow_id=workflow.info().workflow_id,
            total_runtime=(workflow.now().timestamp() - self.start_time)
        )
    
    @workflow.signal
    async def stop_workflow(self):
        """Signal to gracefully stop the workflow."""
        self.should_exit = True
        self.status = "stopping"
    
    @workflow.query
    def get_progress(self) -> Dict:
        """Query current progress and status."""
        iteration_elapsed = 0
        if self.current_iteration_start:
            iteration_elapsed = workflow.now().timestamp() - self.current_iteration_start
            
        return {
            "progress": self.progress,
            "status": self.status,
            "current_sleep_duration": self.current_sleep_duration,
            "iteration_count": self.iteration_count,
            "total_quotes_delivered": self.total_quotes_delivered,
            "current_quote": self.selected_quote,
            "total_elapsed": (workflow.now().timestamp() - self.start_time) if self.start_time else 0,
            "iteration_elapsed": iteration_elapsed,
            "should_exit": self.should_exit
        }