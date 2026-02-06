"""
LangChain integration for Tether
Allows Tether to work as a middleware layer for LangChain agents
"""

from typing import Dict, Any, Optional, List
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from tether import (
    TetherOrchestrator,
    Plan,
    ApprovalRequest
)


class LangChainIntegration:
    """
    Integration adapter for LangChain
    
    Wraps LangChain agent execution with Tether's constraint reasoning,
    scenario simulation, and reliability monitoring.
    """
    
    def __init__(
        self,
        orchestrator: TetherOrchestrator,
        auto_approve_low_risk: bool = True
    ):
        self.orchestrator = orchestrator
        self.auto_approve_low_risk = auto_approve_low_risk
        self.execution_history = []
    
    def create_plan_from_langchain_action(
        self,
        action: Dict[str, Any],
        estimated_time: int = 60,
        estimated_cost: float = 1.0
    ) -> Plan:
        """
        Convert LangChain action/tool call into a Tether Plan
        
        Args:
            action: LangChain action dictionary with 'tool' and 'tool_input'
            estimated_time: Estimated execution time in seconds
            estimated_cost: Estimated cost in dollars
        
        Returns:
            Tether Plan object
        """
        tool_name = action.get('tool', 'unknown')
        tool_input = action.get('tool_input', {})
        
        # Infer permissions from tool type
        permissions = self._infer_permissions(tool_name)
        
        plan = Plan(
            id=f"langchain_{len(self.execution_history)}_{tool_name}",
            description=f"LangChain tool execution: {tool_name}",
            steps=[{
                'action': 'execute_tool',
                'tool': tool_name,
                'input': tool_input
            }],
            estimated_time=estimated_time,
            estimated_cost=estimated_cost,
            required_permissions=permissions
        )
        
        return plan
    
    def _infer_permissions(self, tool_name: str) -> List[str]:
        """Infer required permissions from tool name"""
        permissions = []
        
        # Read operations
        if any(keyword in tool_name.lower() for keyword in ['search', 'read', 'fetch', 'get', 'query']):
            permissions.append('read')
        
        # Write operations
        if any(keyword in tool_name.lower() for keyword in ['write', 'create', 'update', 'delete', 'save']):
            permissions.append('write')
        
        # API access
        if 'api' in tool_name.lower() or 'http' in tool_name.lower():
            permissions.append('api_access')
        
        # Default to read if nothing matched
        if not permissions:
            permissions.append('read')
        
        return permissions
    
    def validate_and_execute(
        self,
        action: Dict[str, Any],
        execute_callback: Optional[callable] = None,
        approval_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Validate action through Tether gates before execution
        
        Args:
            action: LangChain action to validate and execute
            execute_callback: Function to actually execute the action
            approval_callback: Function to handle approval requests
        
        Returns:
            Execution result with Tether metadata
        """
        # Create plan from action
        plan = self.create_plan_from_langchain_action(action)
        
        # Run through Tether orchestration
        tether_result = self.orchestrator.execute_plan(
            plan,
            approval_callback=approval_callback
        )
        
        # Store in history
        self.execution_history.append({
            'plan': plan,
            'tether_result': tether_result,
            'action': action
        })
        
        # Handle different outcomes
        if tether_result['status'] == 'rejected':
            return {
                'success': False,
                'error': 'Plan rejected by Tether',
                'reason': tether_result['reason'],
                'violations': tether_result.get('stages', {}).get('constraint_validation', {}).get('violations', []),
                'suggestions': tether_result.get('suggestions', {})
            }
        
        elif tether_result['status'] == 'awaiting_approval':
            return {
                'success': False,
                'error': 'Awaiting human approval',
                'approval_request': tether_result['stages']['approval']['request']
            }
        
        elif tether_result['status'] == 'approved':
            # Execute the action if callback provided
            if execute_callback:
                try:
                    execution_result = execute_callback(action)
                    
                    # Record success in reliability agent
                    tool_name = action.get('tool', 'unknown')
                    self.orchestrator.reliability_agent.record_execution(
                        tool_name,
                        success=True,
                        response_time=0.5  # Would need actual timing
                    )
                    
                    return {
                        'success': True,
                        'result': execution_result,
                        'tether_metadata': {
                            'success_probability': tether_result['recommended_simulation']['success_probability'],
                            'risk_level': tether_result['recommended_simulation']['risk_level']
                        }
                    }
                    
                except Exception as e:
                    # Record failure in reliability agent
                    tool_name = action.get('tool', 'unknown')
                    self.orchestrator.reliability_agent.record_execution(
                        tool_name,
                        success=False,
                        response_time=0.5
                    )
                    
                    return {
                        'success': False,
                        'error': str(e),
                        'tether_metadata': tether_result
                    }
            else:
                return {
                    'success': True,
                    'approved': True,
                    'ready_for_execution': True,
                    'tether_metadata': tether_result
                }
    
    def get_tool_health(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get reliability metrics for a specific LangChain tool"""
        health = self.orchestrator.reliability_agent.get_tool_health(tool_name)
        
        if health:
            return {
                'tool_name': health.tool_name,
                'success_rate': health.success_rate,
                'avg_response_time': health.avg_response_time,
                'failure_count': health.failure_count,
                'drift_detected': health.drift_detected,
                'last_failure': health.last_failure.isoformat() if health.last_failure else None
            }
        return None
    
    def get_unreliable_tools(self) -> List[str]:
        """Get list of LangChain tools that are currently unreliable"""
        return self.orchestrator.reliability_agent.get_unreliable_tools()


# Example usage
if __name__ == "__main__":
    print("LangChain Integration Example")
    print("=" * 50)
    
    # Create Tether orchestrator
    from tether import TetherOrchestrator
    
    orchestrator = TetherOrchestrator(
        constraints={
            'time_limit': 300,  # 5 minutes
            'budget': 10.0,
            'permissions': ['read', 'api_access']
        }
    )
    
    # Create integration
    integration = LangChainIntegration(orchestrator)
    
    # Simulate LangChain action
    action = {
        'tool': 'search_api',
        'tool_input': {'query': 'AI safety research'}
    }
    
    # Validate and execute
    result = integration.validate_and_execute(action)
    
    print("\nResult:")
    print(result)
