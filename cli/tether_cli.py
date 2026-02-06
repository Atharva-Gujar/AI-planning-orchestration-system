"""
Command-Line Interface for Tether
"""

import argparse
import json
import sys
from pathlib import Path
from tether import TetherOrchestrator, Plan
from config import TetherConfig, Logger


def create_plan_from_file(filepath: str) -> Plan:
    """Load a plan from a JSON file"""
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    return Plan(
        id=data['id'],
        description=data['description'],
        steps=data['steps'],
        estimated_time=data.get('estimated_time', 600),
        estimated_cost=data.get('estimated_cost', 0.0),
        required_permissions=data.get('required_permissions', [])
    )


def cmd_init(args):
    """Initialize Tether configuration"""
    config = TetherConfig(args.config_dir)
    default_config = config.get_default_config()
    config.save_config(default_config)
    print(f"✅ Initialized Tether configuration in {args.config_dir}")
    print(f"📄 Config file: {config.config_file}")



def cmd_validate(args):
    """Validate a plan without executing"""
    config = TetherConfig(args.config_dir)
    cfg = config.load_config()
    
    if not cfg:
        print("❌ No configuration found. Run 'tether init' first.")
        sys.exit(1)
    
    plan = create_plan_from_file(args.plan)
    orchestrator = TetherOrchestrator(
        constraints=cfg['constraints'],
        simulation_depth=cfg.get('simulation_depth', 3),
        reliability_threshold=cfg.get('reliability_threshold', 0.85)
    )
    
    # Validate only
    valid, violations = orchestrator.constraint_agent.validate_plan(plan)
    
    if valid:
        print(f"✅ Plan '{plan.id}' is valid")
    else:
        print(f"❌ Plan '{plan.id}' has violations:")
        for v in violations:
            print(f"   • {v}")


def cmd_simulate(args):
    """Simulate plan execution"""
    config = TetherConfig(args.config_dir)
    cfg = config.load_config()
    
    if not cfg:
        print("❌ No configuration found. Run 'tether init' first.")
        sys.exit(1)
    
    plan = create_plan_from_file(args.plan)
    orchestrator = TetherOrchestrator(
        constraints=cfg['constraints'],
        simulation_depth=cfg.get('simulation_depth', 3)
    )
    
    # Run simulation
    simulations = orchestrator.simulator.simulate_paths(plan, num_paths=3)
    
    print(f"\n🎯 Simulation Results for '{plan.id}':")
    print("=" * 60)
    
    for sim in simulations:
        print(f"\n{sim.path_id}:")
        print(f"  Success Probability: {sim.success_probability * 100:.0f}%")
        print(f"  Estimated Time: {sim.estimated_time // 60} minutes")
        print(f"  Estimated Cost: ${sim.estimated_cost:.2f}")
        print(f"  Risk Level: {sim.risk_level.value.upper()}")
        
        if sim.failure_modes:
            print(f"  Failure Modes:")
            for fm in sim.failure_modes:
                print(f"    • {fm}")
        
        if sim.recommended:
            print(f"  ⭐ RECOMMENDED PATH")


def cmd_execute(args):
    """Execute a plan"""
    config = TetherConfig(args.config_dir)
    logger = Logger(config.logs_dir)
    cfg = config.load_config()
    
    if not cfg:
        print("❌ No configuration found. Run 'tether init' first.")
        sys.exit(1)
    
    plan = create_plan_from_file(args.plan)
    orchestrator = TetherOrchestrator(
        constraints=cfg['constraints'],
        simulation_depth=cfg.get('simulation_depth', 3),
        reliability_threshold=cfg.get('reliability_threshold', 0.85)
    )
    
    # Auto-approval callback
    def auto_approve(request):
        if args.auto_approve:
            logger.info(f"Auto-approving request {request.decision_id}")
            return True
        
        # Interactive approval
        print(f"\n🚨 Approval Required:")
        print(f"   Risk: {request.risk_level.value}")
        print(f"   Cost: {request.context.get('estimated_cost', 'N/A')}")
        print(f"   Time: {request.context.get('estimated_time', 'N/A')}")
        
        response = input("\n   Approve? (y/n): ")
        return response.lower() == 'y'
    
    # Execute
    result = orchestrator.execute_plan(plan, approval_callback=auto_approve)
    
    # Log execution
    config.log_execution(result)
    
    print(f"\n📊 Execution Result:")
    print(f"   Status: {result['status']}")
    
    if result['status'] == 'rejected':
        print(f"   Reason: {result.get('reason', 'Unknown')}")
    elif result['status'] == 'approved':
        print(f"   Success Probability: {result['recommended_simulation']['success_probability'] * 100:.0f}%")


def cmd_health(args):
    """Check system health"""
    config = TetherConfig(args.config_dir)
    cfg = config.load_config()
    
    if not cfg:
        print("❌ No configuration found. Run 'tether init' first.")
        sys.exit(1)
    
    # Load state if exists
    state = config.load_state()
    
    if state:
        print("🏥 System Health:")
        print(f"   Total Executions: {state.get('total_executions', 0)}")
        print(f"   Unreliable Tools: {len(state.get('unreliable_tools', []))}")
        
        if state.get('tool_health'):
            print("\n   Tool Health:")
            for tool, health in state['tool_health'].items():
                print(f"      {tool}: {health['success_rate']*100:.0f}% success rate")
    else:
        print("ℹ️  No state data available. Execute some plans first.")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Tether - AI Planning Orchestration System",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--config-dir',
        default='.tether',
        help='Configuration directory (default: .tether)'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Init command
    parser_init = subparsers.add_parser('init', help='Initialize Tether configuration')
    parser_init.set_defaults(func=cmd_init)
    
    # Validate command
    parser_validate = subparsers.add_parser('validate', help='Validate a plan')
    parser_validate.add_argument('plan', help='Path to plan JSON file')
    parser_validate.set_defaults(func=cmd_validate)
    
    # Simulate command
    parser_simulate = subparsers.add_parser('simulate', help='Simulate plan execution')
    parser_simulate.add_argument('plan', help='Path to plan JSON file')
    parser_simulate.set_defaults(func=cmd_simulate)
    
    # Execute command
    parser_execute = subparsers.add_parser('execute', help='Execute a plan')
    parser_execute.add_argument('plan', help='Path to plan JSON file')
    parser_execute.add_argument('--auto-approve', action='store_true', 
                               help='Auto-approve all requests')
    parser_execute.set_defaults(func=cmd_execute)
    
    # Health command
    parser_health = subparsers.add_parser('health', help='Check system health')
    parser_health.set_defaults(func=cmd_health)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    args.func(args)


if __name__ == '__main__':
    main()
