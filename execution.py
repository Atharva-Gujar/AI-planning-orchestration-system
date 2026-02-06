"""
Execution Engine for Tether
Actually executes approved plans with monitoring
"""
import time
from typing import Dict, Any, Callable, Optional, List
from datetime import datetime
from dataclasses import dataclass

from tether import Plan, ToolReliabilityAgent
from logger import get_logger


@dataclass
class ExecutionStep:
    """Represents a single execution step"""
    step_id: str
    action: str
    params: Dict[str, Any]
    timeout: int = 300  # 5 minutes default
    retry_count: int = 3


@dataclass
class ExecutionResult:
    """Result of an execution"""
    plan_id: str
    success: bool
    start_time: datetime
    end_time: datetime
    duration: float
    actual_cost: float
    steps_completed: int
    total_steps: int
    errors: List[str]
    metadata: Dict[str, Any]


class ExecutionEngine:
    """
    Executes approved plans with real-time monitoring
    """
    
    def __init__(
        self,
        reliability_agent: ToolReliabilityAgent,
        tool_registry: Optional[Dict[str, Callable]] = None
    ):
        self.reliability_agent = reliability_agent
        self.tool_registry = tool_registry or {}
        self.logger = get_logger()
        self.active_executions = {}
    
    def register_tool(self, name: str, func: Callable):
        """Register a tool function for execution"""
        self.tool_registry[name] = func
        self.reliability_agent.register_tool(name)
    
    def execute_plan(
        self,
        plan: Plan,
        on_step_complete: Optional[Callable] = None,
        on_error: Optional[Callable] = None
    ) -> ExecutionResult:
        """
        Execute a plan step by step with monitoring
        """
        start_time = datetime.now()
        self.logger.log_execution_start(plan.id)
        
        steps_completed = 0
        total_steps = len(plan.steps)
        errors = []
        actual_cost = 0.0
        
        try:
            for idx, step in enumerate(plan.steps):
                step_id = f"{plan.id}_step_{idx}"
                action = step.get('action')
                
                if action not in self.tool_registry:
                    error_msg = f"Unknown action: {action}"
                    errors.append(error_msg)
                    self.logger.error(f"Step failed: {step_id} - {error_msg}")
                    
                    if on_error:
                        on_error(step_id, error_msg)
                    continue
                
                # Execute step with monitoring
                step_start = time.time()
                success = False
                
                try:
                    tool_func = self.tool_registry[action]
                    result = tool_func(step)
                    success = True
                    steps_completed += 1
                    
                    # Track cost if provided
                    if isinstance(result, dict) and 'cost' in result:
                        actual_cost += result['cost']
                    
                except Exception as e:
                    error_msg = f"Step execution failed: {str(e)}"
                    errors.append(error_msg)
                    self.logger.error(f"Step {step_id} failed: {error_msg}")
                    
                    if on_error:
                        on_error(step_id, error_msg)
                
                finally:
                    # Record execution metrics
                    step_duration = time.time() - step_start
                    self.reliability_agent.record_execution(
                        action,
                        success,
                        step_duration
                    )
                    
                    if on_step_complete:
                        on_step_complete(step_id, success, step_duration)
        
        except Exception as e:
            error_msg = f"Plan execution failed: {str(e)}"
            errors.append(error_msg)
            self.logger.error(error_msg)
        
        # Calculate results
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        success = len(errors) == 0 and steps_completed == total_steps
        
        result = ExecutionResult(
            plan_id=plan.id,
            success=success,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            actual_cost=actual_cost,
            steps_completed=steps_completed,
            total_steps=total_steps,
            errors=errors,
            metadata={
                'estimated_time': plan.estimated_time,
                'estimated_cost': plan.estimated_cost,
                'time_variance': duration - plan.estimated_time,
                'cost_variance': actual_cost - plan.estimated_cost
            }
        )
        
        self.logger.log_execution_complete(
            plan.id,
            'SUCCESS' if success else 'FAILED',
            duration
        )
        
        return result
    
    def execute_async(
        self,
        plan: Plan,
        callback: Optional[Callable] = None
    ):
        """
        Execute plan asynchronously (simplified version)
        In production, this would use proper async/threading
        """
        import threading
        
        def _execute():
            result = self.execute_plan(plan)
            if callback:
                callback(result)
        
        thread = threading.Thread(target=_execute)
        thread.start()
        
        self.active_executions[plan.id] = thread
        return plan.id
    
    def get_execution_status(self, plan_id: str) -> Optional[str]:
        """Get status of async execution"""
        if plan_id not in self.active_executions:
            return None
        
        thread = self.active_executions[plan_id]
        return "RUNNING" if thread.is_alive() else "COMPLETED"
    
    def wait_for_completion(self, plan_id: str, timeout: Optional[float] = None):
        """Wait for async execution to complete"""
        if plan_id in self.active_executions:
            self.active_executions[plan_id].join(timeout)


# Example tool implementations

def example_scraper_tool(step: Dict[str, Any]) -> Dict[str, Any]:
    """Example web scraper tool"""
    count = step.get('count', 10)
    
    # Simulate scraping
    time.sleep(0.1)
    
    return {
        'success': True,
        'items_scraped': count,
        'cost': count * 0.01  # $0.01 per item
    }


def example_analysis_tool(step: Dict[str, Any]) -> Dict[str, Any]:
    """Example analysis tool"""
    method = step.get('method', 'sentiment')
    
    # Simulate analysis
    time.sleep(0.2)
    
    return {
        'success': True,
        'method': method,
        'cost': 0.50
    }


def example_report_tool(step: Dict[str, Any]) -> Dict[str, Any]:
    """Example report generation tool"""
    format_type = step.get('format', 'pdf')
    
    # Simulate report generation
    time.sleep(0.15)
    
    return {
        'success': True,
        'format': format_type,
        'cost': 0.10
    }


if __name__ == "__main__":
    # Example usage
    from tether import Plan, ToolReliabilityAgent
    
    # Create reliability agent
    reliability = ToolReliabilityAgent()
    
    # Create execution engine
    engine = ExecutionEngine(reliability)
    
    # Register tools
    engine.register_tool('scrape', example_scraper_tool)
    engine.register_tool('analyze', example_analysis_tool)
    engine.register_tool('report', example_report_tool)
    
    # Create test plan
    test_plan = Plan(
        id="exec_test_001",
        description="Test execution",
        steps=[
            {"action": "scrape", "count": 100},
            {"action": "analyze", "method": "sentiment"},
            {"action": "report", "format": "pdf"}
        ],
        estimated_time=60,
        estimated_cost=5.0,
        required_permissions=["read"]
    )
    
    # Execute plan
    def on_step(step_id, success, duration):
        print(f"  ✓ {step_id}: {'SUCCESS' if success else 'FAILED'} ({duration:.2f}s)")
    
    print("Executing plan...")
    result = engine.execute_plan(test_plan, on_step_complete=on_step)
    
    print(f"\nExecution Result:")
    print(f"  Success: {result.success}")
    print(f"  Duration: {result.duration:.2f}s")
    print(f"  Actual Cost: ${result.actual_cost:.2f}")
    print(f"  Steps: {result.steps_completed}/{result.total_steps}")
