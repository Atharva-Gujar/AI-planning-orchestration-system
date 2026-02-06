"""
Core Tether orchestrator with full functionality
"""

import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime

from .models import (
    Plan, Constraint, ConstraintType, RiskLevel,
    SimulationResult, ExecutionResult, ExecutionStatus
)
from .agents import (
    ConstraintReasoningAgent,
    StrategicScenarioSimulator,
    ToolReliabilityAgent,
    HumanInLoopAgent
)
from .execution import ExecutionEngine
from .persistence import Database
from .config import Config

logger = logging.getLogger(__name__)


class TetherOrchestrator:
    """
    Main orchestrator that coordinates all agents
    This is the primary interface for the Tether system
    """
    
    def __init__(
        self,
        constraints: Optional[Dict[str, Any]] = None,
        simulation_depth: int = 3,
        reliability_threshold: float = 0.85,
        config: Optional[Config] = None,
        database: Optional[Database] = None
    ):
        # Load or use provided config
        self.config = config or Config()
        
        # Initialize database
        self.db = database or Database(self.config.get('database.path', 'tether.db'))
        
        # Setup logging
        log_level = getattr(logging, self.config.get('logging.level', 'INFO'))
        logging.basicConfig(
            level=log_level,
            filename=self.config.get('logging.file', 'tether.log'),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Initialize constraints from config or parameters
        if constraints is None:
            constraints = self.config.get('constraints', {})
        
        # Convert constraints to Constraint objects
        constraint_objects = {}
        for key, value in constraints.items():
            if key in ['time_limit', 'budget', 'permissions', 'regulations']:
                try:
                    constraint_type = ConstraintType(key.replace('_limit', ''))
                    constraint_objects[key] = Constraint(constraint_type, value)
                except ValueError:
                    constraint_objects[key] = Constraint(ConstraintType.TIME, value)
        
        # Initialize all agents
        self.constraint_agent = ConstraintReasoningAgent(constraint_objects)
        
        sim_depth = simulation_depth or self.config.get('simulation.depth', 3)
        self.simulator = StrategicScenarioSimulator(sim_depth)
        
        rel_threshold = reliability_threshold or self.config.get('reliability.threshold', 0.85)
        self.reliability_agent = ToolReliabilityAgent(rel_threshold)
        
        self.human_loop_agent = HumanInLoopAgent()
        
        # Initialize execution engine
        self.execution_engine = ExecutionEngine(self.reliability_agent)
        
        self.execution_log = []
    
    def execute_plan(
        self,
        plan: Plan,
        approval_callback: Optional[Callable] = None,
        step_executor: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Main execution pipeline:
        1. Constraint validation
        2. Scenario simulation
        3. Human approval (if needed)
        4. Monitored execution
        """
        logger.info(f"Starting execution pipeline for plan {plan.id}")
        
        result = {
            'plan_id': plan.id,
            'status': 'pending',
            'timestamp': datetime.now(),
            'stages': {}
        }
        
        # Save plan to database
        self.db.save_plan({
            'id': plan.id,
            'description': plan.description,
            'steps': plan.steps,
            'estimated_time': plan.estimated_time,
            'estimated_cost': plan.estimated_cost,
            'required_permissions': plan.required_permissions,
            'metadata': plan.metadata,
            'created_at': plan.created_at.isoformat() if hasattr(plan.created_at, 'isoformat') else str(plan.created_at)
        })
        
        # Stage 1: Constraint Validation
        logger.info("Stage 1: Constraint validation")
        valid, violations = self.constraint_agent.validate_plan(plan)
        result['stages']['constraint_validation'] = {
            'valid': valid,
            'violations': violations
        }
        
        if not valid:
            result['status'] = 'rejected'
            result['reason'] = 'Constraint violations'
            suggestions = self.constraint_agent.suggest_modifications(plan, violations)
            result['suggestions'] = suggestions
            logger.warning(f"Plan {plan.id} rejected: {violations}")
            return result
        
        # Stage 2: Scenario Simulation
        logger.info("Stage 2: Scenario simulation")
        simulations = self.simulator.simulate_paths(
            plan,
            num_paths=self.config.get('simulation.num_paths', 3)
        )
        best_simulation = max(simulations, key=lambda s: s.success_probability)
        result['stages']['simulation'] = {
            'paths_explored': len(simulations),
            'recommended_path': best_simulation.path_id,
            'success_probability': best_simulation.success_probability,
            'risk_level': best_simulation.risk_level.value
        }
        
        # Stage 3: Human Approval (if needed)
        logger.info("Stage 3: Approval check")
        needs_approval = self.human_loop_agent.should_request_approval(plan, best_simulation)
        result['stages']['approval'] = {'required': needs_approval}
        
        if needs_approval:
            approval_request = self.human_loop_agent.create_approval_request(
                plan, best_simulation, violations if not valid else None
            )
            result['stages']['approval']['request'] = {
                'decision_id': approval_request.decision_id,
                'context': approval_request.context,
                'risk_level': approval_request.risk_level.value,
                'recommended_approver': approval_request.recommended_approver,
                'urgency': approval_request.urgency
            }
            
            if approval_callback:
                logger.info("Requesting human approval")
                approved = approval_callback(approval_request)
                result['stages']['approval']['approved'] = approved
                
                if not approved:
                    result['status'] = 'rejected'
                    result['reason'] = 'Human approval denied'
                    logger.warning(f"Plan {plan.id} rejected by human")
                    return result
            else:
                result['status'] = 'awaiting_approval'
                logger.info(f"Plan {plan.id} awaiting approval")
                return result
        
        # Stage 4: Execution (if step_executor provided)
        if step_executor:
            logger.info("Stage 4: Executing plan")
            execution_result = self.execution_engine.execute_plan(plan, step_executor)
            
            # Save execution to database
            self.db.save_execution({
                'plan_id': execution_result.plan_id,
                'status': execution_result.status.value,
                'started_at': execution_result.started_at.isoformat(),
                'completed_at': execution_result.completed_at.isoformat() if execution_result.completed_at else None,
                'actual_time': execution_result.actual_time,
                'actual_cost': execution_result.actual_cost,
                'steps_completed': execution_result.steps_completed,
                'steps_total': execution_result.steps_total,
                'error': execution_result.error,
                'output': execution_result.output
            })
            
            result['execution'] = {
                'status': execution_result.status.value,
                'steps_completed': execution_result.steps_completed,
                'actual_time': execution_result.actual_time,
                'actual_cost': execution_result.actual_cost,
                'error': execution_result.error
            }
            
            result['status'] = execution_result.status.value
        else:
            result['status'] = 'approved'
            result['ready_for_execution'] = True
        
        result['recommended_simulation'] = {
            'path_id': best_simulation.path_id,
            'success_probability': best_simulation.success_probability,
            'estimated_time': best_simulation.estimated_time,
            'estimated_cost': best_simulation.estimated_cost,
            'risk_level': best_simulation.risk_level.value
        }
        
        self.execution_log.append(result)
        logger.info(f"Plan {plan.id} processing complete: {result['status']}")
        return result
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status"""
        unreliable_tools = self.reliability_agent.get_unreliable_tools()
        
        return {
            'timestamp': datetime.now().isoformat(),
            'total_executions': len(self.execution_log),
            'unreliable_tools': unreliable_tools,
            'constraint_violations': len(self.constraint_agent.violation_log),
            'approval_rate': self._calculate_approval_rate(),
            'tool_health': {
                name: {
                    'success_rate': health.success_rate,
                    'avg_response_time': health.avg_response_time,
                    'drift_detected': health.drift_detected
                }
                for name, health in self.reliability_agent.tool_metrics.items()
            }
        }
    
    def _calculate_approval_rate(self) -> float:
        """Calculate percentage of plans that required approval"""
        if not self.execution_log:
            return 0.0
        
        approvals_needed = sum(
            1 for log in self.execution_log
            if log['stages'].get('approval', {}).get('required', False)
        )
        
        return approvals_needed / len(self.execution_log) if self.execution_log else 0.0
    
    def close(self):
        """Cleanup resources"""
        self.db.close()
