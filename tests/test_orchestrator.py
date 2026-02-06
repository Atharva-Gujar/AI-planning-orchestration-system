"""
Integration tests for the full Tether orchestration system
"""

import pytest
from tether import (
    TetherOrchestrator,
    Plan,
    ApprovalRequest
)


class TestTetherOrchestrator:
    
    def setup_method(self):
        """Set up test fixtures"""
        self.orchestrator = TetherOrchestrator(
            constraints={
                'time_limit': 3600,
                'budget': 50.0,
                'permissions': ['read', 'write']
            },
            simulation_depth=3,
            reliability_threshold=0.85
        )
    
    def test_valid_plan_execution(self):
        """Test end-to-end execution of valid plan"""
        plan = Plan(
            id="integration_001",
            description="Valid integration test",
            steps=[{"action": "test"}],
            estimated_time=1800,
            estimated_cost=25.0,
            required_permissions=["read"]
        )
        
        result = self.orchestrator.execute_plan(plan)
        
        assert result['status'] == 'approved'
        assert result['ready_for_execution'] is True
        assert 'recommended_simulation' in result
    
    def test_invalid_plan_rejection(self):
        """Test that invalid plans are rejected"""
        plan = Plan(
            id="integration_002",
            description="Invalid plan",
            steps=[{"action": "test"}],
            estimated_time=7200,  # Exceeds limit
            estimated_cost=100.0,  # Exceeds budget
            required_permissions=["admin"]  # No permission
        )
        
        result = self.orchestrator.execute_plan(plan)
        
        assert result['status'] == 'rejected'
        assert result['reason'] == 'Constraint violations'
        assert 'suggestions' in result
    
    def test_approval_required_workflow(self):
        """Test that high-risk plans require approval"""
        plan = Plan(
            id="integration_003",
            description="High-risk plan",
            steps=[{"action": "test"}],
            estimated_time=3000,
            estimated_cost=75.0,  # High cost triggers approval
            required_permissions=["read"]
        )
        
        result = self.orchestrator.execute_plan(plan)
        
        assert result['stages']['approval']['required'] is True
        assert 'request' in result['stages']['approval']
    
    def test_approval_callback_executed(self):
        """Test that approval callback is properly executed"""
        plan = Plan(
            id="integration_004",
            description="High-cost plan",
            steps=[{"action": "test"}],
            estimated_time=1800,
            estimated_cost=75.0,
            required_permissions=["read"]
        )
        
        callback_invoked = []
        
        def approval_callback(request: ApprovalRequest):
            callback_invoked.append(request)
            return True
        
        result = self.orchestrator.execute_plan(plan, approval_callback=approval_callback)
        
        assert len(callback_invoked) == 1
        assert result['stages']['approval']['approved'] is True
        assert result['status'] == 'approved'
    
    def test_approval_rejection(self):
        """Test plan rejection via approval callback"""
        plan = Plan(
            id="integration_005",
            description="Rejected plan",
            steps=[{"action": "test"}],
            estimated_time=1800,
            estimated_cost=75.0,
            required_permissions=["read"]
        )
        
        def rejection_callback(request: ApprovalRequest):
            return False
        
        result = self.orchestrator.execute_plan(plan, approval_callback=rejection_callback)
        
        assert result['status'] == 'rejected'
        assert result['reason'] == 'Human approval denied'
    
    def test_system_health_reporting(self):
        """Test system health status retrieval"""
        health = self.orchestrator.get_system_health()
        
        assert 'timestamp' in health
        assert 'total_executions' in health
        assert 'unreliable_tools' in health
        assert 'tool_health' in health
    
    def test_execution_logging(self):
        """Test that executions are logged"""
        plan = Plan(
            id="integration_006",
            description="Logged execution",
            steps=[{"action": "test"}],
            estimated_time=1800,
            estimated_cost=25.0,
            required_permissions=["read"]
        )
        
        initial_count = len(self.orchestrator.execution_log)
        self.orchestrator.execute_plan(plan)
        
        assert len(self.orchestrator.execution_log) == initial_count + 1
