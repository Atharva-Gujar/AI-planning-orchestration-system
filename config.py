"""
Configuration System for Tether
Handles loading, saving, and validating configurations
"""
import json
import os
from typing import Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass, asdict


@dataclass
class TetherConfig:
    """Main configuration for Tether orchestrator"""
    
    # Constraint defaults
    default_time_limit: int = 3600  # 1 hour
    default_budget: float = 100.0
    default_permissions: list = None
    
    # Simulation settings
    simulation_depth: int = 3
    simulation_paths: int = 3
    
    # Reliability settings
    reliability_threshold: float = 0.85
    performance_threshold: float = 5.0  # seconds
    
    # Approval settings
    approval_cost_threshold: float = 50.0
    approval_time_threshold: int = 7200  # 2 hours
    approval_success_threshold: float = 0.5
    
    # Logging settings
    log_level: str = "INFO"
    log_file: Optional[str] = None
    
    # Persistence settings
    persist_executions: bool = True
    persist_health: bool = True
    execution_history_limit: int = 1000
    
    def __post_init__(self):
        if self.default_permissions is None:
            self.default_permissions = ['read']
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TetherConfig':
        """Create config from dictionary"""
        return cls(**data)
    
    def save(self, filepath: str):
        """Save configuration to JSON file"""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load(cls, filepath: str) -> 'TetherConfig':
        """Load configuration from JSON file"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)
    
    @classmethod
    def load_or_default(cls, filepath: str) -> 'TetherConfig':
        """Load config if exists, otherwise return default"""
        if os.path.exists(filepath):
            return cls.load(filepath)
        return cls()


class ConfigManager:
    """Manages multiple configurations and profiles"""
    
    def __init__(self, config_dir: str = "~/.tether"):
        self.config_dir = Path(config_dir).expanduser()
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.default_config_path = self.config_dir / "config.json"
        self.profiles_dir = self.config_dir / "profiles"
        self.profiles_dir.mkdir(exist_ok=True)
    
    def get_default_config(self) -> TetherConfig:
        """Get or create default configuration"""
        return TetherConfig.load_or_default(str(self.default_config_path))
    
    def save_default_config(self, config: TetherConfig):
        """Save default configuration"""
        config.save(str(self.default_config_path))
    
    def create_profile(self, name: str, config: TetherConfig):
        """Create a named configuration profile"""
        profile_path = self.profiles_dir / f"{name}.json"
        config.save(str(profile_path))
    
    def load_profile(self, name: str) -> TetherConfig:
        """Load a named configuration profile"""
        profile_path = self.profiles_dir / f"{name}.json"
        if not profile_path.exists():
            raise FileNotFoundError(f"Profile '{name}' not found")
        return TetherConfig.load(str(profile_path))
    
    def list_profiles(self) -> list:
        """List all available configuration profiles"""
        return [p.stem for p in self.profiles_dir.glob("*.json")]
    
    def delete_profile(self, name: str):
        """Delete a configuration profile"""
        profile_path = self.profiles_dir / f"{name}.json"
        if profile_path.exists():
            profile_path.unlink()


# Predefined configuration profiles

def create_development_config() -> TetherConfig:
    """Configuration for development/testing"""
    return TetherConfig(
        default_time_limit=7200,  # 2 hours
        default_budget=500.0,
        default_permissions=['read', 'write', 'admin'],
        simulation_depth=5,
        reliability_threshold=0.75,  # More lenient
        approval_cost_threshold=200.0,
        log_level="DEBUG"
    )


def create_production_config() -> TetherConfig:
    """Configuration for production use"""
    return TetherConfig(
        default_time_limit=3600,  # 1 hour
        default_budget=100.0,
        default_permissions=['read'],
        simulation_depth=3,
        reliability_threshold=0.90,  # Stricter
        approval_cost_threshold=25.0,  # Lower threshold
        log_level="WARNING",
        persist_executions=True
    )


def create_research_config() -> TetherConfig:
    """Configuration for research/exploration"""
    return TetherConfig(
        default_time_limit=14400,  # 4 hours
        default_budget=1000.0,
        default_permissions=['read', 'write'],
        simulation_depth=5,
        simulation_paths=5,  # More scenarios
        reliability_threshold=0.80,
        approval_cost_threshold=500.0,
        log_level="INFO"
    )


if __name__ == "__main__":
    # Example usage
    manager = ConfigManager()
    
    # Create and save profiles
    manager.create_profile("development", create_development_config())
    manager.create_profile("production", create_production_config())
    manager.create_profile("research", create_research_config())
    
    print("Created profiles:", manager.list_profiles())
    
    # Load and use a profile
    prod_config = manager.load_profile("production")
    print(f"\nProduction config: {prod_config.to_dict()}")
