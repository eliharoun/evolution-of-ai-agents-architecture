"""
LangGraph workflow orchestration for Stage 1 ReAct agent.
Uses tools_condition for cleaner routing logic.
"""

from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition

from stage_1.agents.state import AgentState
from stage_1.agents.react_agent import ReactAgent
from common.model_factory import ModelType
from common.config import config
from common.logging_config import get_logger
from typing import cast

logger = get_logger(__name__)


class AgentWorkflow:
    """
    LangGraph workflow for the customer support agent.
    
    The workflow follows a simple pattern:
    1. START → Agent (reasoning and tool selection)
    2. Agent → [tools_condition decides] → Tools OR END
    3. Tools → Agent (observation and next action)
    
    This creates the ReAct loop: Thought → Action → Observation
    """
    
    def __init__(self):
        """Initialize the workflow with models from config."""
        # Load model configuration from config
        self.agent = ReactAgent(
            model_type=cast(ModelType, config.DEFAULT_MODEL_TYPE),
            model_name=config.DEFAULT_MODEL_NAME
        )
        self.workflow = None
        
        logger.info(f"Workflow initializing with model={config.DEFAULT_MODEL_TYPE}:{config.DEFAULT_MODEL_NAME}")
        self._build_graph()
    
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
        
        # Compile the graph (no checkpointer for Phase 1 - stateless as requested)
        self.workflow = graph.compile()
        
        logger.info("Workflow built with nodes=['agent', 'tools'], stateless=True")
    
    def get_app(self):
        """
        Get the compiled application.
        
        Returns:
            Compiled LangGraph application
        """
        return self.workflow
    
    def invoke(self, user_input: str) -> dict:
        """
        Invoke the agent with a user message.
        
        Args:
            user_input: User's message/question
            
        Returns:
            Dictionary with final state including messages
        """
        from langchain_core.messages import HumanMessage
        
        logger.info(f"Workflow invoke - input: {user_input[:100]}...")
        
        initial_state = {
            "messages": [HumanMessage(content=user_input)],
            "iterations": 0
        }
        
        try:
            result = self.workflow.invoke(initial_state)
            
            logger.info(f"Workflow complete - iterations: {result.get('iterations', 0)}, messages: {len(result.get('messages', []))}")
            
            return result
            
        except Exception as e:
            logger.error(f"Workflow error: {str(e)}")
            raise
    
    def stream(self, user_input: str):
        """
        Stream the agent's response in real-time.
        
        Args:
            user_input: User's message/question
            
        Yields:
            State updates as they occur from each node
        """
        from langchain_core.messages import HumanMessage
        
        logger.info(f"Workflow stream start - input: {user_input[:100]}...")
        
        initial_state = {
            "messages": [HumanMessage(content=user_input)],
            "iterations": 0
        }
        
        try:
            for chunk in self.workflow.stream(initial_state):
                yield chunk
                
        except Exception as e:
            logger.error(f"Workflow stream error: {str(e)}")
            raise
