"""
Tool Reliability & Drift Agent
Runtime monitoring: Prevents silent system rot
"""

from typing import Dict, List, Optional, Callable
from datetime import datetime
from ..models import ToolHealth


class ToolReliabilityAgent:
    """
    Runtime monitoring: Prevents silent system rot
    Monitors API failures, data drift, scraper decay
    """
    
    def __init__(self, reliability_threshold: float = 0.85):
        self.reliability_threshold = reliability_threshold
        self.tool_metrics: Dict[str, ToolHealth] = {}
        self.alert_callbacks: List[Callable] = []
    
    def register_tool(self, tool_name: str):
        """Register a tool for monitoring"""
        self.tool_metrics[tool_name] = ToolHealth(
            tool_name=tool_name,
            success_rate=1.0,
            avg_response_time=0.0,
            last_failure=None,
            failure_count=0
        )
    
    def record_execution(self, tool_name: str, success: bool, response_time: float):
        """Record tool execution metrics"""
        if tool_name not in self.tool_metrics:
            self.register_tool(tool_name)
        
        tool = self.tool_metrics[tool_name]
        
        # Update success rate (exponential moving average)
        alpha = 0.1
        tool.success_rate = alpha * (1.0 if success else 0.0) + (1 - alpha) * tool.success_rate
        
        # Update response time
        tool.avg_response_time = alpha * response_time + (1 - alpha) * tool.avg_response_time
        
        if not success:
            tool.failure_count += 1
            tool.last_failure = datetime.now()
        
        # Check for drift
        if tool.success_rate < self.reliability_threshold:
            tool.drift_detected = True
            self._trigger_alert(tool_name, "reliability", tool.success_rate)
        
        # Check for performance degradation
        if tool.avg_response_time > 5.0:
            self._trigger_alert(tool_name, "performance", tool.avg_response_time)
    
    def get_tool_health(self, tool_name: str) -> Optional[ToolHealth]:
        """Get current health metrics for a tool"""
        return self.tool_metrics.get(tool_name)
    
    def get_unreliable_tools(self) -> List[str]:
        """Get list of tools below reliability threshold"""
        return [
            name for name, health in self.tool_metrics.items()
            if health.success_rate < self.reliability_threshold
        ]
    
    def _trigger_alert(self, tool_name: str, alert_type: str, value: float):
        """Trigger alerts for tool issues"""
        alert = {
            'timestamp': datetime.now(),
            'tool': tool_name,
            'type': alert_type,
            'value': value,
            'message': f"{tool_name} {alert_type} issue detected: {value:.2f}"
        }
        
        for callback in self.alert_callbacks:
            callback(alert)
    
    def add_alert_callback(self, callback: Callable):
        """Add callback function for alerts"""
        self.alert_callbacks.append(callback)
