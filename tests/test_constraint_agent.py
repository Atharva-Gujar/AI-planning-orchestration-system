"""
Unit tests for Constraint Reasoning Agent
"""
import pytest
from datetime import datetime
from tether import (
    ConstraintReasoningAgent,
    Constraint,
    ConstraintType,
    Plan
)


class TestConstraintReasoningAgent:
    
    def test_time_constraint_validation_pass(self):
        """Test that plan within time limit passes"""
        constraints = {
            'time_limit': Constraint(ConstraintType.TIME, 3600, True, "1 hour limit")
        }
        agent = ConstraintReasoningAgent(constraints)
        
        plan = Plan(
            id="test_001",
            description="Quick task",
            steps=[{"action": "test"}],
            estimated_time=1800,  # 30 minutes
            estimated_cost=10.0,
            required_permissions=["read"]
        )
        
        valid, violations = agent.validate_plan(plan)
        assert valid is True
        assert len(violations) == 0
    
    def test_time_constraint_validation_fail(self):
        """Test that plan exceeding time limit fails"""
        constraints = {
            'time_limit': Constraint(ConstraintType.TIME, 1800, True, "30 min limit")
        }
        agent = ConstraintReasoningAgent(constraints)
        
        plan = Plan(
            id="test_002",
            description="Long task",
            steps=[{"action": "test"}],
            estimated_time=3600,  # 1 hour
            estimated_cost=10.0,
            required_permissions=["read"]
        )
        
        valid, violations = agent.validate_plan(plan)
        assert valid is False
        assert len(violations) == 1
        assert "Time violation" in violations[0]
    
    def test_budget_constraint_validation_pass(self):
        """Test that plan within budget passes"""
        constraints = {
            'budget': Constraint(ConstraintType.BUDGET, 100.0, True, "$100 limit")
        }
        agent = ConstraintReasoningAgent(constraints)
        
        plan = Plan(
            id="test_003",
            description="Affordable task",
            steps=[{"action": "test"}],
            estimated_time=1800,
            estimated_cost=50.0,
            required_permissions=["read"]
        )
        
        valid, violations = agent.validate_plan(plan)
        assert valid is True
        assert len(violations) == 0
    
    def test_budget_constraint_validation_fail(self):
        """Test that plan exceeding budget fails"""
        constraints = {
            'budget': Constraint(ConstraintType.BUDGET, 50.0, True, "$50 limit")
        }
        agent = ConstraintReasoningAgent(constraints)
        
        plan = Plan(
            id="test_004",
            description="Expensive task",
            steps=[{"action": "test"}],
            estimated_time=1800,
            estimated_cost=100.0,
            required_permissions=["read"]
        )
        
        valid, violations = agent.validate_plan(plan)
        assert valid is False
        assert len(violations) == 1
        assert "Budget violation" in violations[0]
    
    def test_permission_constraint_validation_pass(self):
        """Test that plan with allowed permissions passes"""
        constraints = {
            'permissions': Constraint(
                ConstraintType.PERMISSIONS, 
                ['read', 'write', 'admin'], 
                True, 
                "Allowed permissions"
            )
        }
        agent = ConstraintReasoningAgent(constraints)
        
        plan = Plan(
            id="test_005",
            description="Permitted task",
            steps=[{"action": "test"}],
            estimated_time=1800,
            estimated_cost=10.0,
            required_permissions=["read", "write"]
        )
        
        valid, violations = agent.validate_plan(plan)
        assert valid is True
        assert len(violations) == 0
    
    def test_permission_constraint_validation_fail(self):
        """Test that plan with disallowed permissions fails"""
        constraints = {
            'permissions': Constraint(
                ConstraintType.PERMISSIONS, 
                ['read'], 
                True, 
                "Read-only"
            )
        }
        agent = ConstraintReasoningAgent(constraints)
        
        plan = Plan(
            id="test_006",
            description="Needs write access",
            steps=[{"action": "test"}],
            estimated_time=1800,
            estimated_cost=10.0,
            required_permissions=["read", "write", "admin"]
        )
        
        valid, violations = agent.validate_plan(plan)
        assert valid is False
        assert len(violations) == 1
        assert "Permission violation" in violations[0]
        assert "write" in violations[0] or "admin" in violations[0]
    
    def test_multiple_constraint_violations(self):
        """Test plan that violates multiple constraints"""
        constraints = {
            'time_limit': Constraint(ConstraintType.TIME, 1800, True),
            'budget': Constraint(ConstraintType.BUDGET, 50.0, True),
            'permissions': Constraint(ConstraintType.PERMISSIONS, ['read'], True)
        }
        agent = ConstraintReasoningAgent(constraints)
        
        plan = Plan(
            id="test_007",
            description="Violates everything",
            steps=[{"action": "test"}],
            estimated_time=3600,  # Too long
            estimated_cost=100.0,  # Too expensive
            required_permissions=["read", "write", "admin"]  # Too many perms
        )
        
        valid, violations = agent.validate_plan(plan)
        assert valid is False
        assert len(violations) == 3
    
    def test_suggest_modifications_time_violation(self):
        """Test modification suggestions for time violation"""
        constraints = {
            'time_limit': Constraint(ConstraintType.TIME, 1800, True)
        }
        agent = ConstraintReasoningAgent(constraints)
        
        plan = Plan(
            id="test_008",
            description="Too slow",
            steps=[{"action": "test"}],
            estimated_time=3600,
            estimated_cost=10.0,
            required_permissions=["read"]
        )
        
        valid, violations = agent.validate_plan(plan)
        suggestions = agent.suggest_modifications(plan, violations)
        
        assert suggestions['original_plan'] == "test_008"
        assert len(suggestions['modifications']) > 0
        assert any('reduce_scope' in mod['type'] for mod in suggestions['modifications'])
    
    def test_suggest_modifications_budget_violation(self):
        """Test modification suggestions for budget violation"""
        constraints = {
            'budget': Constraint(ConstraintType.BUDGET, 50.0, True)
        }
        agent = ConstraintReasoningAgent(constraints)
        
        plan = Plan(
            id="test_009",
            description="Too expensive",
            steps=[{"action": "test"}],
            estimated_time=1800,
            estimated_cost=100.0,
            required_permissions=["read"]
        )
        
        valid, violations = agent.validate_plan(plan)
        suggestions = agent.suggest_modifications(plan, violations)
        
        assert len(suggestions['modifications']) > 0
        assert any('optimize_cost' in mod['type'] for mod in suggestions['modifications'])
    
    def test_violation_logging(self):
        """Test that violations are logged"""
        constraints = {
            'budget': Constraint(ConstraintType.BUDGET, 50.0, True)
        }
        agent = ConstraintReasoningAgent(constraints)
        
        plan = Plan(
            id="test_010",
            description="Test logging",
            steps=[{"action": "test"}],
            estimated_time=1800,
            estimated_cost=100.0,
            required_permissions=["read"]
        )
        
        agent.validate_plan(plan)
        
        assert len(agent.violation_log) == 1
        assert agent.violation_log[0]['plan_id'] == "test_010"
        assert len(agent.violation_log[0]['violations']) > 0
