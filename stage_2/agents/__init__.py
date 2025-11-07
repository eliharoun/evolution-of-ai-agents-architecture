"""
Agents package for Stage 2: Sophisticated Single Agent.
Contains the same ReAct agent as Stage 1, but with 7 tools instead of 2.
"""

from stage_2.agents.state import AgentState
from stage_2.agents.react_agent import ReactAgent
from stage_2.agents.workflow import AgentWorkflow

__all__ = [
    "AgentState",
    "ReactAgent", 
    "AgentWorkflow"
]
