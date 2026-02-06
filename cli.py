"""
Command-Line Interface for Tether
"""
import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from tether import TetherOrchestrator, Plan
from config import ConfigManager, TetherConfig
from logger import setup_logger


def load_plan_from_file(filepath: str) -> Plan:
    """Load a plan from JSON file"""
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    return Plan(
        id=data['id'],
        description=data['description'],
        steps=data['steps'],
        estimated_time=data['estimated_time'],
        estimated_cost=data['estimated_cost'],
        required_permissions=data['required_permissions'],
        metadata=data.get('metadata', {})
    )


def create_plan_interactive() -> Plan:
    """Create a plan interactively"""
    print("\n=== Create New Plan ===")
    plan_id = input("Plan ID: ")
    description = input("Description: ")
    estimated_time = int(input("Estimated time (seconds): "))
    estimated_cost = float(input("Estimated cost ($): "))
    
    permissions = input("Required permissions (comma-separated): ").split(',')
    permissions = [p.strip() for p in permissions]
    
    steps = []
    print("\nEnter steps (empty action to finish):")
    while True:
        action = input("  Step action: ").strip()
        if not action:
            break
        steps.append({"action": action})
    
    return Plan(
        id=plan_id,
        description=description,
        steps=steps,
        estimated_time=estimated_time,
        estimated_cost=estimated_cost,
        required_permissions=permissions
    )


def execute_plan_command(args):
    """Execute a plan"""
    # Load configuration
    config_manager = ConfigManager()
    
    if args.profile:
        config = config_manager.load_profile(args.profile)
    else:
        config = config_manager.get_default_config()
    
    # Setup logging
    setup_logger(level=config.log_level, log_file=config.log_file)
    
    # Load or create plan
    if args.plan_file:
        plan = load_plan_from_file(args.plan_file)
    else:
        plan = create_plan_interactive()
    
    # Create orchestrator
    constraints = {}
    if args.time_limit or config.default_time_limit:
        constraints['time_limit'] = args.time_limit or config.default_time_limit
    if args.budget or config.default_budget:
        constraints['budget'] = args.budget or config.default_budget
    if args.permissions or config.default_permissions:
        perms = args.permissions.split(',') if args.permissions else config.default_permissions
        constraints['permissions'] = [p.strip() for p in perms]
    
    orchestrator = TetherOrchestrator(
        constraints=constraints,
        simulation_depth=config.simulation_depth,
        reliability_threshold=config.reliability_threshold
    )
    
    # Define approval callback if interactive
    def approval_callback(request):
        if args.auto_approve:
            print(f"\n✅ Auto-approved: {request.decision_id}")
            return True
        
        print(f"\n🚨 APPROVAL REQUIRED")
        print(f"Decision ID: {request.decision_id}")
        print(f"Risk Level: {request.risk_level.value.upper()}")
        print(f"Recommended Approver: {request.recommended_approver}")
        print(f"\nContext:")
        for key, value in request.context.items():
            print(f"  {key}: {value}")
        
        while True:
            response = input("\nApprove this plan? [y/n]: ").lower()
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False
            print("Please enter 'y' or 'n'")
    
    # Execute plan
    print(f"\n🚀 Executing plan: {plan.id}")
    result = orchestrator.execute_plan(
        plan,
        approval_callback=approval_callback if not args.no_approval else None
    )
    
    # Display result
    print(f"\n📊 Execution Result")
    print(f"Status: {result['status']}")
    
    if result['status'] == 'approved':
        print(f"✅ Plan ready for execution")
        sim = result['recommended_simulation']
        print(f"  Success Probability: {sim['success_probability']*100:.0f}%")
        print(f"  Estimated Time: {sim['estimated_time']//60} minutes")
        print(f"  Estimated Cost: ${sim['estimated_cost']:.2f}")
        print(f"  Risk Level: {sim['risk_level']}")
    elif result['status'] == 'rejected':
        print(f"❌ Plan rejected: {result['reason']}")
        if 'violations' in result.get('stages', {}).get('constraint_validation', {}):
            print("\nViolations:")
            for v in result['stages']['constraint_validation']['violations']:
                print(f"  - {v}")
        if 'suggestions' in result:
            print("\nSuggestions:")
            for mod in result['suggestions']['modifications']:
                print(f"  - {mod['suggestion']}")
    
    # Save result if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        print(f"\n💾 Result saved to: {args.output}")


