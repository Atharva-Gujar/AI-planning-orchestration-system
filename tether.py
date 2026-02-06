"""
Tether: AI Planning Orchestration System
The reality layer for AI agents that prevents deployment failure
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import time
import json
from datetime import datetime, timedelta


class ConstraintType(Enum):
    TIME = "time"
    BUDGET = "budget"
    PERMISSIONS = "permissions"
    REGULATIONS = "regulations"


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Constraint:
    """Represents a real-world constraint on plan execution"""
    type: ConstraintType
    value: Any
    hard_limit: bool = True  # If False, can be exceeded with approval
    description: str = ""


@dataclass
class Plan:
    """Represents an AI-generated execution plan"""
    id: str
    description: str
    steps: List[Dict[str, Any]]
    estimated_time: int  # seconds
    estimated_cost: float
    required_permissions: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SimulationResult:
    """Results from scenario simulation"""
    path_id: str
    success_probability: float
    estimated_time: int
    estimated_cost: float
    risk_level: RiskLevel
    failure_modes: List[str]
    second_order_effects: List[str]
    recommended: bool = False


@dataclass
class ToolHealth:
    """Monitors the health of external tools/APIs"""
    tool_name: str
    success_rate: float
    avg_response_time: float
    last_failure: Optional[datetime]
    failure_count: int
    drift_detected: bool = False


@dataclass
class ApprovalRequest:
    """Request for human approval"""
    decision_id: str
    context: Dict[str, Any]
    risk_level: RiskLevel
    recommended_approver: str
    urgency: str  # low, medium, high
    timeout: int  # seconds before auto-decision


class ConstraintReasoningAgent:
    """
    Gate 1: Validates plans against real-world constraints
    Most planning agents fail because this is missing
    """
    
    def __init__(self, constraints: Dict[str, Constraint]):
        self.constraints = constraints
        self.violation_log = []
    
    def validate_plan(self, plan: Plan) -> tuple[bool, List[str]]:
        """
        Validates a plan against all constraints
        Returns: (is_valid, list_of_violations)
        """
        violations = []
        
        # Time constraint check
        if 'time_limit' in self.constraints:
            time_constraint = self.constraints['time_limit']
            if plan.estimated_time > time_constraint.value:
                violations.append(
                    f"Time violation: Plan requires {plan.estimated_time}s "
                    f"but limit is {time_constraint.value}s"
                )
        
        # Budget constraint check
        if 'budget' in self.constraints:
            budget_constraint = self.constraints['budget']
            if plan.estimated_cost > budget_constraint.value:
                violations.append(
                    f"Budget violation: Plan costs ${plan.estimated_cost} "
                    f"but budget is ${budget_constraint.value}"
                )
        
        # Permissions constraint check
        if 'permissions' in self.constraints:
            perm_constraint = self.constraints['permissions']
            allowed_perms = set(perm_constraint.value)
            required_perms = set(plan.required_permissions)
            missing_perms = required_perms - allowed_perms
            if missing_perms:
                violations.append(
                    f"Permission violation: Missing permissions {missing_perms}"
                )
        
        # Log violations
        if violations:
            self.violation_log.append({
                'plan_id': plan.id,
                'timestamp': datetime.now(),
                'violations': violations
            })
        
        return len(violations) == 0, violations
    
    def suggest_modifications(self, plan: Plan, violations: List[str]) -> Dict[str, Any]:
        """Suggest how to modify plan to meet constraints"""
        suggestions = {
            'original_plan': plan.id,
            'modifications': []
        }
        
        for violation in violations:
            if 'Time violation' in violation:
                suggestions['modifications'].append({
                    'type': 'reduce_scope',
                    'reason': violation,
                    'suggestion': 'Consider parallelization or reducing batch sizes'
                })
            elif 'Budget violation' in violation:
                suggestions['modifications'].append({
                    'type': 'optimize_cost',
                    'reason': violation,
                    'suggestion': 'Use cheaper API tiers or cache results'
                })
            elif 'Permission violation' in violation:
                suggestions['modifications'].append({
                    'type': 'request_permissions',
                    'reason': violation,
                    'suggestion': 'Request additional permissions or modify approach'
                })
        
        return suggestions


class StrategicScenarioSimulator:
    """
    Gate 2: Multi-path simulation with second-order effects
    Turns naive planning into strategic planning
    """
    
    def __init__(self, simulation_depth: int = 3):
        self.simulation_depth = simulation_depth
        self.simulation_history = []
    
    def simulate_paths(self, plan: Plan, num_paths: int = 3) -> List[SimulationResult]:
        """
        Simulates multiple execution paths for a plan
        Returns risk-weighted outcomes
        """
        results = []
        
        for i in range(num_paths):
            # Simulate different scenarios (optimistic, realistic, pessimistic)
            if i == 0:  # Optimistic path
                success_prob = 0.85
                time_multiplier = 1.0
                cost_multiplier = 1.0
                risk = RiskLevel.LOW
            elif i == 1:  # Realistic path
                success_prob = 0.65
                time_multiplier = 1.3
                cost_multiplier = 1.2
                risk = RiskLevel.MEDIUM
            else:  # Pessimistic path
                success_prob = 0.40
                time_multiplier = 1.8
                cost_multiplier = 1.5
                risk = RiskLevel.HIGH
            
            # Identify failure modes
            failure_modes = self._identify_failure_modes(plan, risk)
            
            # Analyze second-order effects
            second_order = self._analyze_second_order_effects(plan, failure_modes)
            
            result = SimulationResult(
                path_id=f"{plan.id}_path_{i}",
                success_probability=success_prob,
                estimated_time=int(plan.estimated_time * time_multiplier),
                estimated_cost=plan.estimated_cost * cost_multiplier,
                risk_level=risk,
                failure_modes=failure_modes,
                second_order_effects=second_order,
                recommended=(i == 1)  # Recommend realistic path
            )
            results.append(result)
        
        self.simulation_history.append({
            'plan_id': plan.id,
            'timestamp': datetime.now(),
            'results': results
        })
        
        return results
    
    def _identify_failure_modes(self, plan: Plan, risk: RiskLevel) -> List[str]:
        """Identify potential failure modes based on plan and risk level"""
        failure_modes = []
        
        if risk in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            failure_modes.extend([
                "API rate limiting exceeded",
                "External service downtime",
                "Data quality degradation"
            ])
        
        if risk in [RiskLevel.MEDIUM, RiskLevel.HIGH]:
            failure_modes.extend([
                "Timeout due to network latency",
                "Partial data retrieval"
            ])
        
        # Add plan-specific failure modes
        if plan.estimated_time > 3600:  # > 1 hour
            failure_modes.append("Long-running task interruption risk")
        
        if len(plan.steps) > 10:
            failure_modes.append("Complex workflow coordination failure")
        
        return failure_modes
    
    def _analyze_second_order_effects(self, plan: Plan, failure_modes: List[str]) -> List[str]:
        """Analyze cascading effects of failures"""
        effects = []
        
        if "API rate limiting exceeded" in failure_modes:
            effects.append("Downstream services may queue requests, causing delays")
            effects.append("Potential cost spillover to next billing cycle")
        
        if "Data quality degradation" in failure_modes:
            effects.append("Invalid results may propagate to dependent systems")
            effects.append("Manual cleanup effort required")
        
        if "Long-running task interruption risk" in failure_modes:
            effects.append("Partial state may require rollback procedures")
            effects.append("Resource cleanup needed to prevent leaks")
        
        return effects


class ToolReliabilityAgent:
    """
    Runtime monitoring: Prevents silent system rot
    Monitors API failures, data drift, scraper decay
    """
    
    def __init__(self, reliability_threshold: float = 0.85):
        self.reliability_threshold = reliability_threshold
        self.tool_metrics: Dict[str, ToolHealth] = {}
        self.alert_callbacks: List[Callable] = []
    
    def register_tool(self, tool_name: str):
        """Register a tool for monitoring"""
        self.tool_metrics[tool_name] = ToolHealth(
            tool_name=tool_name,
            success_rate=1.0,
            avg_response_time=0.0,
            last_failure=None,
            failure_count=0
        )
    
    def record_execution(self, tool_name: str, success: bool, response_time: float):
        """Record tool execution metrics"""
        if tool_name not in self.tool_metrics:
            self.register_tool(tool_name)
        
        tool = self.tool_metrics[tool_name]
        
        # Update success rate (exponential moving average)
        alpha = 0.1  # Smoothing factor
        tool.success_rate = alpha * (1.0 if success else 0.0) + (1 - alpha) * tool.success_rate
        
        # Update response time
        tool.avg_response_time = alpha * response_time + (1 - alpha) * tool.avg_response_time
        
        if not success:
            tool.failure_count += 1
            tool.last_failure = datetime.now()
        
        # Check for drift
        if tool.success_rate < self.reliability_threshold:
            tool.drift_detected = True
            self._trigger_alert(tool_name, "reliability", tool.success_rate)
        
        # Check for performance degradation
        if tool.avg_response_time > 5.0:  # 5 seconds threshold
            self._trigger_alert(tool_name, "performance", tool.avg_response_time)
    
    def get_tool_health(self, tool_name: str) -> Optional[ToolHealth]:
        """Get current health metrics for a tool"""
        return self.tool_metrics.get(tool_name)
    
    def get_unreliable_tools(self) -> List[str]:
        """Get list of tools below reliability threshold"""
        return [
            name for name, health in self.tool_metrics.items()
            if health.success_rate < self.reliability_threshold
        ]
    
    def _trigger_alert(self, tool_name: str, alert_type: str, value: float):
        """Trigger alerts for tool issues"""
        alert = {
            'timestamp': datetime.now(),
            'tool': tool_name,
            'type': alert_type,
            'value': value,
            'message': f"{tool_name} {alert_type} issue detected: {value:.2f}"
        }
        
        for callback in self.alert_callbacks:
            callback(alert)
    
    def add_alert_callback(self, callback: Callable):
        """Add callback function for alerts"""
        self.alert_callbacks.append(callback)


class HumanInLoopAgent:
    """
    Intelligent approval workflow
    Learns when to ask, who to ask, how much context to show
    """
    
    def __init__(self):
        self.approval_history = []
        self.approver_expertise = {}  # Maps domains to approvers
        self.decision_patterns = {}   # Learns from past decisions
    
    def should_request_approval(self, plan: Plan, simulation: SimulationResult) -> bool:
        """
        Determines if human approval is needed
        Based on risk, cost, and learned patterns
        """
        # High risk always requires approval
        if simulation.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            return True
        
        # High cost requires approval
        if plan.estimated_cost > 50:  # $50 threshold
            return True
        
        # Long duration requires approval
        if plan.estimated_time > 7200:  # 2 hours
            return True
        
        # Low success probability requires approval
        if simulation.success_probability < 0.5:
            return True
        
        return False
    
    def create_approval_request(
        self, 
        plan: Plan, 
        simulation: SimulationResult,
        violations: List[str] = None
    ) -> ApprovalRequest:
        """
        Creates a context-rich approval request
        Shows only decision-relevant information
        """
        # Determine risk level
        risk = simulation.risk_level
        
        # Select appropriate approver based on domain
        approver = self._select_approver(plan, risk)
        
        # Build context with relevant information only
        context = {
            'plan_summary': plan.description,
            'estimated_time': f"{plan.estimated_time // 60} minutes",
            'estimated_cost': f"${plan.estimated_cost:.2f}",
            'success_probability': f"{simulation.success_probability * 100:.0f}%",
            'risk_level': risk.value,
            'key_risks': simulation.failure_modes[:3],  # Top 3 risks only
        }
        
        if violations:
            context['constraint_violations'] = violations
        
        # Determine urgency
        urgency = "high" if risk == RiskLevel.CRITICAL else "medium"
        
        # Set timeout based on urgency
        timeout = 300 if urgency == "high" else 1800  # 5 min or 30 min
        
        request = ApprovalRequest(
            decision_id=f"approval_{plan.id}_{int(time.time())}",
            context=context,
            risk_level=risk,
            recommended_approver=approver,
            urgency=urgency,
            timeout=timeout
        )
        
        return request
    
    def _select_approver(self, plan: Plan, risk: RiskLevel) -> str:
        """Select appropriate approver based on domain and risk"""
        # In production, this would use learned patterns
        # For now, simple rule-based selection
        
        if risk == RiskLevel.CRITICAL:
            return "senior_engineer"
        elif risk == RiskLevel.HIGH:
            return "team_lead"
        else:
            return "any_engineer"
    
    def record_decision(self, request: ApprovalRequest, approved: bool, approver: str):
        """Record approval decision for learning"""
        self.approval_history.append({
            'request': request,
            'approved': approved,
            'approver': approver,
            'timestamp': datetime.now()
        })


class TetherOrchestrator:
    """
    Main orchestrator that coordinates all agents
    This is the primary interface for the Tether system
    """
    
    def __init__(
        self,
        constraints: Dict[str, Any],
        simulation_depth: int = 3,
        reliability_threshold: float = 0.85
    ):
        # Initialize all agents
        self.constraint_agent = ConstraintReasoningAgent(
            {k: Constraint(ConstraintType(k), v) for k, v in constraints.items()
             if k in ['time_limit', 'budget', 'permissions', 'regulations']}
        )
        self.simulator = StrategicScenarioSimulator(simulation_depth)
        self.reliability_agent = ToolReliabilityAgent(reliability_threshold)
        self.human_loop_agent = HumanInLoopAgent()
        
        self.execution_log = []
    
    def execute_plan(
        self, 
        plan: Plan,
        approval_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Main execution pipeline:
        1. Constraint validation
        2. Scenario simulation
        3. Human approval (if needed)
        4. Monitored execution
        """
        result = {
            'plan_id': plan.id,
            'status': 'pending',
            'timestamp': datetime.now(),
            'stages': {}
        }
        
        # Stage 1: Constraint Validation
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
            return result
        
        # Stage 2: Scenario Simulation
        simulations = self.simulator.simulate_paths(plan)
        best_simulation = max(simulations, key=lambda s: s.success_probability)
        result['stages']['simulation'] = {
            'paths_explored': len(simulations),
            'recommended_path': best_simulation.path_id,
            'success_probability': best_simulation.success_probability,
            'risk_level': best_simulation.risk_level.value
        }
        
        # Stage 3: Human Approval (if needed)
        needs_approval = self.human_loop_agent.should_request_approval(plan, best_simulation)
        result['stages']['approval'] = {
            'required': needs_approval
        }
        
        if needs_approval:
            approval_request = self.human_loop_agent.create_approval_request(
                plan, best_simulation, violations if not valid else None
            )
            result['stages']['approval']['request'] = approval_request
            
            if approval_callback:
                approved = approval_callback(approval_request)
                result['stages']['approval']['approved'] = approved
                
                if not approved:
                    result['status'] = 'rejected'
                    result['reason'] = 'Human approval denied'
                    return result
            else:
                result['status'] = 'awaiting_approval'
                return result
        
        # Stage 4: Execution (simulated for demo)
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
        return result
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status"""
        unreliable_tools = self.reliability_agent.get_unreliable_tools()
        
        return {
            'timestamp': datetime.now(),
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
        
        return approvals_needed / len(self.execution_log)


# Example usage and testing
if __name__ == "__main__":
    print("Tether: AI Planning Orchestration System")
    print("=" * 50)
    
    # Example: Create a test plan
    test_plan = Plan(
        id="research_001",
        description="Scrape 1000 websites and analyze sentiment",
        steps=[
            {"action": "scrape", "count": 1000},
            {"action": "analyze", "method": "sentiment"},
            {"action": "report", "format": "pdf"}
        ],
        estimated_time=7200,  # 2 hours
        estimated_cost=75.0,
        required_permissions=["read", "write", "api_access"]
    )
    
    # Initialize orchestrator with constraints
    orchestrator = TetherOrchestrator(
        constraints={
            'time_limit': 3600,  # 1 hour
            'budget': 50.0,      # $50
            'permissions': ['read', 'write']  # Missing 'api_access'
        },
        simulation_depth=3,
        reliability_threshold=0.85
    )
    
    # Define approval callback
    def mock_approval(request: ApprovalRequest) -> bool:
        print(f"\n🚨 Approval Required:")
        print(f"   Decision ID: {request.decision_id}")
        print(f"   Risk Level: {request.risk_level.value}")
        print(f"   Recommended Approver: {request.recommended_approver}")
        print(f"   Context: {json.dumps(request.context, indent=4)}")
        return True  # Auto-approve for demo
    
    # Execute plan
    print("\nExecuting Plan...")
    result = orchestrator.execute_plan(test_plan, approval_callback=mock_approval)
    
    print("\n📊 Execution Result:")
    print(json.dumps(result, indent=2, default=str))
    
    # Show system health
    print("\n🏥 System Health:")
    health = orchestrator.get_system_health()
    print(json.dumps(health, indent=2, default=str))
    
    print("\n" + "=" * 50)
    print("Tether keeps your AI agents grounded in reality.")
