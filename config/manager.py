"""
Configuration management for Tether
Handles loading/saving system configurations
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import asdict


class ConfigManager:
    """Manages Tether configuration persistence"""
    
    DEFAULT_CONFIG_PATH = Path.home() / ".tether" / "config.json"
    
    DEFAULT_CONFIG = {
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
            "alert_enabled": True
        },
        "approval": {
            "auto_approve_low_risk": True,
            "timeout_seconds": 1800
        },
        "logging": {
            "enabled": True,
            "level": "INFO",
            "file_path": None
        }
    }
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load config from {self.config_path}: {e}")
                return self.DEFAULT_CONFIG.copy()
        else:
            return self.DEFAULT_CONFIG.copy()
    
    def save_config(self) -> bool:
        """Save current configuration to file"""
        try:
            # Ensure directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving config to {self.config_path}: {e}")
            return False
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation
        Example: config.get('constraints.time_limit')
        """
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, key_path: str, value: Any, save: bool = True) -> bool:
        """
        Set configuration value using dot notation
        Example: config.set('constraints.budget', 200.0)
        """
        keys = key_path.split('.')
        target = self.config
        
        # Navigate to the parent of the target key
        for key in keys[:-1]:
            if key not in target:
                target[key] = {}
            target = target[key]
        
        # Set the value
        target[keys[-1]] = value
        
        if save:
            return self.save_config()
        return True
    
    def reset_to_default(self) -> bool:
        """Reset configuration to default values"""
        self.config = self.DEFAULT_CONFIG.copy()
        return self.save_config()
    
    def export_config(self, path: Path) -> bool:
        """Export configuration to a specific file"""
        try:
            with open(path, 'w') as f:
                json.dump(self.config, f, indent=2)
            return True
        except Exception as e:
            print(f"Error exporting config to {path}: {e}")
            return False
    
    def import_config(self, path: Path) -> bool:
        """Import configuration from a file"""
        try:
            with open(path, 'r') as f:
                self.config = json.load(f)
            return True
        except Exception as e:
            print(f"Error importing config from {path}: {e}")
            return False