def config_command(args):
    """Manage configurations"""
    config_manager = ConfigManager()
    
    if args.config_action == 'list':
        profiles = config_manager.list_profiles()
        print("\n📋 Available Profiles:")
        for profile in profiles:
            print(f"  - {profile}")
    
    elif args.config_action == 'show':
        if args.profile:
            config = config_manager.load_profile(args.profile)
            print(f"\n📄 Profile: {args.profile}")
        else:
            config = config_manager.get_default_config()
            print("\n📄 Default Configuration")
        
        print(json.dumps(config.to_dict(), indent=2))
    
    elif args.config_action == 'create':
        if not args.profile:
            print("❌ Error: --profile required for create action")
            return
        
        print(f"\n✨ Creating profile: {args.profile}")
        config = TetherConfig()
        
        # Customize configuration
        if input("Customize configuration? [y/n]: ").lower() in ['y', 'yes']:
            config.default_time_limit = int(input(f"Time limit ({config.default_time_limit}s): ") or config.default_time_limit)
            config.default_budget = float(input(f"Budget (${config.default_budget}): ") or config.default_budget)
            perms = input(f"Permissions ({','.join(config.default_permissions)}): ") or ','.join(config.default_permissions)
            config.default_permissions = [p.strip() for p in perms.split(',')]
        
        config_manager.create_profile(args.profile, config)
        print(f"✅ Profile '{args.profile}' created")
    
    elif args.config_action == 'delete':
        if not args.profile:
            print("❌ Error: --profile required for delete action")
            return
        
        confirm = input(f"Delete profile '{args.profile}'? [y/n]: ")
        if confirm.lower() in ['y', 'yes']:
            config_manager.delete_profile(args.profile)
            print(f"✅ Profile '{args.profile}' deleted")


def health_command(args):
    """Check system health"""
    config_manager = ConfigManager()
    config = config_manager.get_default_config()
    
    orchestrator = TetherOrchestrator(
        constraints={'budget': 100.0},
        reliability_threshold=config.reliability_threshold
    )
    
    health = orchestrator.get_system_health()
    
    print("\n🏥 System Health Report")
    print(f"Total Executions: {health['total_executions']}")
    print(f"Approval Rate: {health['approval_rate']*100:.1f}%")
    print(f"Constraint Violations: {health['constraint_violations']}")
    
    if health['unreliable_tools']:
        print(f"\n⚠️  Unreliable Tools: {', '.join(health['unreliable_tools'])}")
    
    if health['tool_health']:
        print("\n📊 Tool Health:")
        for tool, metrics in health['tool_health'].items():
            print(f"  {tool}:")
            print(f"    Success Rate: {metrics['success_rate']*100:.1f}%")
            print(f"    Avg Response: {metrics['avg_response_time']:.2f}s")
            if metrics['drift_detected']:
                print(f"    ⚠️ DRIFT DETECTED")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Tether: AI Planning Orchestration System",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Execute command
    exec_parser = subparsers.add_parser('execute', help='Execute a plan')
    exec_parser.add_argument('--plan-file', '-f', help='Load plan from JSON file')
    exec_parser.add_argument('--profile', '-p', help='Use configuration profile')
    exec_parser.add_argument('--time-limit', '-t', type=int, help='Time limit override (seconds)')
    exec_parser.add_argument('--budget', '-b', type=float, help='Budget override ($)')
    exec_parser.add_argument('--permissions', help='Permissions override (comma-separated)')
    exec_parser.add_argument('--auto-approve', action='store_true', help='Auto-approve all requests')
    exec_parser.add_argument('--no-approval', action='store_true', help='Skip approval checks')
    exec_parser.add_argument('--output', '-o', help='Save result to file')
    exec_parser.set_defaults(func=execute_plan_command)
    
    # Config command
    config_parser = subparsers.add_parser('config', help='Manage configurations')
    config_parser.add_argument('config_action', choices=['list', 'show', 'create', 'delete'])
    config_parser.add_argument('--profile', '-p', help='Profile name')
    config_parser.set_defaults(func=config_command)
    
    # Health command
    health_parser = subparsers.add_parser('health', help='Check system health')
    health_parser.set_defaults(func=health_command)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    args.func(args)


if __name__ == "__main__":
    main()
