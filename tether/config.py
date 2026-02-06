"""
Configuration management for Tether
"""

import json
import os
from typing import Dict, Any
from pathlib import Path


class Config:
    """Manages Tether configuration"""
    
    DEFAULT_CONFIG = {
        'constraints': {
            'time_limit': 3600,  # 1 hour
            'budget': 100.0,     # $100
            'permissions': ['read', 'write']
        },
        'simulation': {
            'depth': 3,
            'num_paths': 3
        },
        'reliability': {
            'threshold': 0.85,
            'alert_email': None
        },
        'approval': {
            'high_cost_threshold': 50.0,
            'long_duration_threshold': 7200,
            'low_success_threshold': 0.5
        },
        'database': {
            'path': 'tether.db'
        },
        'logging': {
            'level': 'INFO',
            'file': 'tether.log'
        }
    }
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path or os.path.join(os.getcwd(), 'tether_config.json')
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or use defaults"""
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                user_config = json.load(f)
                # Merge with defaults
                config = self.DEFAULT_CONFIG.copy()
                config.update(user_config)
                return config
        return self.DEFAULT_CONFIG.copy()
    
    def save(self):
        """Save current configuration to file"""
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def get(self, key: str, default=None):
        """Get configuration value"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        
        return value if value is not None else default
    
    def set(self, key: str, value: Any):
        """Set configuration value"""
        keys = key.split('.')
        current = self.config
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """Get configuration as dictionary"""
        return self.config.copy()
