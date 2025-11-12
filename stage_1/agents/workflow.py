"""
LangGraph workflow orchestration for Stage 1 ReAct agent.
Uses tools_condition for cleaner routing logic and extends BaseWorkflow.
"""

from typing import Optional
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage

from stage_1.agents.state import AgentState
from stage_1.agents.react_agent import ReactAgent
from common.base_workflow import BaseWorkflow
from common.model_factory import ModelType
from common.config import config
from common.logging_config import get_logger
from typing import cast

logger = get_logger(__name__)


class AgentWorkflow(BaseWorkflow):
    """
    LangGraph workflow for the customer support agent.
    
    The workflow follows a simple pattern:
    1. START → Agent (reasoning and tool selection)
    2. Agent → [tools_condition decides] → Tools OR END
    3. Tools → Agent (observation and next action)
    
    This creates the ReAct loop: Thought → Action → Observation
    """
    
    def __init__(self, enable_checkpointing: Optional[bool] = None):
        """Initialize the workflow with models from config. Stage 1 is always stateless."""
        # Force checkpointing to be disabled for Stage 1 (stateless by design)
        super().__init__(False)
        
        # Load model configuration from config
        self.agent = ReactAgent(
            model_type=cast(ModelType, config.DEFAULT_MODEL_TYPE),
            model_name=config.DEFAULT_MODEL_NAME
        )
        
        logger.info(f"Workflow initializing with model={config.DEFAULT_MODEL_TYPE}:{config.DEFAULT_MODEL_NAME}")
        self.workflow = self._build_graph()
    
    def _build_graph(self):
        """
        Build the LangGraph workflow with nodes and edges.
        
        Graph structure:
        START → agent → [tools_condition] → tools → agent
                           ↓                          ↑
                          END ←───────────────────────┘
        """
        # Create the state graph
        graph = StateGraph(AgentState)
        
        # Add nodes
        # 1. Agent node: Reasons and decides on actions (ReAct: Thought + Action)
        graph.add_node("agent", self.agent.call_model)
        
        # 2. Tools node: Executes tool calls (ReAct: Observation)
        #    ToolNode automatically handles tool execution and formats results
        graph.add_node("tools", ToolNode(self.agent.tools))
        
        # Add edges
        # Start with the agent node
        graph.add_edge(START, "agent")

        # Use built-in tools_condition for routing
        # If agent returned tool_calls, go to tools node
        # Otherwise, end the workflow
        graph.add_conditional_edges(
            "agent",
            tools_condition,  # Built-in function that checks for tool_calls
            {
                "tools": "tools",  # If tool calls exist, go to tools
                END: END           # If no tool calls, end
            }
        )
        
        # After tools execute, always return to agent for observation
        graph.add_edge("tools", "agent")
        
        # Compile with optional checkpointing using BaseWorkflow's helper
        compiled_graph = self._compile_graph(graph)
        
        logger.info(f"Workflow built with nodes=['agent', 'tools'], checkpointing={'enabled' if self.enable_checkpointing else 'disabled'}")
        return compiled_graph
    
    def _invoke_impl(self, user_input: str, config: Optional[RunnableConfig], **kwargs) -> dict:
        """
        Execute Stage 1 workflow (always stateless - no checkpointing).
        
        Args:
            user_input: User query/task
            config: Optional config (ignored - Stage 1 is stateless)
            
        Returns:
            Final state with result
        """
        logger.info(f"Stage 1 workflow invoke - input: {user_input[:100]}...")
        
        # Stage 1 is always stateless - start fresh each time
        initial_state = {
            "messages": [HumanMessage(content=user_input)],
            "iterations": 0
        }
        
        try:
            # Always invoke without config (stateless)
            result = self.workflow.invoke(initial_state)
            
            logger.info(f"Stage 1 complete - iterations: {result.get('iterations', 0)}, messages: {len(result.get('messages', []))}")
            
            return result
            
        except Exception as e:
            logger.error(f"Stage 1 workflow error: {str(e)}")
            raise
    
    def _stream_impl(self, user_input: str, config: Optional[RunnableConfig], **kwargs):
        """
        Stream Stage 1 workflow (always stateless - no checkpointing).
        
        Args:
            user_input: User query/task
            config: Optional config (ignored - Stage 1 is stateless)
            
        Yields:
            State updates as they occur
        """
        logger.info(f"Stage 1 workflow stream start - input: {user_input[:100]}...")
        
        # Stage 1 is always stateless - start fresh each time
        initial_state = {
            "messages": [HumanMessage(content=user_input)],
            "iterations": 0
        }
        
        try:
            # Always stream without config (stateless)
            for chunk in self.workflow.stream(initial_state):
                yield chunk
        except Exception as e:
            logger.error(f"Stage 1 workflow stream error: {str(e)}")
            raise
