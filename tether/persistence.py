"""
Database and persistence layer for Tether
"""

import json
import sqlite3
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path


class Database:
    """SQLite-based persistence for Tether"""
    
    def __init__(self, db_path: str = "tether.db"):
        self.db_path = db_path
        self.conn = None
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        
        cursor = self.conn.cursor()
        
        # Plans table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS plans (
                id TEXT PRIMARY KEY,
                description TEXT,
                steps TEXT,
                estimated_time INTEGER,
                estimated_cost REAL,
                required_permissions TEXT,
                metadata TEXT,
                created_at TEXT
            )
        """)
        
        # Executions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS executions (
                plan_id TEXT,
                status TEXT,
                started_at TEXT,
                completed_at TEXT,
                actual_time INTEGER,
                actual_cost REAL,
                steps_completed INTEGER,
                steps_total INTEGER,
                error TEXT,
                output TEXT,
                FOREIGN KEY(plan_id) REFERENCES plans(id)
            )
        """)
        
        # Tool health metrics
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tool_health (
                tool_name TEXT,
                success_rate REAL,
                avg_response_time REAL,
                last_failure TEXT,
                failure_count INTEGER,
                drift_detected INTEGER,
                timestamp TEXT
            )
        """)
        
        # Approval history
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS approvals (
                decision_id TEXT PRIMARY KEY,
                plan_id TEXT,
                context TEXT,
                risk_level TEXT,
                recommended_approver TEXT,
                urgency TEXT,
                approved INTEGER,
                approver TEXT,
                created_at TEXT,
                decided_at TEXT
            )
        """)
        
        self.conn.commit()
    
    def save_plan(self, plan: Dict[str, Any]):
        """Save a plan to database"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO plans VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            plan['id'],
            plan['description'],
            json.dumps(plan['steps']),
            plan['estimated_time'],
            plan['estimated_cost'],
            json.dumps(plan['required_permissions']),
            json.dumps(plan.get('metadata', {})),
            plan.get('created_at', datetime.now().isoformat())
        ))
        self.conn.commit()
    
    def save_execution(self, execution: Dict[str, Any]):
        """Save execution result"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO executions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            execution['plan_id'],
            execution['status'],
            execution['started_at'],
            execution.get('completed_at'),
            execution.get('actual_time'),
            execution.get('actual_cost'),
            execution['steps_completed'],
            execution['steps_total'],
            execution.get('error'),
            json.dumps(execution.get('output'))
        ))
        self.conn.commit()
    
    def save_tool_health(self, tool_name: str, health: Dict[str, Any]):
        """Save tool health metrics"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO tool_health VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            tool_name,
            health['success_rate'],
            health['avg_response_time'],
            health.get('last_failure'),
            health['failure_count'],
            1 if health.get('drift_detected') else 0,
            datetime.now().isoformat()
        ))
        self.conn.commit()
    
    def get_plan(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a plan"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM plans WHERE id = ?", (plan_id,))
        row = cursor.fetchone()
        
        if row:
            return {
                'id': row['id'],
                'description': row['description'],
                'steps': json.loads(row['steps']),
                'estimated_time': row['estimated_time'],
                'estimated_cost': row['estimated_cost'],
                'required_permissions': json.loads(row['required_permissions']),
                'metadata': json.loads(row['metadata']),
                'created_at': row['created_at']
            }
        return None
    
    def get_executions(self, plan_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get execution history"""
        cursor = self.conn.cursor()
        
        if plan_id:
            cursor.execute("SELECT * FROM executions WHERE plan_id = ?", (plan_id,))
        else:
            cursor.execute("SELECT * FROM executions ORDER BY started_at DESC")
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
