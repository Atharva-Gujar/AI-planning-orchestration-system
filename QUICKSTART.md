# Quick Start Guide

## Installation

### From source

```bash
cd "AI planning orchestration system"
pip install -e .
```

### With development dependencies

```bash
pip install -e ".[dev]"
```

## Basic Usage

### 1. Using Python API

```python
from tether import TetherOrchestrator, Plan

# Define your plan
plan = Plan(
    id="my_task_001",
    description="Analyze customer feedback",
    steps=[
        {"action": "fetch_data", "source": "database"},
        {"action": "analyze", "method": "sentiment"},
        {"action": "report"}
    ],
    estimated_time=1200,  # 20 minutes
    estimated_cost=10.0,
    required_permissions=["read", "write"]
)

# Create orchestrator with constraints
orchestrator = TetherOrchestrator(
    constraints={
        'time_limit': 3600,      # 1 hour max
        'budget': 50.0,          # $50 max
        'permissions': ['read', 'write']
    },
    simulation_depth=3,
    reliability_threshold=0.85
)

# Execute the plan
result = orchestrator.execute_plan(plan)

# Check result
if result['status'] == 'approved':
    print("✅ Plan ready for execution!")
    print(f"Success probability: {result['recommended_simulation']['success_probability']}")
elif result['status'] == 'rejected':
    print("❌ Plan rejected due to constraint violations")
    print("Violations:", result['stages']['constraint_validation']['violations'])
```

### 2. Using CLI

```bash
# Execute a plan from file
tether execute --plan-file my_plan.json --profile production

# Create a plan interactively
tether execute --profile development

# Check system health
tether health

# Manage configurations
tether config list
tether config show --profile production
tether config create --profile my-profile
```

### 3. Configuration Management

```python
from config import ConfigManager, create_production_config

# Create config manager
manager = ConfigManager()

# Create and save a profile
prod_config = create_production_config()
manager.create_profile("production", prod_config)

# Load and use profile
config = manager.load_profile("production")
```

### 4. With Real Execution

```python
from tether import Plan, ToolReliabilityAgent
from execution import ExecutionEngine

# Create reliability agent
reliability = ToolReliabilityAgent()

# Create execution engine
engine = ExecutionEngine(reliability)

# Register your tools
def my_tool(step):
    # Your tool implementation
    return {"success": True, "cost": 0.10}

engine.register_tool('my_action', my_tool)

# Execute plan
result = engine.execute_plan(plan)
print(f"Execution {'succeeded' if result.success else 'failed'}")
print(f"Duration: {result.duration:.2f}s")
print(f"Cost: ${result.actual_cost:.2f}")
```

## Understanding the Results

The orchestrator returns a comprehensive result dictionary:

```python
{
    'plan_id': 'my_task_001',
    'status': 'approved',  # or 'rejected', 'awaiting_approval'
    'stages': {
        'constraint_validation': {
            'valid': True,
            'violations': []
        },
        'simulation': {
            'paths_explored': 3,
            'recommended_path': 'my_task_001_path_1',
            'success_probability': 0.65,
            'risk_level': 'medium'
        },
        'approval': {
            'required': False
        }
    },
    'recommended_simulation': {
        'success_probability': 0.65,
        'estimated_time': 1560,
        'estimated_cost': 12.0,
        'risk_level': 'medium'
    }
}
```

## Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov

# Run specific test file
pytest tests/test_constraint_agent.py

# Run with verbose output
pytest -v
```

## Run Examples

```bash
# Run all examples
python examples.py

# Run the main demo
python tether.py

# Run execution engine example
python execution.py
```

## Create a Plan File

Create `my_plan.json`:

```json
{
  "id": "data_analysis_001",
  "description": "Analyze sales data",
  "steps": [
    {"action": "fetch_data", "source": "database", "query": "SELECT * FROM sales"},
    {"action": "clean_data"},
    {"action": "analyze", "method": "regression"},
    {"action": "generate_report", "format": "pdf"}
  ],
  "estimated_time": 1800,
  "estimated_cost": 25.0,
  "required_permissions": ["read", "write"],
  "metadata": {
    "priority": "high",
    "department": "analytics"
  }
}
```

Then execute it:

```bash
tether execute --plan-file my_plan.json
```

## Next Steps

- Check out `examples.py` for more detailed use cases
- Read the full README.md for architecture details
- Explore `ARCHITECTURE.md` for system design
- See `CONTRIBUTING.md` for integration development
- Review test files in `tests/` for usage patterns

## Common Workflows

### Development Workflow

```bash
# 1. Install with dev dependencies
pip install -e ".[dev]"

# 2. Run tests
pytest

# 3. Format code
black .

# 4. Type check
mypy tether.py

# 5. Lint code
flake8 .
```

### Production Workflow

```bash
# 1. Create production config
tether config create --profile production

# 2. Execute plan with production settings
tether execute --plan-file plan.json --profile production

# 3. Check system health
tether health

# 4. View execution history (via Python API)
python -c "from persistence import TetherDatabase; db = TetherDatabase(); print(db.get_statistics())"
```
