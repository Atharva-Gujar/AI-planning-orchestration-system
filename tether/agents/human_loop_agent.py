"""
Human-in-the-Loop Decision Agent
Intelligent approval workflow
"""

from typing import List, Optional
import time
from datetime import datetime
from ..models import Plan, SimulationResult, ApprovalRequest, RiskLevel


class HumanInLoopAgent:
    """
    Intelligent approval workflow
    Learns when to ask, who to ask, how much context to show
    """
    
    def __init__(self):
        self.approval_history = []
        self.approver_expertise = {}
        self.decision_patterns = {}
    
    def should_request_approval(self, plan: Plan, simulation: SimulationResult) -> bool:
        """
        Determines if human approval is needed
        Based on risk, cost, and learned patterns
        """
        # High risk always requires approval
        if simulation.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            return True
        
        # High cost requires approval
        if plan.estimated_cost > 50:
            return True
        
        # Long duration requires approval
        if plan.estimated_time > 7200:
            return True
        
        # Low success probability requires approval
        if simulation.success_probability < 0.5:
            return True
        
        return False
    
    def create_approval_request(
        self,
        plan: Plan,
        simulation: SimulationResult,
        violations: Optional[List[str]] = None
    ) -> ApprovalRequest:
        """
        Creates a context-rich approval request
        Shows only decision-relevant information
        """
        risk = simulation.risk_level
        approver = self._select_approver(plan, risk)
        
        context = {
            'plan_summary': plan.description,
            'estimated_time': f"{plan.estimated_time // 60} minutes",
            'estimated_cost': f"${plan.estimated_cost:.2f}",
            'success_probability': f"{simulation.success_probability * 100:.0f}%",
            'risk_level': risk.value,
            'key_risks': simulation.failure_modes[:3],
        }
        
        if violations:
            context['constraint_violations'] = violations
        
        urgency = "high" if risk == RiskLevel.CRITICAL else "medium"
        timeout = 300 if urgency == "high" else 1800
        
        request = ApprovalRequest(
            decision_id=f"approval_{plan.id}_{int(time.time())}",
            context=context,
            risk_level=risk,
            recommended_approver=approver,
            urgency=urgency,
            timeout=timeout
        )
        
        return request
    
    def _select_approver(self, plan: Plan, risk: RiskLevel) -> str:
        """Select appropriate approver based on domain and risk"""
        if risk == RiskLevel.CRITICAL:
            return "senior_engineer"
        elif risk == RiskLevel.HIGH:
            return "team_lead"
        else:
            return "any_engineer"
    
    def record_decision(self, request: ApprovalRequest, approved: bool, approver: str):
        """Record approval decision for learning"""
        self.approval_history.append({
            'request': request,
            'approved': approved,
            'approver': approver,
            'timestamp': datetime.now()
        })
