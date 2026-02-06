# Tether Usage Guide

Complete guide to using Tether AI Planning Orchestration System.

## Table of Contents
1. [Installation](#installation)
2. [Quick Start](#quick-start)
3. [CLI Usage](#cli-usage)
4. [Python API](#python-api)
5. [Configuration](#configuration)
6. [Integrations](#integrations)
7. [Testing](#testing)
8. [Advanced Features](#advanced-features)

## Installation

### Basic Installation
```bash
# Clone the repository
git clone https://github.com/yourusername/tether.git
cd tether

# Install dependencies
pip install -r requirements.txt

# Install as package (optional)
pip install -e .
```

### With LangChain Integration
```bash
pip install -e ".[langchain]"
```

### Development Setup
```bash
pip install -e ".[dev]"
```

## Quick Start

### 1. Using the CLI

Execute a plan from a JSON file:
```bash
python cli.py execute examples/example_plan.json
```

Validate a plan without executing:
```bash
python cli.py validate examples/example_plan.json
```

Check system health:
```bash
python cli.py health
```

### 2. Using Python API

```python
from tether import TetherOrchestrator, Plan

# Create a plan
plan = Plan(
    id="my_task",
    description="Analyze customer data",
    steps=[
        {"action": "fetch_data"},
        {"action": "analyze"},
        {"action": "report"}
    ],
    estimated_time=1800,  # 30 minutes
    estimated_cost=10.0,
    required_permissions=["read", "write"]
)

# Create orchestrator
orchestrator = TetherOrchestrator(
    constraints={
        'time_limit': 3600,
        'budget': 50.0,
        'permissions': ['read', 'write']
    }
)

# Execute
result = orchestrator.execute_plan(plan)

if result['status'] == 'approved':
    print("✅ Ready to execute!")
    print(f"Success probability: {result['recommended_simulation']['success_probability']}")
```

## CLI Usage

### Execute Command
```bash
# Basic execution
python cli.py execute examples/example_plan.json

# Auto-approve all requests
python cli.py execute examples/example_plan.json --auto-approve

# Save result to file
python cli.py execute examples/example_plan.json -o result.json
```

### Validate Command
```bash
# Validate plan constraints and simulate outcomes
python cli.py validate examples/example_plan.json
```

### Config Command
```bash
# Show all configuration
python cli.py config show

# Get specific config value
python cli.py config get --key constraints.budget

# Set config value
python cli.py config set --key constraints.budget --value 100.0

# Reset to defaults
python cli.py config reset
```

### Health Command
```bash
# Check system health and tool reliability
python cli.py health
```

## Python API

### Basic Orchestration

```python
from tether import TetherOrchestrator, Plan

# Initialize with constraints
orchestrator = TetherOrchestrator(
    constraints={
        'time_limit': 3600,      # 1 hour max
        'budget': 100.0,         # $100 max
        'permissions': ['read', 'write', 'api_access']
    },
    simulation_depth=3,
    reliability_threshold=0.85
)

# Create and execute plan
plan = Plan(...)
result = orchestrator.execute_plan(plan)
```

### With Approval Callback

```python
def my_approval_handler(request):
    print(f"Approval needed: {request.context}")
    # Your approval logic here
    return True  # or False

result = orchestrator.execute_plan(
    plan,
    approval_callback=my_approval_handler
)
```

### Monitoring Tool Health

```python
# Register tools for monitoring
orchestrator.reliability_agent.register_tool("openai_api")
orchestrator.reliability_agent.register_tool("github_api")

# Record executions
orchestrator.reliability_agent.record_execution(
    "openai_api",
    success=True,
    response_time=1.2
)

# Check health
health = orchestrator.reliability_agent.get_tool_health("openai_api")
print(f"Success rate: {health.success_rate}")

# Get unreliable tools
unreliable = orchestrator.reliability_agent.get_unreliable_tools()
```

## Configuration

### Configuration File

Tether stores configuration in `~/.tether/config.json`:

```json
{
  "constraints": {
    "time_limit": 3600,
    "budget": 100.0,
    "permissions": ["read", "write"]
  },
  "simulation": {
    "depth": 3,
    "num_paths": 3
  },
  "reliability": {
    "threshold": 0.85,
    "alert_enabled": true
  },
  "approval": {
    "auto_approve_low_risk": true,
    "timeout_seconds": 1800
  }
}
```

### Using ConfigManager

```python
from config.manager import ConfigManager

config = ConfigManager()

# Get values
budget = config.get('constraints.budget')
threshold = config.get('reliability.threshold')

# Set values
config.set('constraints.budget', 200.0)
config.set('simulation.depth', 5)

# Export/Import
config.export_config(Path('my_config.json'))
config.import_config(Path('backup_config.json'))
```

## Integrations

### LangChain Integration

```python
from integrations.langchain_integration import LangChainIntegration
from tether import TetherOrchestrator

# Create orchestrator
orchestrator = TetherOrchestrator(
    constraints={'budget': 50.0}
)

# Create integration
integration = LangChainIntegration(orchestrator)

# Use with LangChain actions
action = {
    'tool': 'search_api',
    'tool_input': {'query': 'AI research'}
}

result = integration.validate_and_execute(action)

# Check tool health
health = integration.get_tool_health('search_api')
```

## Testing

### Run All Tests
```bash
pytest
```

### Run Specific Test File
```bash
pytest tests/test_constraint_agent.py
```

### Run with Coverage
```bash
pytest --cov=. --cov-report=html
```

### Run Specific Test
```bash
pytest tests/test_orchestrator.py::TestTetherOrchestrator::test_valid_plan_execution
```

## Advanced Features

### Custom Constraints

```python
from tether import Constraint, ConstraintType

custom_constraints = {
    'security_level': Constraint(
        type=ConstraintType.REGULATIONS,
        value='high',
        hard_limit=True,
        description='Security clearance required'
    )
}
```

### Persistence

```python
from persistence import TetherDatabase

db = TetherDatabase()

# Save execution
db.save_execution(plan_id, result)

# Get history
history = db.get_execution_history(limit=50)

# Get statistics
violations = db.get_violation_stats()
approvals = db.get_approval_stats()
```

### Custom Alert Handlers

```python
def my_alert_handler(alert):
    print(f"Alert: {alert['message']}")
    # Send to monitoring system, etc.

orchestrator.reliability_agent.add_alert_callback(my_alert_handler)
```

### Logging

```python
from config.logging_config import get_logger

logger = get_logger(
    name='tether',
    level='DEBUG',
    log_file=Path('tether.log')
)

logger.info("Starting plan execution")
logger.error("Tool failure detected")
```

## Best Practices

1. **Always validate plans** before execution
2. **Monitor tool health** regularly
3. **Use persistence** to track history
4. **Set realistic constraints** based on your environment
5. **Implement proper approval callbacks** for production use
6. **Enable logging** for debugging
7. **Run tests** before deploying changes

## Troubleshooting

### Plan Rejected
- Check constraint violations in result
- Review suggestions for modifications
- Adjust constraints if too restrictive

### High Tool Failure Rate
- Check tool health metrics
- Implement retry logic
- Use fallback tools

### Approval Timeout
- Increase timeout in config
- Implement async approval workflow
- Use auto-approval for low-risk tasks

## Getting Help

- GitHub Issues: Report bugs and request features
- Discussions: Ask questions and share ideas
- Documentation: Read ARCHITECTURE.md for internals
