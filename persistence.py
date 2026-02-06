"""
Persistence layer for Tether
Stores execution history and system health data
"""
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from contextlib import contextmanager


class TetherDatabase:
    """SQLite-based persistence for Tether"""
    
    def __init__(self, db_path: str = "~/.tether/tether.db"):
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Initialize database schema"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Execution history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS executions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plan_id TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    status TEXT NOT NULL,
                    description TEXT,
                    estimated_time INTEGER,
                    estimated_cost REAL,
                    actual_time INTEGER,
                    actual_cost REAL,
                    success_probability REAL,
                    risk_level TEXT,
                    approved BOOLEAN,
                    approver TEXT,
                    result_data TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tool health history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tool_health (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tool_name TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    success_rate REAL NOT NULL,
                    avg_response_time REAL NOT NULL,
                    failure_count INTEGER NOT NULL,
                    drift_detected BOOLEAN NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Constraint violations table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS constraint_violations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plan_id TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    violation_type TEXT NOT NULL,
                    violation_message TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Approval decisions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS approval_decisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    decision_id TEXT NOT NULL UNIQUE,
                    plan_id TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    approved BOOLEAN NOT NULL,
                    approver TEXT NOT NULL,
                    risk_level TEXT NOT NULL,
                    urgency TEXT NOT NULL,
                    context_data TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_plan_id ON executions(plan_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tool_name ON tool_health(tool_name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON executions(timestamp)')
            
            conn.commit()
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def save_execution(self, execution_data: Dict[str, Any]):
        """Save an execution record"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO executions (
                    plan_id, timestamp, status, description,
                    estimated_time, estimated_cost, success_probability,
                    risk_level, approved, approver, result_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                execution_data['plan_id'],
                execution_data['timestamp'],
                execution_data['status'],
                execution_data.get('description'),
                execution_data.get('estimated_time'),
                execution_data.get('estimated_cost'),
                execution_data.get('success_probability'),
                execution_data.get('risk_level'),
                execution_data.get('approved'),
                execution_data.get('approver'),
                json.dumps(execution_data)
            ))
            
            conn.commit()
            return cursor.lastrowid
    
    def get_executions(
        self,
        limit: int = 100,
        plan_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve execution records"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            query = 'SELECT * FROM executions WHERE 1=1'
            params = []
            
            if plan_id:
                query += ' AND plan_id = ?'
                params.append(plan_id)
            
            if status:
                query += ' AND status = ?'
                params.append(status)
            
            query += ' ORDER BY timestamp DESC LIMIT ?'
            params.append(limit)
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def save_tool_health(self, tool_name: str, health_data: Dict[str, Any]):
        """Save tool health snapshot"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO tool_health (
                    tool_name, timestamp, success_rate,
                    avg_response_time, failure_count, drift_detected
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                tool_name,
                datetime.now(),
                health_data['success_rate'],
                health_data['avg_response_time'],
                health_data['failure_count'],
                health_data['drift_detected']
            ))
            
            conn.commit()
    
    def get_tool_health_history(
        self,
        tool_name: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get historical health data for a tool"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM tool_health
                WHERE tool_name = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (tool_name, limit))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def save_constraint_violation(
        self,
        plan_id: str,
        violation_type: str,
        message: str
    ):
        """Save a constraint violation"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO constraint_violations (
                    plan_id, timestamp, violation_type, violation_message
                ) VALUES (?, ?, ?, ?)
            ''', (plan_id, datetime.now(), violation_type, message))
            
            conn.commit()
    
    def save_approval_decision(self, decision_data: Dict[str, Any]):
        """Save an approval decision"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO approval_decisions (
                    decision_id, plan_id, timestamp, approved,
                    approver, risk_level, urgency, context_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                decision_data['decision_id'],
                decision_data['plan_id'],
                decision_data['timestamp'],
                decision_data['approved'],
                decision_data['approver'],
                decision_data['risk_level'],
                decision_data['urgency'],
                json.dumps(decision_data.get('context', {}))
            ))
            
            conn.commit()
    
    def get_approval_decisions(
        self,
        limit: int = 100,
        approved: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """Get approval decision history"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            query = 'SELECT * FROM approval_decisions WHERE 1=1'
            params = []
            
            if approved is not None:
                query += ' AND approved = ?'
                params.append(approved)
            
            query += ' ORDER BY timestamp DESC LIMIT ?'
            params.append(limit)
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get overall statistics"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Total executions
            cursor.execute('SELECT COUNT(*) as count FROM executions')
            total_executions = cursor.fetchone()['count']
            
            # Executions by status
            cursor.execute('''
                SELECT status, COUNT(*) as count
                FROM executions
                GROUP BY status
            ''')
            status_counts = {row['status']: row['count'] for row in cursor.fetchall()}
            
            # Approval rate
            cursor.execute('''
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN approved = 1 THEN 1 ELSE 0 END) as approved_count
                FROM approval_decisions
            ''')
            approval_stats = cursor.fetchone()
            approval_rate = (
                approval_stats['approved_count'] / approval_stats['total']
                if approval_stats['total'] > 0 else 0
            )
            
            # Most common violations
            cursor.execute('''
                SELECT violation_type, COUNT(*) as count
                FROM constraint_violations
                GROUP BY violation_type
                ORDER BY count DESC
                LIMIT 5
            ''')
            common_violations = [
                {row['violation_type']: row['count']}
                for row in cursor.fetchall()
            ]
            
            return {
                'total_executions': total_executions,
                'status_counts': status_counts,
                'approval_rate': approval_rate,
                'common_violations': common_violations
            }
    
    def cleanup_old_records(self, days: int = 30):
        """Delete records older than specified days"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cutoff = datetime.now().timestamp() - (days * 24 * 3600)
            
            cursor.execute(
                'DELETE FROM executions WHERE timestamp < ?',
                (cutoff,)
            )
            cursor.execute(
                'DELETE FROM tool_health WHERE timestamp < ?',
                (cutoff,)
            )
            cursor.execute(
                'DELETE FROM constraint_violations WHERE timestamp < ?',
                (cutoff,)
            )
            cursor.execute(
                'DELETE FROM approval_decisions WHERE timestamp < ?',
                (cutoff,)
            )
            
            conn.commit()
