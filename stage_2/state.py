"""
State management for the customer support agent.
Defines the structure of data flowing through the agent graph.
"""

from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """
    The state of our agent represents the data flowing through the graph.
    
    In Phase 1, we keep state simple with just messages and iteration counter.
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
