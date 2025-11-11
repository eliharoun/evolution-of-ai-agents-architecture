"""
Common base state definitions for all agent stages.
This provides the foundational state structure used across different agent patterns.
"""

from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class BaseAgentState(TypedDict):
    """
    Base state for all agent patterns.
    
    This represents the minimal state structure shared across all stages.
    The `add_messages` reducer properly handles message accumulation, ensuring
    tool calls and responses are correctly linked.
    
    Attributes:
        messages: List of messages in the conversation.
                  The add_messages function handles proper message accumulation,
                  including tool calls and tool responses.
        iterations: Counter for ReAct loop iterations to prevent infinite loops.
    """
    messages: Annotated[Sequence[BaseMessage], add_messages]
    iterations: int
