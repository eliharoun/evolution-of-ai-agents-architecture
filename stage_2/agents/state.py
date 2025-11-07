"""
State management for the sophisticated customer support agent.
Defines the structure of data flowing through the agent graph.
Same as Stage 1 - demonstrates that complexity comes from tools, not state.
"""

from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """
    The state of our agent represents the data flowing through the graph.
    
    In Stage 2, we keep the same simple state as Stage 1. The complexity
    and struggles come from having 7 tools instead of 2, not from state management.
    The `add_messages` reducer properly handles message accumulation.
    
    Attributes:
        messages: List of messages in the conversation.
                  The add_messages function handles proper message accumulation,
                  including tool calls and tool responses.
        iterations: Counter for ReAct loop iterations to prevent infinite loops.
    """
    messages: Annotated[Sequence[BaseMessage], add_messages]
    iterations: int
