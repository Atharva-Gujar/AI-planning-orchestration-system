"""
Setup configuration for Tether
"""
from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text() if readme_file.exists() else ""

setup(
    name="tether-ai",
    version="0.2.0",
    author="Tether Contributors",
    description="AI Planning Orchestration System - The reality layer for AI agents",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/tether",
    packages=find_packages(exclude=["tests", "tests.*"]),
    py_modules=[
        "tether",
        "config",
        "logger",
        "persistence",
        "execution",
        "cli"
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.7",
    install_requires=[
        "dataclasses>=0.6; python_version < '3.7'",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "mypy>=0.950",
            "flake8>=6.0.0",
            "pylint>=2.15.0",
        ],
        "docs": [
            "sphinx>=5.0.0",
            "sphinx-rtd-theme>=1.0.0",
        ],
        "langchain": [
            "langchain>=0.1.0",
        ],
        "anthropic": [
            "anthropic>=0.18.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "tether=cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
