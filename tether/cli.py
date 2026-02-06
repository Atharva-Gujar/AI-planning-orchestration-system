#!/usr/bin/env python3
"""
Command-line interface for Tether
"""

import argparse
import json
import sys
from pathlib import Path

from tether import TetherOrchestrator, Plan, Config
from tether.persistence import Database


def create_plan_from_file(filepath: str) -> Plan:
    """Load plan from JSON file"""
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    return Plan(
        id=data['id'],
        description=data['description'],
        steps=data['steps'],
        estimated_time=data['estimated_time'],
        estimated_cost=data['estimated_cost'],
        required_permissions=data.get('required_permissions', []),
        metadata=data.get('metadata', {})
    )


def execute_command(args):
    """Execute a plan"""
    config = Config(args.config) if args.config else Config()
    orchestrator = TetherOrchestrator(config=config)
    
    plan = create_plan_from_file(args.plan)
    
    # Define approval callback if interactive
    def approval_callback(request):
        if args.auto_approve:
            return True
        
        print("\n🚨 APPROVAL REQUIRED")
        print(f"Decision ID: {request.decision_id}")
        print(f"Risk Level: {request.risk_level.value.upper()}")
        print(f"Approver: {request.recommended_approver}")
        print(f"Urgency: {request.urgency}")
        print("\nContext:")
        for key, value in request.context.items():
            print(f"  {key}: {value}")
        
        response = input("\nApprove? (y/n): ")
        return response.lower() == 'y'
    
    result = orchestrator.execute_plan(plan, approval_callback=approval_callback)
    
    print("\n" + "="*60)
    print("EXECUTION RESULT")
    print("="*60)
    print(json.dumps(result, indent=2, default=str))
    
    orchestrator.close()
    return 0 if result['status'] != 'rejected' else 1


def health_command(args):
    """Show system health"""
    config = Config(args.config) if args.config else Config()
    orchestrator = TetherOrchestrator(config=config)
    
    health = orchestrator.get_system_health()
    
    print("\n" + "="*60)
    print("SYSTEM HEALTH")
    print("="*60)
    print(json.dumps(health, indent=2, default=str))
    
    orchestrator.close()
    return 0


def history_command(args):
    """Show execution history"""
    config = Config(args.config) if args.config else Config()
    db = Database(config.get('database.path', 'tether.db'))
    
    executions = db.get_executions()
    
    print("\n" + "="*60)
    print("EXECUTION HISTORY")
    print("="*60)
    
    for exec in executions[:args.limit]:
        print(f"\nPlan ID: {exec['plan_id']}")
        print(f"Status: {exec['status']}")
        print(f"Started: {exec['started_at']}")
        print(f"Duration: {exec.get('actual_time', 'N/A')}s")
        print(f"Cost: ${exec.get('actual_cost', 'N/A')}")
        print("-" * 40)
    
    db.close()
    return 0


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Tether: AI Planning Orchestration System'
    )
    parser.add_argument(
        '--config', '-c',
        help='Path to configuration file'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Execute command
    execute_parser = subparsers.add_parser('execute', help='Execute a plan')
    execute_parser.add_argument('plan', help='Path to plan JSON file')
    execute_parser.add_argument('--auto-approve', action='store_true',
                               help='Automatically approve all requests')
    execute_parser.set_defaults(func=execute_command)
    
    # Health command
    health_parser = subparsers.add_parser('health', help='Show system health')
    health_parser.set_defaults(func=health_command)
    
    # History command
    history_parser = subparsers.add_parser('history', help='Show execution history')
    history_parser.add_argument('--limit', type=int, default=10,
                               help='Number of records to show')
    history_parser.set_defaults(func=history_command)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
