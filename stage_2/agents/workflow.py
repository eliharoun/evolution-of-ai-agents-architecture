"""
LangGraph workflow orchestration for Stage 2 sophisticated agent.
Same architecture as Stage 1, but with struggle monitoring and optional checkpointing.
"""

from typing import Optional
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage

from stage_2.agents.state import AgentState
from stage_2.agents.react_agent import ReactAgent
from common.base_workflow import BaseWorkflow
from common.model_factory import ModelType
from common.config import config
from common.logging_config import get_logger
from common.monitoring.struggle_analyzer import StruggleAnalyzer

logger = get_logger(__name__)


class AgentWorkflow(BaseWorkflow):
    """
    LangGraph workflow for the sophisticated customer support agent with optional checkpointing.
    
    Pattern:
    1. START → Agent (reasoning and tool selection from 7 tools)
    2. Agent → [tools_condition decides] → Tools OR END
    3. Tools → Agent (observation and next action)
    
    Features:
    - 7 tools (reveals ReAct limitations)
    - Struggle monitoring
    - Optional checkpointing for conversation memory
    """
    
    def __init__(self, model_type: Optional[ModelType] = None, enable_checkpointing: Optional[bool] = None):
        """
        Initialize the workflow with struggle monitoring and optional checkpointing.
        
        Args:
            model_type: Type of model to use
            enable_checkpointing: Enable state persistence (defaults to config)
        """
        super().__init__(model_type, enable_checkpointing)
        self.agent = ReactAgent(model_type=self.model_type)
        self.struggle_analyzer = StruggleAnalyzer(stage=2, enable_logging=True)
        self.workflow = self._build_graph()
        
        logger.info("Stage 2 workflow will monitor for agent struggles with 7-tool complexity")
    
    def _build_graph(self):
        """
        Build the LangGraph workflow with nodes and edges.
        Same structure as Stage 1 but with struggle monitoring.
        
        Graph structure:
        START → agent → [tools_condition] → tools → agent
                           ↓                          ↑
                          END ←───────────────────────┘
        """
        # Create the state graph
        graph = StateGraph(AgentState)
        
        # Add nodes
        # 1. Agent node: Reasons and decides on actions (ReAct: Thought + Action)
        graph.add_node("agent", self._agent_with_monitoring)
        
        # 2. Tools node: Executes tool calls (ReAct: Observation)  
        graph.add_node("tools", ToolNode(self.agent.tools))
        
        # Add edges
        # Start with the agent node
        graph.add_edge(START, "agent")

        # Use built-in tools_condition for routing
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
        
        # Compile with optional checkpointing
        return self._compile_graph(graph)
    
    def _agent_with_monitoring(self, state: AgentState) -> dict:
        """
        Agent node wrapper that adds struggle monitoring.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with struggle detection
        """
        iterations = state.get("iterations", 0)
        
        # Analyze iteration count for struggles
        self.struggle_analyzer.analyze_iteration(iterations)
        
        # Call the original agent logic
        result = self.agent.call_model(state)
        
        # Post-process to analyze tool calls for struggles
        new_messages = result.get("messages", [])
        if new_messages:
            msg = new_messages[-1]
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                tool_names = [tc["name"] for tc in msg.tool_calls]
                self.struggle_analyzer.analyze_tool_calls(tool_names)
        
        return result
    
    def get_app(self):
        """Get the compiled application."""
        return self.workflow
    
    def get_struggle_stats(self) -> dict:
        """
        Get struggle statistics for analysis.
        
        Returns formatted structure for frontend with booleans + details.
        """
        return self.struggle_analyzer.get_stats()
    
    def reset_struggle_stats(self):
        """Reset struggle statistics."""
        self.struggle_analyzer.reset()
    
    def _invoke_impl(self, user_input: str, config: Optional[RunnableConfig], **kwargs) -> dict:
        """
        Execute Stage 2 workflow with optional checkpointing.
        
        Args:
            user_input: User query/task
            config: Optional config with thread_id (for checkpointing)
            
        Returns:
            Final state with result and struggle stats
        """
        # Reset struggle analyzer for new invocation
        self.struggle_analyzer.reset()
        
        logger.info(f"Stage 2 workflow invoke - input: {user_input[:100]}...")
        
        # Load previous state if checkpointing enabled
        if config and self.enable_checkpointing:
            try:
                previous_state = self.workflow.get_state(config)
                if previous_state and previous_state.values:
                    # Continue conversation with history
                    initial_state = previous_state.values.copy()
                    initial_state["messages"].append(HumanMessage(content=user_input))
                else:
                    # No previous state
                    initial_state = {"messages": [HumanMessage(content=user_input)], "iterations": 0}
            except Exception:
                initial_state = {"messages": [HumanMessage(content=user_input)], "iterations": 0}
        else:
            initial_state = {"messages": [HumanMessage(content=user_input)], "iterations": 0}
        
        try:
            result = self.workflow.invoke(initial_state, config) if config else self.workflow.invoke(initial_state)
            
            # Add struggle statistics to result
            result["struggle_stats"] = self.get_struggle_stats()
            
            logger.info(f"Stage 2 complete - iterations: {result.get('iterations', 0)}, messages: {len(result.get('messages', []))}")
            
            if self.struggle_analyzer.has_struggles():
                logger.warning(f"Stage 2 struggles: {self.struggle_analyzer.get_struggle_summary()}")
            
            return result
        except Exception as e:
            logger.error(f"Stage 2 workflow error: {str(e)}")
            raise
    
    def _stream_impl(self, user_input: str, config: Optional[RunnableConfig], **kwargs):
        """
        Stream Stage 2 workflow with optional checkpointing.
        
        Args:
            user_input: User query/task
            config: Optional config with thread_id (for checkpointing)
            
        Yields:
            State updates as they occur
        """
        # Reset struggle analyzer for new stream
        self.struggle_analyzer.reset()
        
        logger.info(f"Stage 2 workflow stream start - input: {user_input[:100]}...")
        
        # Load previous state if checkpointing enabled  
        if config and self.enable_checkpointing:
            try:
                previous_state = self.workflow.get_state(config)
                if previous_state and previous_state.values:
                    initial_state = previous_state.values.copy()
                    initial_state["messages"].append(HumanMessage(content=user_input))
                else:
                    initial_state = {"messages": [HumanMessage(content=user_input)], "iterations": 0}
            except Exception:
                initial_state = {"messages": [HumanMessage(content=user_input)], "iterations": 0}
        else:
            initial_state = {"messages": [HumanMessage(content=user_input)], "iterations": 0}
        
        try:
            stream_method = self.workflow.stream(initial_state, config) if config else self.workflow.stream(initial_state)
            for chunk in stream_method:
                # Add struggle stats to chunks
                if "agent" in chunk:
                    chunk["struggle_stats"] = self.get_struggle_stats()
                yield chunk
        except Exception as e:
            logger.error(f"Stage 2 workflow stream error: {str(e)}")
            raise
