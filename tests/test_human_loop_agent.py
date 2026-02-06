"""
Tests for Human-in-the-Loop Agent
"""

import pytest
from tether import (
    HumanInLoopAgent,
    Plan,
    SimulationResult,
    RiskLevel
)


class TestHumanInLoopAgent:
    
    def test_approval_required_for_high_risk(self):
        """Test that high risk plans require approval"""
        agent = HumanInLoopAgent()
        
        plan = Plan(
            id="hitl_001",
            description="High risk task",
            steps=[{"action": "risky"}],
            estimated_time=600,
            estimated_cost=25.0,
            required_permissions=['read']
        )
        
        simulation = SimulationResult(
            path_id="hitl_001_path_0",
            success_probability=0.7,
            estimated_time=600,
            estimated_cost=25.0,
            risk_level=RiskLevel.HIGH,
            failure_modes=["API failure"],
            second_order_effects=[]
        )
        
        requires_approval = agent.should_request_approval(plan, simulation)
        assert requires_approval is True
    
    def test_approval_required_for_high_cost(self):
        """Test that expensive plans require approval"""
        agent = HumanInLoopAgent()
        
        plan = Plan(
            id="hitl_002",
            description="Expensive task",
            steps=[{"action": "expensive"}],
            estimated_time=1200,
            estimated_cost=75.0,  # > $50 threshold
            required_permissions=['read']
        )
        
        simulation = SimulationResult(
            path_id="hitl_002_path_0",
            success_probability=0.8,
            estimated_time=1200,
            estimated_cost=75.0,
            risk_level=RiskLevel.MEDIUM,
            failure_modes=[],
            second_order_effects=[]
        )
        
        requires_approval = agent.should_request_approval(plan, simulation)
        assert requires_approval is True
    
    def test_no_approval_for_low_risk_low_cost(self):
        """Test that low risk, low cost plans don't require approval"""
        agent = HumanInLoopAgent()
        
        plan = Plan(
            id="hitl_003",
            description="Safe task",
            steps=[{"action": "safe"}],
            estimated_time=600,
            estimated_cost=10.0,
            required_permissions=['read']
        )
        
        simulation = SimulationResult(
            path_id="hitl_003_path_0",
            success_probability=0.85,
            estimated_time=600,
            estimated_cost=10.0,
            risk_level=RiskLevel.LOW,
            failure_modes=[],
            second_order_effects=[]
        )
        
        requires_approval = agent.should_request_approval(plan, simulation)
        assert requires_approval is False
    
    def test_approval_request_creation(self):
        """Test creation of approval requests"""
        agent = HumanInLoopAgent()
        
        plan = Plan(
            id="hitl_004",
            description="Approval test",
            steps=[{"action": "test"}],
            estimated_time=3000,
            estimated_cost=60.0,
            required_permissions=['read', 'write']
        )
        
        simulation = SimulationResult(
            path_id="hitl_004_path_0",
            success_probability=0.6,
            estimated_time=3000,
            estimated_cost=60.0,
            risk_level=RiskLevel.MEDIUM,
            failure_modes=["Rate limiting", "Timeout"],
            second_order_effects=["Spillover"]
        )
        
        request = agent.create_approval_request(plan, simulation)
        
        assert request.decision_id.startswith("approval_")
        assert request.risk_level == RiskLevel.MEDIUM
        assert 'plan_summary' in request.context
        assert 'estimated_cost' in request.context
        assert 'key_risks' in request.context
        assert len(request.context['key_risks']) <= 3  # Max 3 risks
    
    def test_approver_selection_by_risk(self):
        """Test that appropriate approvers are selected based on risk"""
        agent = HumanInLoopAgent()
        
        plan = Plan(
            id="hitl_005",
            description="Critical task",
            steps=[{"action": "critical"}],
            estimated_time=1800,
            estimated_cost=50.0,
            required_permissions=['admin']
        )
        
        critical_sim = SimulationResult(
            path_id="hitl_005_path_0",
            success_probability=0.5,
            estimated_time=1800,
            estimated_cost=50.0,
            risk_level=RiskLevel.CRITICAL,
            failure_modes=["Data loss"],
            second_order_effects=[]
        )
        
        request = agent.create_approval_request(plan, critical_sim)
        assert request.recommended_approver == "senior_engineer"
    
    def test_decision_recording(self):
        """Test that approval decisions are recorded"""
        agent = HumanInLoopAgent()
        
        plan = Plan(
            id="hitl_006",
            description="Decision recording test",
            steps=[{"action": "test"}],
            estimated_time=900,
            estimated_cost=30.0,
            required_permissions=['read']
        )
        
        simulation = SimulationResult(
            path_id="hitl_006_path_0",
            success_probability=0.7,
            estimated_time=900,
            estimated_cost=30.0,
            risk_level=RiskLevel.MEDIUM,
            failure_modes=[],
            second_order_effects=[]
        )
        
        request = agent.create_approval_request(plan, simulation)
        agent.record_decision(request, approved=True, approver="test_engineer")
        
        assert len(agent.approval_history) == 1
        assert agent.approval_history[0]['approved'] is True
        assert agent.approval_history[0]['approver'] == "test_engineer"
