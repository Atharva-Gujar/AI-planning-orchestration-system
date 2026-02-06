"""
Unit tests for Tool Reliability Agent
"""
import pytest
from datetime import datetime, timedelta
from tether import ToolReliabilityAgent, ToolHealth


class TestToolReliabilityAgent:
    
    def test_register_tool(self):
        """Test tool registration"""
        agent = ToolReliabilityAgent(reliability_threshold=0.85)
        agent.register_tool("test_api")
        
        assert "test_api" in agent.tool_metrics
        health = agent.tool_metrics["test_api"]
        assert health.success_rate == 1.0
        assert health.failure_count == 0
    
    def test_record_successful_execution(self):
        """Test recording successful tool execution"""
        agent = ToolReliabilityAgent()
        agent.register_tool("test_api")
        
        agent.record_execution("test_api", success=True, response_time=0.5)
        
        health = agent.get_tool_health("test_api")
        assert health.success_rate > 0.9
        assert health.avg_response_time > 0
    
    def test_record_failed_execution(self):
        """Test recording failed tool execution"""
        agent = ToolReliabilityAgent()
        agent.register_tool("test_api")
        
        agent.record_execution("test_api", success=False, response_time=1.0)
        
        health = agent.get_tool_health("test_api")
        assert health.failure_count == 1
        assert health.last_failure is not None
    
    def test_success_rate_degradation_detection(self):
        """Test detection of success rate degradation"""
        agent = ToolReliabilityAgent(reliability_threshold=0.80)
        agent.register_tool("degrading_api")
        
        # Simulate degrading performance
        for i in range(10):
            success = i < 5  # 50% success rate
            agent.record_execution("degrading_api", success, 0.5)
        
        health = agent.get_tool_health("degrading_api")
        assert health.drift_detected is True
    
    def test_get_unreliable_tools(self):
        """Test identification of unreliable tools"""
        agent = ToolReliabilityAgent(reliability_threshold=0.80)
        
        # Create one reliable and one unreliable tool
        agent.register_tool("reliable_api")
        agent.register_tool("unreliable_api")
        
        # Reliable tool - mostly successes
        for _ in range(10):
            agent.record_execution("reliable_api", True, 0.5)
        
        # Unreliable tool - mostly failures
        for i in range(10):
            agent.record_execution("unreliable_api", i < 3, 0.5)
        
        unreliable = agent.get_unreliable_tools()
        assert "unreliable_api" in unreliable
        assert "reliable_api" not in unreliable
    
    def test_alert_callback_triggered(self):
        """Test that alerts trigger callbacks"""
        agent = ToolReliabilityAgent(reliability_threshold=0.80)
        
        alerts_received = []
        
        def callback(alert):
            alerts_received.append(alert)
        
        agent.add_alert_callback(callback)
        agent.register_tool("failing_api")
        
        # Trigger reliability alert
        for i in range(10):
            agent.record_execution("failing_api", i < 2, 0.5)
        
        assert len(alerts_received) > 0
        assert any("reliability" in alert['type'] for alert in alerts_received)
    
    def test_performance_degradation_alert(self):
        """Test alert for slow response times"""
        agent = ToolReliabilityAgent()
        
        alerts_received = []
        agent.add_alert_callback(lambda a: alerts_received.append(a))
        agent.register_tool("slow_api")
        
        # Simulate slow responses
        for _ in range(10):
            agent.record_execution("slow_api", True, 6.0)  # > 5s threshold
        
        assert len(alerts_received) > 0
        assert any("performance" in alert['type'] for alert in alerts_received)
    
    def test_exponential_moving_average_calculation(self):
        """Test that EMA is calculated correctly for metrics"""
        agent = ToolReliabilityAgent()
        agent.register_tool("test_api")
        
        # Record mixed success/failure
        agent.record_execution("test_api", True, 1.0)
        agent.record_execution("test_api", True, 1.0)
        agent.record_execution("test_api", False, 1.0)
        
        health = agent.get_tool_health("test_api")
        # With alpha=0.1, success rate should be between 0 and 1
        assert 0.0 < health.success_rate < 1.0
