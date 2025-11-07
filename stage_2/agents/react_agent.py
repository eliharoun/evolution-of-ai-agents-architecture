"""
ReAct (Reason and Act) Agent implementation for Stage 2.
Same pattern as Stage 1, but with 7 tools instead of 2.
Demonstrates how tool complexity leads to agent struggles.
"""

from typing import Optional
from langchain_core.messages import SystemMessage, AIMessage

from stage_2.agents.state import AgentState
from common.tools import STAGE_2_TOOLS
from stage_2.prompts import SYSTEM_PROMPT
from common.model_factory import ModelFactory, ModelType
from common.config import config
from common.logging_config import get_logger

logger = get_logger(__name__)


class ReactAgent:
    """
    Sophisticated ReAct agent for customer support with multiple tools.
    
    Same ReAct pattern as Stage 1:
    1. Thought: Reason about what needs to be done
    2. Action: Select from 7 available tools or respond directly
    3. Observation: Process tool results and respond
    
    The complexity comes from having 7 tools instead of 2, leading to:
    - Tool selection confusion
    - Sequential bottlenecks
    - Context management challenges
    """
    
    def __init__(
        self,
        model_type: ModelType = "openai",
        model_name: Optional[str] = None,
        temperature: float = 0
    ):
        """
        Initialize the sophisticated ReAct agent.
        
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
        
        logger.info(f"Stage 2 agent initialized - model_type={model_type}, model_name={model_name}")
        
        # Define available tools (7 tools - up from 2 in Stage 1)
        self.tools = STAGE_2_TOOLS
        
        # Bind tools to model
        self.model_with_tools = self.model.bind_tools(self.tools)
        
        # Use system prompt designed for multiple tools
        self.system_prompt = SYSTEM_PROMPT

        logger.info(f"Stage 2 ReactAgent ready with {len(self.tools)} tools (vs 2 in Stage 1)")
    
    def call_model(self, state: AgentState) -> dict:
        """
        Call the LLM with current state (Thought + Action step in ReAct).
        
        This is the main agent node in the LangGraph workflow.
        With 7 tools available, the model must choose between many options,
        leading to potential confusion and suboptimal choices.
        
        Args:
            state: Current agent state with messages
            
        Returns:
            Dictionary with updated messages and iteration count
        """
        messages = state["messages"]
        iterations = state.get("iterations", 0)
        
        # Add struggle detection logging
        if iterations > 3:
            logger.warning(f"Stage 2 agent struggling - iteration {iterations + 1}, high iteration count suggests confusion")
        
        logger.info(f"Stage 2 agent reasoning - iteration {iterations + 1}, messages: {len(messages)}, tools available: {len(self.tools)}")
        
        # Prepend system prompt if not already present
        if not any(isinstance(m, SystemMessage) for m in messages):
            messages = [SystemMessage(content=self.system_prompt)] + list(messages)
        
        try:
            # Call the model (Thought + Action)
            response = self.model_with_tools.invoke(messages)
            
            # Log the agent's action with struggle detection
            if hasattr(response, "tool_calls") and response.tool_calls:
                tool_names = [tc["name"] for tc in response.tool_calls]
                
                # Detect potential struggles
                if len(tool_names) > 2:
                    logger.warning(f"Stage 2 agent using many tools simultaneously: {tool_names} - potential parallel processing struggle")
                
                # Check for certain tool combinations that indicate confusion
                if "process_refund" in tool_names and "modify_shipping" in tool_names:
                    logger.warning("Stage 2 agent shows tool selection confusion: trying both refund AND shipping modification")
                
                logger.info(f"Stage 2 agent action: using tools {tool_names} - iteration {iterations + 1}")
            else:
                logger.info(f"Stage 2 agent action: final response - iteration {iterations + 1}, length: {len(response.content) if response.content else 0}")
            
            return {
                "messages": [response],
                "iterations": iterations + 1
            }
            
        except Exception as e:
            logger.error(f"Stage 2 agent model error at iteration {iterations + 1}: {str(e)}")
            # Return graceful error message
            error_msg = AIMessage(
                content="I apologize, but I encountered an error processing your complex request. Let me create a support ticket for specialized assistance."
            )
            return {
                "messages": [error_msg],
                "iterations": iterations + 1
            }
