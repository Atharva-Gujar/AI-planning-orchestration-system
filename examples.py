"""
Example Usage of Tether AI Planning Orchestration System
"""

from tether import (
    TetherOrchestrator,
    Plan,
    ApprovalRequest,
    Constraint,
    ConstraintType
)
import json


def example_1_simple_plan():
    """Example 1: Simple plan that passes all gates"""
    print("\n" + "="*60)
    print("EXAMPLE 1: Simple Plan (Low Risk)")
    print("="*60)
    
    plan = Plan(
        id="simple_001",
        description="Analyze 100 customer reviews",
        steps=[
            {"action": "fetch_reviews", "count": 100},
            {"action": "sentiment_analysis"},
            {"action": "generate_report"}
        ],
        estimated_time=600,  # 10 minutes
        estimated_cost=5.0,
        required_permissions=["read"]
    )
    
    orchestrator = TetherOrchestrator(
        constraints={
            'time_limit': 1800,  # 30 minutes
            'budget': 20.0,
            'permissions': ['read', 'write']
        }
    )
    
    result = orchestrator.execute_plan(plan)
    print("\n✅ Result:", result['status'])
    print(f"Success Probability: {result['recommended_simulation']['success_probability']*100:.0f}%")


def example_2_constraint_violation():
    """Example 2: Plan that violates constraints"""
    print("\n" + "="*60)
    print("EXAMPLE 2: Constraint Violation")
    print("="*60)
    
    plan = Plan(
        id="violation_001",
        description="Large-scale data scraping",
        steps=[{"action": "scrape", "count": 10000}],
        estimated_time=7200,  # 2 hours
        estimated_cost=150.0,
        required_permissions=["read", "write", "admin"]
    )
    
    orchestrator = TetherOrchestrator(
        constraints={
            'time_limit': 3600,  # 1 hour (VIOLATED)
            'budget': 100.0,     # $100 (VIOLATED)
            'permissions': ['read', 'write']  # Missing 'admin' (VIOLATED)
        }
    )
    
    result = orchestrator.execute_plan(plan)
    print("\n❌ Result:", result['status'])
    print("Violations:", result['stages']['constraint_validation']['violations'])
    print("\n💡 Suggestions:")
    print(json.dumps(result['suggestions'], indent=2))


def example_3_approval_required():
    """Example 3: High-risk plan requiring human approval"""
    print("\n" + "="*60)
    print("EXAMPLE 3: Human Approval Required")
    print("="*60)
    
    plan = Plan(
        id="highrisk_001",
        description="Production database migration",
        steps=[
            {"action": "backup_database"},
            {"action": "migrate_schema"},
            {"action": "verify_data"}
        ],
        estimated_time=5400,  # 90 minutes
        estimated_cost=75.0,
        required_permissions=["read", "write", "admin"]
    )
    
    orchestrator = TetherOrchestrator(
        constraints={
            'time_limit': 7200,  # 2 hours
            'budget': 100.0,
            'permissions': ['read', 'write', 'admin']
        }
    )
    
    def approval_handler(request: ApprovalRequest) -> bool:
        print("\n🚨 APPROVAL REQUESTED")
        print(f"Risk Level: {request.risk_level.value.upper()}")
        print(f"Approver: {request.recommended_approver}")
        print(f"Urgency: {request.urgency}")
        print("\nContext:")
        for key, value in request.context.items():
            print(f"  {key}: {value}")
        
        # Simulate human decision
        decision = True  # Approve
        print(f"\n{'✅ APPROVED' if decision else '❌ REJECTED'}")
        return decision
    
    result = orchestrator.execute_plan(plan, approval_callback=approval_handler)
    print(f"\nFinal Status: {result['status']}")


def example_4_tool_reliability():
    """Example 4: Monitoring tool reliability"""
    print("\n" + "="*60)
    print("EXAMPLE 4: Tool Reliability Monitoring")
    print("="*60)
    
    orchestrator = TetherOrchestrator(
        constraints={'budget': 100.0},
        reliability_threshold=0.80
    )
    
    # Simulate tool executions
    print("\nSimulating API calls...")
    
    orchestrator.reliability_agent.register_tool("github_api")
    orchestrator.reliability_agent.register_tool("openai_api")
    
    # Simulate successful and failed calls
    for i in range(10):
        # GitHub API - mostly successful
        success = i < 8
        orchestrator.reliability_agent.record_execution("github_api", success, 0.5)
        
        # OpenAI API - degrading performance
        success = i < 5
        orchestrator.reliability_agent.record_execution("openai_api", success, 1.2)
    
    # Check health
    health = orchestrator.get_system_health()
    print("\n🏥 System Health Report:")
    print(json.dumps(health['tool_health'], indent=2))
    
    unreliable = orchestrator.reliability_agent.get_unreliable_tools()
    if unreliable:
        print(f"\n⚠️  Unreliable tools detected: {unreliable}")


if __name__ == "__main__":
    print("\n" + "🔗 TETHER: AI PLANNING ORCHESTRATION EXAMPLES")
    print("The reality layer for AI agents\n")
    
    # Run all examples
    example_1_simple_plan()
    example_2_constraint_violation()
    example_3_approval_required()
    example_4_tool_reliability()
    
    print("\n" + "="*60)
    print("Examples completed. Tether keeps AI agents grounded.")
    print("="*60 + "\n")
