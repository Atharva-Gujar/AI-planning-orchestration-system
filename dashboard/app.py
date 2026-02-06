"""
Simple Flask backend for Tether Dashboard
Provides REST API for dashboard data
"""

from flask import Flask, jsonify, render_template, send_from_directory
from flask_cors import CORS
import os
import sys

# Add parent directory to path to import tether
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from tether import TetherOrchestrator
from config import TetherConfig

app = Flask(__name__, 
            static_folder='.',
            template_folder='.')
CORS(app)

# Global orchestrator instance
config = TetherConfig()
cfg = config.load_config()

if cfg:
    orchestrator = TetherOrchestrator(
        constraints=cfg.get('constraints', {}),
        simulation_depth=cfg.get('simulation_depth', 3),
        reliability_threshold=cfg.get('reliability_threshold', 0.85)
    )
else:
    # Use defaults if no config
    orchestrator = TetherOrchestrator(
        constraints={'budget': 100, 'time_limit': 3600},
        simulation_depth=3,
