"""
Real Execution Engine for Tether
Executes validated and approved plans with monitoring
"""

import time
import traceback
from typing import Dict, Any, List, Callable, Optional
from datetime import datetime
from enum import Enum
from dataclasses import dataclass


class ExecutionStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ExecutionResult:
    """Result of a plan execution"""
    plan_id: str
    status: ExecutionStatus
    start_time: datetime
    end_time: Optional[datetime]
    steps_completed: int
    total_steps: int
    actual_cost: float
    actual_time: int  # seconds
    errors: List[str]
    output: Any



class ExecutionEngine:
    """
    Real execution engine that runs validated plans
    with monitoring and error handling
    """
    
    def __init__(self, reliability_agent, logger=None):
        self.reliability_agent = reliability_agent
        self.logger = logger
        self.active_executions: Dict[str, ExecutionResult] = {}
        
        # Registry of step handlers
        self.step_handlers: Dict[str, Callable] = {}
        self._register_default_handlers()
    
    def register_step_handler(self, action: str, handler: Callable):
        """Register a handler for a specific action type"""
        self.step_handlers[action] = handler
    
    def _register_default_handlers(self):
        """Register default step handlers"""
        self.step_handlers['wait'] = self._handle_wait
        self.step_handlers['log'] = self._handle_log
        self.step_handlers['validate'] = self._handle_validate
    
    def _handle_wait(self, step: Dict[str, Any]) -> Any:
        """Default handler: wait"""
        duration = step.get('duration', 1)
        time.sleep(duration)
        return {'waited': duration}
    
    def _handle_log(self, step: Dict[str, Any]) -> Any:
        """Default handler: log message"""
        message = step.get('message', 'Step executed')
        if self.logger:
            self.logger.info(message)
        return {'logged': message}
    
    def _handle_validate(self, step: Dict[str, Any]) -> Any:
        """Default handler: validate condition"""
        condition = step.get('condition', True)
        return {'valid': condition}
    
    def execute(self, plan, simulation_result=None) -> ExecutionResult:
        """
        Execute a validated plan with monitoring
        Returns ExecutionResult with actual metrics
        """
        start_time = datetime.now()
        
        result = ExecutionResult(
            plan_id=plan.id,
            status=ExecutionStatus.RUNNING,
            start_time=start_time,
            end_time=None,
            steps_completed=0,
            total_steps=len(plan.steps),
            actual_cost=0.0,
            actual_time=0,
            errors=[],
            output={}
        )
        
        self.active_executions[plan.id] = result
        
        if self.logger:
            self.logger.info(f"Starting execution of plan {plan.id}")
        
        try:
            for i, step in enumerate(plan.steps):
                step_start = time.time()
                action = step.get('action', 'unknown')
                
                if self.logger:
                    self.logger.info(f"Executing step {i+1}/{len(plan.steps)}: {action}")
                
                # Get handler for this action
                handler = self.step_handlers.get(action)
                
                if handler is None:
                    error_msg = f"No handler registered for action: {action}"
                    result.errors.append(error_msg)
                    if self.logger:
                        self.logger.error(error_msg)
                    continue
                
                # Execute step
                try:
                    step_result = handler(step)
                    result.output[f"step_{i}"] = step_result
                    result.steps_completed += 1
                    
                    # Track tool reliability
                    step_time = time.time() - step_start
                    if 'tool' in step:
                        self.reliability_agent.record_execution(
                            tool_name=step['tool'],
                            success=True,
                            response_time=step_time
                        )
                    
                    # Track cost if specified
                    if 'cost' in step:
                        result.actual_cost += step['cost']
                
                except Exception as e:
                    error_msg = f"Step {i} failed: {str(e)}"
                    result.errors.append(error_msg)
                    
                    if self.logger:
                        self.logger.error(error_msg, {'traceback': traceback.format_exc()})
                    
                    # Track tool failure
                    step_time = time.time() - step_start
                    if 'tool' in step:
                        self.reliability_agent.record_execution(
                            tool_name=step['tool'],
                            success=False,
                            response_time=step_time
                        )
                    
                    # Decide whether to continue or abort
                    if step.get('critical', False):
                        result.status = ExecutionStatus.FAILED
                        break
            
            # Mark as success if we completed without critical failures
            if result.status == ExecutionStatus.RUNNING:
                result.status = ExecutionStatus.SUCCESS
        
        except Exception as e:
            result.status = ExecutionStatus.FAILED
            result.errors.append(f"Fatal error: {str(e)}")
            if self.logger:
                self.logger.critical(f"Execution failed for plan {plan.id}", 
                                   {'error': str(e), 'traceback': traceback.format_exc()})
        
        finally:
            # Finalize result
            result.end_time = datetime.now()
            result.actual_time = int((result.end_time - result.start_time).total_seconds())
            
            if self.logger:
                self.logger.info(f"Execution completed for plan {plan.id}", 
                               {'status': result.status.value, 
                                'steps_completed': result.steps_completed,
                                'actual_time': result.actual_time})
            
            del self.active_executions[plan.id]
        
        return result
    
    def get_execution_status(self, plan_id: str) -> Optional[ExecutionResult]:
        """Get status of currently running execution"""
        return self.active_executions.get(plan_id)
    
    def cancel_execution(self, plan_id: str) -> bool:
        """Cancel a running execution"""
        if plan_id in self.active_executions:
            self.active_executions[plan_id].status = ExecutionStatus.CANCELLED
            return True
        return False
