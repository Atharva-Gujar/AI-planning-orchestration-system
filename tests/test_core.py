"""
Test suite for TetherOrchestrator
"""

import pytest
import tempfile
import os
from tether.core import TetherOrchestrator
from tether.models import Plan
from tether.config import Config
from tether.persistence import Database


class TestTetherOrchestrator:
    """Tests for main TetherOrchestrator"""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database"""
        fd, path = tempfile.mkstemp(suffix='.db')
        yield path
        os.close(fd)
        os.unlink(path)
    
    def test_initialization(self, temp_db):
        """Test orchestrator initialization"""
        config = Config()
        config.set('database.path', temp_db)
        
        orchestrator = TetherOrchestrator(config=config)
        
        assert orchestrator.constraint_agent is not None
        assert orchestrator.simulator is not None
        assert orchestrator.reliability_agent is not None
        assert orchestrator.human_loop_agent is not None
        
        orchestrator.close()
    
    def test_valid_plan_execution(self, temp_db):
        """Test executing a valid plan"""
        config = Config()
        config.set('database.path', temp_db)
        
        orchestrator = TetherOrchestrator(
            constraints={
                'time_limit': 3600,
                'budget': 100.0,
                'permissions': ['read', 'write']
            },
            config=config
        )
        
        plan = Plan(
            id="test_valid",
            description="Valid test plan",
            steps=[{"action": "fetch"}, {"action": "process"}],
            estimated_time=1800,
            estimated_cost=50.0,
            required_permissions=['read']
        )
        
        result = orchestrator.execute_plan(plan)
        
        assert result['status'] in ['approved', 'awaiting_approval']
        assert result['stages']['constraint_validation']['valid'] is True
        assert len(result['stages']['simulation']['paths_explored']) == 3
        
        orchestrator.close()
    
    def test_invalid_plan_rejection(self, temp_db):
        """Test rejecting an invalid plan"""
        config = Config()
        config.set('database.path', temp_db)
        
        orchestrator = TetherOrchestrator(
            constraints={
                'time_limit': 1800,
                'budget': 50.0,
                'permissions': ['read']
            },
            config=config
        )
        
        plan = Plan(
            id="test_invalid",
            description="Invalid test plan",
            steps=[{"action": "fetch"}],
            estimated_time=3600,  # Exceeds limit
            estimated_cost=100.0,  # Exceeds budget
            required_permissions=['read', 'write', 'admin']  # Missing permissions
        )
        
        result = orchestrator.execute_plan(plan)
        
        assert result['status'] == 'rejected'
        assert result['stages']['constraint_validation']['valid'] is False
        assert len(result['stages']['constraint_validation']['violations']) > 0
        assert 'suggestions' in result
        
        orchestrator.close()
    
    def test_system_health(self, temp_db):
        """Test system health reporting"""
        config = Config()
        config.set('database.path', temp_db)
        
        orchestrator = TetherOrchestrator(config=config)
        
        # Register some tools
        orchestrator.reliability_agent.register_tool("test_api")
        orchestrator.reliability_agent.record_execution("test_api", True, 0.5)
        
        health = orchestrator.get_system_health()
        
        assert 'timestamp' in health
        assert 'total_executions' in health
        assert 'unreliable_tools' in health
        assert 'tool_health' in health
        assert 'test_api' in health['tool_health']
        
        orchestrator.close()
