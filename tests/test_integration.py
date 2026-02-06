"""
Integration tests for full Tether Orchestrator
"""
import pytest
from tether import TetherOrchestrator, Plan


class TestTetherOrchestrator:
    
    def test_full_workflow_valid_plan(self):
        """Test complete workflow with valid plan"""
        orchestrator = TetherOrchestrator(
            constraints={
                'time_limit': 3600,
                'budget': 100.0,
                'permissions': ['read', 'write']
            }
        )
        
        plan = Plan(
            id="integration_001",
            description="Valid test plan",
            steps=[{"action": "test"}],
            estimated_time=1800,
            estimated_cost=50.0,
            required_permissions=["read"]
        )
        
        result = orchestrator.execute_plan(plan)
        
        assert result['status'] == 'approved'
        assert result['stages']['constraint_validation']['valid'] is True
        assert result['ready_for_execution'] is True
    
    def test_full_workflow_constraint_violation(self):
        """Test workflow with constraint violations"""
        orchestrator = TetherOrchestrator(
            constraints={
                'time_limit': 1800,
                'budget': 25.0,
                'permissions': ['read']
            }
        )
        
        plan = Plan(
            id="integration_002",
            description="Violates constraints",
            steps=[{"action": "test"}],
            estimated_time=3600,  # Too long
            estimated_cost=50.0,  # Too expensive
            required_permissions=["read", "write"]  # Too many perms
        )
        
        result = orchestrator.execute_plan(plan)
        
        assert result['status'] == 'rejected'
        assert result['reason'] == 'Constraint violations'
        assert len(result['stages']['constraint_validation']['violations']) == 3
        assert 'suggestions' in result
    
    def test_full_workflow_with_approval(self):
        """Test workflow requiring human approval"""
        orchestrator = TetherOrchestrator(
            constraints={
                'time_limit': 7200,
                'budget': 100.0,
                'permissions': ['read', 'write', 'admin']
            }
        )
        
        plan = Plan(
            id="integration_003",
            description="Requires approval",
            steps=[{"action": "test"}],
            estimated_time=7200,  # Long task
            estimated_cost=75.0,  # Expensive
            required_permissions=["read", "write", "admin"]
        )
        
        approved_plans = []
        
        def approval_callback(request):
            approved_plans.append(request.decision_id)
            return True  # Approve
        
        result = orchestrator.execute_plan(plan, approval_callback)
        
        assert result['status'] == 'approved'
        assert result['stages']['approval']['required'] is True
        assert result['stages']['approval']['approved'] is True
        assert len(approved_plans) == 1
    
    def test_full_workflow_approval_denied(self):
        """Test workflow when approval is denied"""
        orchestrator = TetherOrchestrator(
            constraints={
                'time_limit': 7200,
                'budget': 100.0,
                'permissions': ['read', 'write']
            }
        )
        
        plan = Plan(
            id="integration_004",
            description="Will be denied",
            steps=[{"action": "test"}],
            estimated_time=7200,
            estimated_cost=75.0,
            required_permissions=["read", "write"]
        )
        
        def approval_callback(request):
            return False  # Deny
        
        result = orchestrator.execute_plan(plan, approval_callback)
        
        assert result['status'] == 'rejected'
        assert result['reason'] == 'Human approval denied'
    
    def test_system_health_tracking(self):
        """Test that system health is tracked correctly"""
        orchestrator = TetherOrchestrator(
            constraints={'budget': 100.0}
        )
        
        # Execute multiple plans
        for i in range(3):
            plan = Plan(
                id=f"health_test_{i}",
                description="Test plan",
                steps=[{"action": "test"}],
                estimated_time=600,
                estimated_cost=10.0,
                required_permissions=["read"]
            )
            orchestrator.execute_plan(plan)
        
        health = orchestrator.get_system_health()
        
        assert health['total_executions'] == 3
        assert 'approval_rate' in health
        assert 'tool_health' in health
