"""Setup script for sentinel-guardrails."""

from setuptools import setup, find_packages

setup(
    name="sentinel-guardrails",
    version="0.1.0",
    description=(
        "Define, document, and enforce agentic AI policies using Python decorators "
        "with SQLite persistence and audit logging."
    ),
    author="Sentinel Team",
    packages=find_packages(),
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "sentinel=sentinel.cli:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
