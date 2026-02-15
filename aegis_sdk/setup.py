"""Kept for backward compatibility — see pyproject.toml for canonical config."""

from setuptools import setup, find_packages

setup(
    name="aegis-sentinel",
    version="0.1.0",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "pymongo>=4.0",
        "dnspython>=2.0",
        "python-dotenv>=1.0",
        "pydantic>=2.0",
    ],
)
