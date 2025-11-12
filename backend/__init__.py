"""
Shared backend package for all stages.
Configurable FastAPI backend that works with any stage's workflow.
"""

from backend.api import app

__all__ = ["app"]
