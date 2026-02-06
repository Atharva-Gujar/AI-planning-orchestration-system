"""
Unit tests for Human-in-Loop Agent
"""
import pytest
from tether import (
    HumanInLoopAgent,
    Plan,
    SimulationResult,
    RiskLevel,
    ApprovalRequest
)


class TestHumanInLoopAgent:
    
    def test_high_risk_requires_approval(self):
        """Test that high-risk plans require approval"""
        agent = HumanInLoopAgent()
        
        plan = Plan(
            id="hitl_001",
            description="High risk task",
            steps=[{"action": "test"}],
            estimated_time=1800,
            estimated_cost=50.0,
            required_permissions=["read"]
        )
        
        simulation = SimulationResult(
            path_id="path_1",
            success_probability=0.65,
            estimated_time=1800,
            estimated_cost=50.0,
            risk_level=RiskLevel.HIGH,
            failure_modes=[],
            second_order_effects=[]
        )
        
        assert agent.should_request_approval(plan, simulation) is True
    
    def test_high_cost_requires_approval(self):
        """Test that high-cost plans require approval"""
        agent = HumanInLoopAgent()
        
        plan = Plan(
            id="hitl_002",
            description="Expensive task",
            steps=[{"action": "test"}],
            estimated_time=1800,
            estimated_cost=75.0,  # > $50 threshold
            required_permissions=["read"]
        )
        
        simulation = SimulationResult(
            path_id="path_1",
            success_probability=0.85,
            estimated_time=1800,
            estimated_cost=75.0,
            risk_level=RiskLevel.MEDIUM,
            failure_modes=[],
            second_order_effects=[]
        )
        
        assert agent.should_request_approval(plan, simulation) is True
    
    def test_long_duration_requires_approval(self):
        """Test that long-running tasks require approval"""
        agent = HumanInLoopAgent()
        
        plan = Plan(
            id="hitl_003",
            description="Long task",
            steps=[{"action": "test"}],
            estimated_time=10800,  # 3 hours > 2 hour threshold
            estimated_cost=25.0,
            required_permissions=["read"]
        )
        
        simulation = SimulationResult(
            path_id="path_1",
            success_probability=0.85,
            estimated_time=10800,
            estimated_cost=25.0,
            risk_level=RiskLevel.MEDIUM,
            failure_modes=[],
            second_order_effects=[]
        )
        
        assert agent.should_request_approval(plan, simulation) is True
    
    def test_low_success_probability_requires_approval(self):
        """Test that low success probability requires approval"""
        agent = HumanInLoopAgent()
        
        plan = Plan(
            id="hitl_004",
            description="Risky task",
            steps=[{"action": "test"}],
            estimated_time=1800,
            estimated_cost=25.0,
            required_permissions=["read"]
        )
        
        simulation = SimulationResult(
            path_id="path_1",
            success_probability=0.35,  # < 50%
            estimated_time=1800,
            estimated_cost=25.0,
            risk_level=RiskLevel.MEDIUM,
            failure_modes=["might fail"],
            second_order_effects=[]
        )
        
        assert agent.should_request_approval(plan, simulation) is True
    
    def test_low_risk_low_cost_no_approval(self):
        """Test that safe plans don't require approval"""
        agent = HumanInLoopAgent()
        
        plan = Plan(
            id="hitl_005",
            description="Safe task",
            steps=[{"action": "test"}],
            estimated_time=600,  # 10 minutes
            estimated_cost=10.0,
            required_permissions=["read"]
        )
        
        simulation = SimulationResult(
            path_id="path_1",
            success_probability=0.85,
            estimated_time=600,
            estimated_cost=10.0,
            risk_level=RiskLevel.LOW,
            failure_modes=[],
            second_order_effects=[]
        )
        
        assert agent.should_request_approval(plan, simulation) is False
    
    def test_create_approval_request_context(self):
        """Test that approval requests contain proper context"""
        agent = HumanInLoopAgent()
        
        plan = Plan(
            id="hitl_006",
            description="Test context",
            steps=[{"action": "test"}],
            estimated_time=7200,
            estimated_cost=75.0,
            required_permissions=["read"]
        )
        
        simulation = SimulationResult(
            path_id="path_1",
            success_probability=0.65,
            estimated_time=7200,
            estimated_cost=75.0,
            risk_level=RiskLevel.HIGH,
            failure_modes=["API rate limit", "Data loss", "Timeout"],
            second_order_effects=[]
        )
        
        request = agent.create_approval_request(plan, simulation)
        
        assert isinstance(request, ApprovalRequest)
        assert request.risk_level == RiskLevel.HIGH
        assert 'plan_summary' in request.context
        assert 'estimated_cost' in request.context
        assert 'key_risks' in request.context
    
    def test_approval_request_limits_risks_shown(self):
        """Test that only top 3 risks are shown in approval"""
        agent = HumanInLoopAgent()
        
        plan = Plan(
            id="hitl_007",
            description="Many risks",
            steps=[{"action": "test"}],
            estimated_time=1800,
            estimated_cost=75.0,
            required_permissions=["read"]
        )
        
        simulation = SimulationResult(
            path_id="path_1",
            success_probability=0.65,
            estimated_time=1800,
            estimated_cost=75.0,
            risk_level=RiskLevel.HIGH,
            failure_modes=[f"Risk {i}" for i in range(10)],  # 10 risks
            second_order_effects=[]
        )
        
        request = agent.create_approval_request(plan, simulation)
        
        # Should only show top 3 risks
        assert len(request.context['key_risks']) <= 3
    
    def test_record_decision_logs_approval(self):
        """Test that approval decisions are recorded"""
        agent = HumanInLoopAgent()
        
        request = ApprovalRequest(
            decision_id="test_decision",
            context={"test": "data"},
            risk_level=RiskLevel.MEDIUM,
            recommended_approver="engineer",
            urgency="medium",
            timeout=1800
        )
        
        agent.record_decision(request, approved=True, approver="alice")
        
        assert len(agent.approval_history) == 1
        assert agent.approval_history[0]['approved'] is True
        assert agent.approval_history[0]['approver'] == "alice"
