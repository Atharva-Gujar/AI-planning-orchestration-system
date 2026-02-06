"""
Test suite for Tether agents
"""

import pytest
from datetime import datetime
from tether.models import Plan, Constraint, ConstraintType, RiskLevel
from tether.agents import (
    ConstraintReasoningAgent,
    StrategicScenarioSimulator,
    ToolReliabilityAgent,
    HumanInLoopAgent
)


class TestConstraintReasoningAgent:
    """Tests for ConstraintReasoningAgent"""
    
    def test_valid_plan(self):
        """Test plan that passes all constraints"""
        constraints = {
            'time_limit': Constraint(ConstraintType.TIME, 3600),
            'budget': Constraint(ConstraintType.BUDGET, 100.0),
            'permissions': Constraint(ConstraintType.PERMISSIONS, ['read', 'write'])
        }
        agent = ConstraintReasoningAgent(constraints)
        
        plan = Plan(
            id="test_001",
            description="Test plan",
            steps=[{"action": "test"}],
            estimated_time=1800,
            estimated_cost=50.0,
            required_permissions=['read']
        )
        
        valid, violations = agent.validate_plan(plan)
        assert valid is True
        assert len(violations) == 0
    
    def test_time_violation(self):
        """Test plan that exceeds time limit"""
        constraints = {
            'time_limit': Constraint(ConstraintType.TIME, 1800)
        }
        agent = ConstraintReasoningAgent(constraints)
        
        plan = Plan(
            id="test_002",
            description="Long running plan",
            steps=[{"action": "test"}],
            estimated_time=3600,
            estimated_cost=10.0,
            required_permissions=[]
        )
        
        valid, violations = agent.validate_plan(plan)
        assert valid is False
        assert len(violations) == 1
        assert "Time violation" in violations[0]
    
    def test_budget_violation(self):
        """Test plan that exceeds budget"""
        constraints = {
            'budget': Constraint(ConstraintType.BUDGET, 50.0)
        }
        agent = ConstraintReasoningAgent(constraints)
        
        plan = Plan(
            id="test_003",
            description="Expensive plan",
            steps=[{"action": "test"}],
            estimated_time=600,
            estimated_cost=100.0,
            required_permissions=[]
        )
        
        valid, violations = agent.validate_plan(plan)
        assert valid is False
        assert "Budget violation" in violations[0]


class TestStrategicScenarioSimulator:
    """Tests for StrategicScenarioSimulator"""
    
    def test_simulate_paths(self):
        """Test multi-path simulation"""
        simulator = StrategicScenarioSimulator(simulation_depth=3)
        
        plan = Plan(
            id="sim_001",
            description="Test simulation",
            steps=[{"action": "step1"}, {"action": "step2"}],
            estimated_time=1200,
            estimated_cost=25.0,
            required_permissions=['read']
        )
        
        results = simulator.simulate_paths(plan, num_paths=3)
        
        assert len(results) == 3
        assert results[0].risk_level == RiskLevel.LOW
        assert results[1].risk_level == RiskLevel.MEDIUM
        assert results[2].risk_level == RiskLevel.HIGH
        
        # Optimistic should have highest success probability
        assert results[0].success_probability > results[1].success_probability
        assert results[1].success_probability > results[2].success_probability


class TestToolReliabilityAgent:
    """Tests for ToolReliabilityAgent"""
    
    def test_tool_registration(self):
        """Test registering tools"""
        agent = ToolReliabilityAgent(reliability_threshold=0.8)
        agent.register_tool("test_api")
        
        assert "test_api" in agent.tool_metrics
        assert agent.tool_metrics["test_api"].success_rate == 1.0
    
    def test_record_success(self):
        """Test recording successful executions"""
        agent = ToolReliabilityAgent()
        
        for _ in range(10):
            agent.record_execution("api1", True, 0.5)
        
        health = agent.get_tool_health("api1")
        assert health.success_rate > 0.9
        assert health.failure_count == 0
    
    def test_record_failures(self):
        """Test recording failures and drift detection"""
        agent = ToolReliabilityAgent(reliability_threshold=0.8)
        
        # Record many failures
        for _ in range(20):
            agent.record_execution("failing_api", False, 1.0)
        
        health = agent.get_tool_health("failing_api")
        assert health.drift_detected is True
        assert "failing_api" in agent.get_unreliable_tools()


class TestHumanInLoopAgent:
    """Tests for HumanInLoopAgent"""
    
    def test_low_risk_no_approval(self):
        """Test low risk plans don't require approval"""
        agent = HumanInLoopAgent()
        
        plan = Plan(
            id="low_risk",
            description="Low risk plan",
            steps=[{"action": "test"}],
            estimated_time=600,
            estimated_cost=10.0,
            required_permissions=['read']
        )
        
        from tether.models import SimulationResult
        sim = SimulationResult(
            path_id="test_path",
            success_probability=0.85,
            estimated_time=600,
            estimated_cost=10.0,
            risk_level=RiskLevel.LOW,
            failure_modes=[],
            second_order_effects=[]
        )
        
        needs_approval = agent.should_request_approval(plan, sim)
        assert needs_approval is False
    
    def test_high_risk_needs_approval(self):
        """Test high risk plans require approval"""
        agent = HumanInLoopAgent()
        
        plan = Plan(
            id="high_risk",
            description="High risk plan",
            steps=[{"action": "test"}],
            estimated_time=600,
            estimated_cost=75.0,
            required_permissions=['admin']
        )
        
        from tether.models import SimulationResult
        sim = SimulationResult(
            path_id="test_path",
            success_probability=0.4,
            estimated_time=600,
            estimated_cost=75.0,
            risk_level=RiskLevel.HIGH,
            failure_modes=["API failure", "Data loss"],
            second_order_effects=["System downtime"]
        )
        
        needs_approval = agent.should_request_approval(plan, sim)
        assert needs_approval is True
