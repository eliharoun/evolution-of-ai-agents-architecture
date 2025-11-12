"""
State management for Stage 3 agents.
"""
from typing import List
from common.base_state import BaseAgentState


class ReWOOState(BaseAgentState):
    """
    State for ReWOO agent workflow.
    """
    task: str  # Original user query
    plan_string: str  # Full plan as string
    steps: List  # List of (plan, step_name, tool, tool_input) tuples
    results: dict  # Tool execution results {step_name: result}
    result: str  # Final answer
