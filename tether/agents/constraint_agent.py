"""
Constraint Reasoning Agent
Gate 1: Validates plans against real-world constraints
"""

from typing import Dict, List, Tuple
from datetime import datetime
from ..models import Constraint, Plan, ConstraintType


class ConstraintReasoningAgent:
    """
    Gate 1: Validates plans against real-world constraints
    Most planning agents fail because this is missing
    """
    
    def __init__(self, constraints: Dict[str, Constraint]):
        self.constraints = constraints
        self.violation_log = []
    
    def validate_plan(self, plan: Plan) -> Tuple[bool, List[str]]:
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
    
    def suggest_modifications(self, plan: Plan, violations: List[str]) -> Dict:
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
