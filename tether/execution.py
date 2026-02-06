"""
Execution Engine for Tether
Handles actual plan execution with monitoring
"""

import time
import logging
from typing import Dict, Any, Callable, Optional
from datetime import datetime
from .models import Plan, ExecutionResult, ExecutionStatus
from .agents import ToolReliabilityAgent

logger = logging.getLogger(__name__)


class ExecutionEngine:
    """
    Executes validated plans with real-time monitoring
    """
    
    def __init__(self, reliability_agent: ToolReliabilityAgent):
        self.reliability_agent = reliability_agent
        self.active_executions: Dict[str, ExecutionResult] = {}
        self.execution_callbacks: Dict[str, Callable] = {}
    
    def execute_plan(
        self,
        plan: Plan,
        step_executor: Callable[[Dict[str, Any]], Any]
    ) -> ExecutionResult:
        """
        Execute a plan step by step with monitoring
        
        Args:
            plan: The validated plan to execute
            step_executor: Callback function that executes individual steps
        
        Returns:
            ExecutionResult with outcome
        """
        result = ExecutionResult(
            plan_id=plan.id,
            status=ExecutionStatus.EXECUTING,
            started_at=datetime.now(),
            completed_at=None,
            actual_time=None,
            actual_cost=None,
            steps_completed=0,
            steps_total=len(plan.steps)
        )
        
        self.active_executions[plan.id] = result
        start_time = time.time()
        total_cost = 0.0
        
        try:
            for i, step in enumerate(plan.steps):
                logger.info(f"Executing step {i+1}/{len(plan.steps)}: {step}")
                
                step_start = time.time()
                
                try:
                    # Execute the step
                    step_result = step_executor(step)
                    step_duration = time.time() - step_start
                    
                    # Record successful execution
                    tool_name = step.get('action', 'unknown')
                    self.reliability_agent.record_execution(
                        tool_name, True, step_duration
                    )
                    
                    result.steps_completed += 1
                    
                    # Track cost if available
                    if isinstance(step_result, dict) and 'cost' in step_result:
                        total_cost += step_result['cost']
                    
                except Exception as e:
                    # Record failed execution
                    tool_name = step.get('action', 'unknown')
                    step_duration = time.time() - step_start
                    self.reliability_agent.record_execution(
                        tool_name, False, step_duration
                    )
                    
                    result.status = ExecutionStatus.FAILED
                    result.error = str(e)
                    logger.error(f"Step {i+1} failed: {e}")
                    raise
            
            # Success
            result.status = ExecutionStatus.COMPLETED
            result.completed_at = datetime.now()
            result.actual_time = int(time.time() - start_time)
            result.actual_cost = total_cost
            
        except Exception as e:
            result.status = ExecutionStatus.FAILED
            result.error = str(e)
            result.completed_at = datetime.now()
            result.actual_time = int(time.time() - start_time)
        
        finally:
            del self.active_executions[plan.id]
        
        return result
    
    def get_execution_status(self, plan_id: str) -> Optional[ExecutionResult]:
        """Get current execution status"""
        return self.active_executions.get(plan_id)
