"""Kept for backward compatibility — see pyproject.toml for canonical config."""

from setuptools import setup, find_packages

setup(
    name="aegis-secure",
    version="2.0.0",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "httpx>=0.27",
        "python-dotenv>=1.0",
    ],
)
