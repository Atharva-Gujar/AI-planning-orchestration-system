"""
Logging system for Tether
"""
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


class TetherLogger:
    """Centralized logging for Tether"""
    
    def __init__(
        self,
        name: str = "tether",
        level: str = "INFO",
        log_file: Optional[str] = None,
        console: bool = True
    ):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        
        # Remove existing handlers
        self.logger.handlers.clear()
        
        # Console handler
        if console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(getattr(logging, level.upper()))
            console_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)
        
        # File handler
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(getattr(logging, level.upper()))
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
    
    def debug(self, msg: str, **kwargs):
        """Log debug message"""
        self.logger.debug(msg, extra=kwargs)
    
    def info(self, msg: str, **kwargs):
        """Log info message"""
        self.logger.info(msg, extra=kwargs)
    
    def warning(self, msg: str, **kwargs):
        """Log warning message"""
        self.logger.warning(msg, extra=kwargs)
    
    def error(self, msg: str, **kwargs):
        """Log error message"""
        self.logger.error(msg, extra=kwargs)
    
    def critical(self, msg: str, **kwargs):
        """Log critical message"""
        self.logger.critical(msg, extra=kwargs)
    
    # Tether-specific logging methods
    
    def log_plan_submission(self, plan_id: str, description: str):
        """Log plan submission"""
        self.info(f"Plan submitted: {plan_id} - {description}")
    
    def log_constraint_check(self, plan_id: str, valid: bool, violations: list):
        """Log constraint validation"""
        if valid:
            self.info(f"Constraint check PASSED: {plan_id}")
        else:
            self.warning(
                f"Constraint check FAILED: {plan_id}",
                violations=violations
            )
    
    def log_simulation(self, plan_id: str, num_paths: int, recommended_path: str):
        """Log scenario simulation"""
        self.info(
            f"Simulation complete: {plan_id}",
            num_paths=num_paths,
            recommended=recommended_path
        )
    
    def log_approval_request(self, decision_id: str, risk_level: str, approver: str):
        """Log approval request"""
        self.info(
            f"Approval requested: {decision_id}",
            risk=risk_level,
            approver=approver
        )
    
    def log_approval_decision(self, decision_id: str, approved: bool, approver: str):
        """Log approval decision"""
        status = "APPROVED" if approved else "DENIED"
        self.info(f"Approval {status}: {decision_id} by {approver}")
    
    def log_tool_execution(self, tool_name: str, success: bool, response_time: float):
        """Log tool execution"""
        status = "SUCCESS" if success else "FAILURE"
        self.debug(
            f"Tool execution {status}: {tool_name}",
            response_time=response_time
        )
    
    def log_tool_degradation(self, tool_name: str, metric: str, value: float):
        """Log tool performance degradation"""
        self.warning(
            f"Tool degradation detected: {tool_name}",
            metric=metric,
            value=value
        )
    
    def log_execution_start(self, plan_id: str):
        """Log execution start"""
        self.info(f"Execution started: {plan_id}")
    
    def log_execution_complete(self, plan_id: str, status: str, duration: float):
        """Log execution completion"""
        self.info(
            f"Execution complete: {plan_id}",
            status=status,
            duration=duration
        )


# Global logger instance
_global_logger: Optional[TetherLogger] = None


def get_logger() -> TetherLogger:
    """Get or create global logger"""
    global _global_logger
    if _global_logger is None:
        _global_logger = TetherLogger()
    return _global_logger


def setup_logger(level: str = "INFO", log_file: Optional[str] = None):
    """Setup global logger with custom configuration"""
    global _global_logger
    _global_logger = TetherLogger(level=level, log_file=log_file)
    return _global_logger
