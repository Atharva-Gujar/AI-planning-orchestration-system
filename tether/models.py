"""
Core data models for Tether
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime


class ConstraintType(Enum):
    TIME = "time"
    BUDGET = "budget"
    PERMISSIONS = "permissions"
    REGULATIONS = "regulations"


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ExecutionStatus(Enum):
    PENDING = "pending"
    VALIDATING = "validating"
    SIMULATING = "simulating"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Constraint:
    """Represents a real-world constraint on plan execution"""
    type: ConstraintType
    value: Any
    hard_limit: bool = True  # If False, can be exceeded with approval
    description: str = ""


@dataclass
class Plan:
    """Represents an AI-generated execution plan"""
    id: str
    description: str
    steps: List[Dict[str, Any]]
    estimated_time: int  # seconds
    estimated_cost: float
    required_permissions: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class SimulationResult:
    """Results from scenario simulation"""
    path_id: str
    success_probability: float
    estimated_time: int
    estimated_cost: float
    risk_level: RiskLevel
    failure_modes: List[str]
    second_order_effects: List[str]
    recommended: bool = False


@dataclass
class ToolHealth:
    """Monitors the health of external tools/APIs"""
    tool_name: str
    success_rate: float
    avg_response_time: float
    last_failure: Optional[datetime]
    failure_count: int
    drift_detected: bool = False


@dataclass
class ApprovalRequest:
    """Request for human approval"""
    decision_id: str
    context: Dict[str, Any]
    risk_level: RiskLevel
    recommended_approver: str
    urgency: str  # low, medium, high
    timeout: int  # seconds before auto-decision
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class ExecutionResult:
    """Result of plan execution"""
    plan_id: str
    status: ExecutionStatus
    started_at: datetime
    completed_at: Optional[datetime]
    actual_time: Optional[int]
    actual_cost: Optional[float]
    steps_completed: int
    steps_total: int
    error: Optional[str] = None
    output: Optional[Any] = None
