"""
Strategic Scenario Simulator
Gate 2: Multi-path simulation with second-order effects
"""

from typing import List
from datetime import datetime
from ..models import Plan, SimulationResult, RiskLevel


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
            # Simulate different scenarios
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
            
            failure_modes = self._identify_failure_modes(plan, risk)
            second_order = self._analyze_second_order_effects(plan, failure_modes)
            
            result = SimulationResult(
                path_id=f"{plan.id}_path_{i}",
                success_probability=success_prob,
                estimated_time=int(plan.estimated_time * time_multiplier),
                estimated_cost=plan.estimated_cost * cost_multiplier,
                risk_level=risk,
                failure_modes=failure_modes,
                second_order_effects=second_order,
                recommended=(i == 1)
            )
            results.append(result)
        
        self.simulation_history.append({
            'plan_id': plan.id,
            'timestamp': datetime.now(),
            'results': results
        })
        
        return results
    
    def _identify_failure_modes(self, plan: Plan, risk: RiskLevel) -> List[str]:
        """Identify potential failure modes"""
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
        
        if plan.estimated_time > 3600:
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
