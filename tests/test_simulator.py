"""
Unit tests for Strategic Scenario Simulator
"""
import pytest
from tether import (
    StrategicScenarioSimulator,
    Plan,
    RiskLevel,
    SimulationResult
)


class TestStrategicScenarioSimulator:
    
    def test_simulate_paths_creates_multiple_scenarios(self):
        """Test that simulator creates multiple execution paths"""
        simulator = StrategicScenarioSimulator(simulation_depth=3)
        
        plan = Plan(
            id="sim_001",
            description="Test simulation",
            steps=[{"action": "test"}],
            estimated_time=1800,
            estimated_cost=50.0,
            required_permissions=["read"]
        )
        
        results = simulator.simulate_paths(plan, num_paths=3)
        
        assert len(results) == 3
        assert all(isinstance(r, SimulationResult) for r in results)
    
    def test_optimistic_path_has_highest_success_rate(self):
        """Test that optimistic path has highest success probability"""
        simulator = StrategicScenarioSimulator()
        
        plan = Plan(
            id="sim_002",
            description="Test optimistic",
            steps=[{"action": "test"}],
            estimated_time=1800,
            estimated_cost=50.0,
            required_permissions=["read"]
        )
        
        results = simulator.simulate_paths(plan, num_paths=3)
        
        # First path should be optimistic
        assert results[0].success_probability > results[1].success_probability
        assert results[0].success_probability > results[2].success_probability
    
    def test_pessimistic_path_has_lowest_success_rate(self):
        """Test that pessimistic path has lowest success probability"""
        simulator = StrategicScenarioSimulator()
        
        plan = Plan(
            id="sim_003",
            description="Test pessimistic",
            steps=[{"action": "test"}],
            estimated_time=1800,
            estimated_cost=50.0,
            required_permissions=["read"]
        )
        
        results = simulator.simulate_paths(plan, num_paths=3)
        
        # Last path should be pessimistic
        assert results[2].success_probability < results[0].success_probability
        assert results[2].success_probability < results[1].success_probability
    
    def test_realistic_path_is_recommended(self):
        """Test that realistic path (middle) is recommended"""
        simulator = StrategicScenarioSimulator()
        
        plan = Plan(
            id="sim_004",
            description="Test recommendation",
            steps=[{"action": "test"}],
            estimated_time=1800,
            estimated_cost=50.0,
            required_permissions=["read"]
        )
        
        results = simulator.simulate_paths(plan, num_paths=3)
        
        # Middle path should be recommended
        assert results[1].recommended is True
        assert results[0].recommended is False
        assert results[2].recommended is False
    
    def test_risk_levels_increase_across_paths(self):
        """Test that risk increases from optimistic to pessimistic"""
        simulator = StrategicScenarioSimulator()
        
        plan = Plan(
            id="sim_005",
            description="Test risk levels",
            steps=[{"action": "test"}],
            estimated_time=1800,
            estimated_cost=50.0,
            required_permissions=["read"]
        )
        
        results = simulator.simulate_paths(plan, num_paths=3)
        
        assert results[0].risk_level == RiskLevel.LOW
        assert results[1].risk_level == RiskLevel.MEDIUM
        assert results[2].risk_level == RiskLevel.HIGH
    
    def test_failure_modes_identified_for_high_risk(self):
        """Test that failure modes are identified"""
        simulator = StrategicScenarioSimulator()
        
        plan = Plan(
            id="sim_006",
            description="Long complex task",
            steps=[{"action": f"step_{i}"} for i in range(15)],
            estimated_time=7200,  # 2 hours
            estimated_cost=50.0,
            required_permissions=["read"]
        )
        
        results = simulator.simulate_paths(plan, num_paths=3)
        
        # Pessimistic path should have failure modes
        pessimistic = results[2]
        assert len(pessimistic.failure_modes) > 0
    
    def test_second_order_effects_analyzed(self):
        """Test that second-order effects are identified"""
        simulator = StrategicScenarioSimulator()
        
        plan = Plan(
            id="sim_007",
            description="Test cascading effects",
            steps=[{"action": "test"}],
            estimated_time=7200,
            estimated_cost=50.0,
            required_permissions=["read"]
        )
        
        results = simulator.simulate_paths(plan, num_paths=3)
        
        # At least one path should have second-order effects
        assert any(len(r.second_order_effects) > 0 for r in results)
    
    def test_simulation_history_recorded(self):
        """Test that simulation history is maintained"""
        simulator = StrategicScenarioSimulator()
        
        plan1 = Plan(
            id="sim_008",
            description="First simulation",
            steps=[{"action": "test"}],
            estimated_time=1800,
            estimated_cost=50.0,
            required_permissions=["read"]
        )
        
        plan2 = Plan(
            id="sim_009",
            description="Second simulation",
            steps=[{"action": "test"}],
            estimated_time=1800,
            estimated_cost=50.0,
            required_permissions=["read"]
        )
        
        simulator.simulate_paths(plan1)
        simulator.simulate_paths(plan2)
        
        assert len(simulator.simulation_history) == 2
        assert simulator.simulation_history[0]['plan_id'] == "sim_008"
        assert simulator.simulation_history[1]['plan_id'] == "sim_009"
