# Installation & Usage Guide

## Installation

### Method 1: pip install (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/tether.git
cd tether

# Install in development mode
pip install -e .

# Or install directly
pip install .
```

### Method 2: From source

```bash
# Clone the repository
git clone https://github.com/yourusername/tether.git
cd tether

# Install dependencies
pip install -r requirements.txt

# Run directly
python tether.py
```

## Quick Start

### 1. Initialize Tether

```bash
# Create configuration file
tether init

# This creates ~/.tether/config.json with default settings
```

### 2. Create a Plan

Create a JSON file describing your task (e.g., `my_plan.json`):

```json
{
  "id": "my_task_001",
  "description": "Analyze customer feedback",
  "steps": [
    {"action": "fetch_data", "source": "database"},
    {"action": "analyze", "method": "sentiment"},
    {"action": "generate_report"}
  ],
  "estimated_time": 1200,
  "estimated_cost": 15.0,
  "required_permissions": ["read", "write"]
}
```

### 3. Validate Your Plan

```bash
# Check if plan passes constraints
tether validate my_plan.json
```

### 4. Execute Your Plan

```bash
# Execute with interactive approval
tether execute my_plan.json

# Execute with auto-approval (use with caution!)
tether execute my_plan.json --auto-approve
```

## Python API Usage

### Basic Example

```python
from tether import TetherOrchestrator, Plan

# Define your plan
plan = Plan(
    id="analysis_001",
    description="Analyze data",
    steps=[{"action": "analyze"}],
    estimated_time=600,
    estimated_cost=10.0,
    required_permissions=["read"]
)

# Create orchestrator
orchestrator = TetherOrchestrator(
    constraints={
        'time_limit': 3600,
        'budget': 100.0,
        'permissions': ['read', 'write']
    }
)

# Execute
result = orchestrator.execute_plan(plan)
print(result['status'])
```

### With Approval Callback

```python
from tether import ApprovalRequest

def approval_handler(request: ApprovalRequest) -> bool:
    print(f"Approval needed for: {request.context['plan_summary']}")
    print(f"Risk level: {request.risk_level.value}")
    
    # Your approval logic here
    return True  # or False

result = orchestrator.execute_plan(plan, approval_callback=approval_handler)
```

### With Persistence

```python
from persistence import TetherPersistence

# Enable persistence
persistence = TetherPersistence("~/.tether/data.db")

# After execution, save to database
persistence.save_execution(
    plan_id=plan.id,
    status=result['status'],
    result=result
)

# Query history
history = persistence.get_execution_history(limit=10)
```

### Monitor Tool Reliability

```python
# Register tools for monitoring
orchestrator.reliability_agent.register_tool("openai_api")
orchestrator.reliability_agent.register_tool("github_api")

# Simulate tool usage
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

## CLI Commands

### Execute Plans

```bash
# Basic execution
tether execute plan.json

# With custom config
tether execute plan.json --config /path/to/config.json

# Auto-approve (dangerous!)
tether execute plan.json --auto-approve

# Verbose logging
tether execute plan.json --verbose
```

### Validate Plans

```bash
# Validate before execution
tether validate plan.json

# Shows constraint violations and suggestions
```

### Check System Health

```bash
# View system health metrics
tether health

# Shows:
# - Total executions
# - Unreliable tools
# - Constraint violations
# - Tool health metrics
```

### Manage Configuration

```bash
# Show current configuration
tether config show

# Initialize new config
tether init

# Save to specific location
tether init --output /path/to/config.json
```

## Configuration

### Config File Format

Edit `~/.tether/config.json`:

```json
{
  "default_time_limit": 3600,
  "default_budget": 100.0,
  "default_permissions": ["read", "write"],
  "simulation_depth": 3,
  "simulation_paths": 3,
  "reliability_threshold": 0.85,
  "performance_threshold": 5.0,
  "high_cost_threshold": 50.0,
  "long_duration_threshold": 7200,
  "low_success_threshold": 0.5,
  "log_level": "INFO",
  "log_file": null,
  "log_to_console": true,
  "persistence_enabled": false,
  "persistence_path": null
}
```

### Environment Variables

Override config with environment variables:

```bash
export TETHER_TIME_LIMIT=7200
export TETHER_BUDGET=200.0
export TETHER_LOG_LEVEL=DEBUG
export TETHER_PERSISTENCE_PATH=~/.tether/data.db

tether execute plan.json
```

## Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_orchestrator.py

# Run specific test
pytest tests/test_orchestrator.py::TestTetherOrchestrator::test_valid_plan_execution
```

## Examples

See the `example_plans/` directory for sample plans:

- `simple_analysis.json` - Low risk, quick task
- `data_scraping.json` - Medium complexity scraping
- `high_risk_migration.json` - Critical database migration

Run examples:

```bash
# Low risk plan (auto-approved)
tether execute example_plans/simple_analysis.json

# Medium risk plan (may require approval)
tether execute example_plans/data_scraping.json

# High risk plan (requires approval)
tether execute example_plans/high_risk_migration.json
```

## Troubleshooting

### Import Errors

```bash
# Make sure tether is installed
pip install -e .

# Or add to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/path/to/tether"
```

### Permission Denied

```bash
# Check config file permissions
chmod 600 ~/.tether/config.json

# Check database permissions (if using persistence)
chmod 600 ~/.tether/data.db
```

### Config Not Found

```bash
# Initialize config
tether init
```

## Next Steps

- Read the [Architecture documentation](ARCHITECTURE.md)
- Check out [Examples](examples.py)
- See [Contributing guide](CONTRIBUTING.md) to add features
