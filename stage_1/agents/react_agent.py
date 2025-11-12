"""
ReAct (Reason and Act) Agent implementation for customer support.
Implements the Thought → Action → Observation loop.
"""

from typing import Optional
from langchain_core.messages import SystemMessage, AIMessage

from stage_1.agents.state import AgentState
from common.tools import get_order_status, search_faq
from stage_1.prompts import SYSTEM_PROMPT
from common.model_factory import ModelFactory, ModelType
from common.config import config
from common.logging_config import get_logger

logger = get_logger(__name__)


class ReactAgent:
    """
    Simple ReAct agent for customer support.
    
    The agent follows the ReAct pattern:
    1. Thought: Reason about what needs to be done
    2. Action: Select and use appropriate tools
    3. Observation: Process tool results and respond
    """
    
    def __init__(
        self,
        model_type: ModelType,
        model_name: str,
        temperature: float = 0
    ):
        """
        Initialize the ReAct agent.
        
        Args:
            model_type: Type of model to use ("openai", "anthropic", or "ollama")
            model_name: Specific model name (uses config default if None)
            temperature: Temperature for model generation
        """
        self.model_type = model_type
        self.temperature = temperature
        
        # Use ModelFactory to create the appropriate model
        self.model = ModelFactory.create_model(
            model_type=model_type,
            model_name=model_name,
            temperature=temperature
        )
        
        logger.info(f"Agent initialized - model_type={model_type}, model_name={model_name}")
        
        # Define available tools
        self.tools = [get_order_status, search_faq]
        
        # Bind tools to model
        self.model_with_tools = self.model.bind_tools(self.tools)
        
        # Use system prompt constant
        self.system_prompt = SYSTEM_PROMPT

        logger.info(f"ReactAgent ready with {len(self.tools)} tools")
    
    def call_model(self, state: AgentState) -> dict:
        """
        Call the LLM with current state (Thought + Action step in ReAct).
        
        This is the main agent node in the LangGraph workflow.
        The model reasons about the current state and decides what action to take.
        
        Args:
            state: Current agent state with messages
            
        Returns:
            Dictionary with updated messages and iteration count
        """
        messages = state["messages"]
        iterations = state.get("iterations", 0)
        
        logger.info(f"Agent reasoning - iteration {iterations + 1}, messages: {len(messages)}")
        
        # Prepend system prompt if not already present
        if not any(isinstance(m, SystemMessage) for m in messages):
            messages = [SystemMessage(content=self.system_prompt)] + list(messages)
        
        try:
            # Call the model (Thought + Action)
            response = self.model_with_tools.invoke(messages)
            
            # Log the agent's action
            if hasattr(response, "tool_calls") and response.tool_calls:
                tool_names = [tc["name"] for tc in response.tool_calls]
                logger.info(f"Agent action: using tools {tool_names} - iteration {iterations + 1}")
            else:
                logger.info(f"Agent action: final response - iteration {iterations + 1}, length: {len(response.content) if response.content else 0}")
            
            return {
                "messages": [response],
                "iterations": iterations + 1
            }
            
        except Exception as e:
            logger.error(f"Agent model error at iteration {iterations + 1}: {str(e)}")
            # Return graceful error message
            error_msg = AIMessage(
                content="I apologize, but I encountered an error processing your request. Please try again or rephrase your question."
            )
            return {
                "messages": [error_msg],
                "iterations": iterations + 1
            }
