"""
State management for the customer support agent.
Defines the structure of data flowing through the agent graph.
"""

from common.base_state import BaseAgentState


class AgentState(BaseAgentState):
    """
    The state of our agent represents the data flowing through the graph.
    
    In Stage 1, we keep state simple with just messages and iteration counter.
    Inherits the base state structure from common.base_state.
    The `add_messages` reducer properly handles message accumulation, ensuring
    tool calls and responses are correctly linked.
    
    Attributes:
        messages: List of messages in the conversation.
                  The add_messages function handles proper message accumulation,
                  including tool calls and tool responses.
        iterations: Counter for ReAct loop iterations to prevent infinite loops.
    """
    pass
