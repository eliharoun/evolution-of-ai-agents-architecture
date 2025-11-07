"""
LangGraph workflow orchestration for Stage 2 sophisticated agent.
Same architecture as Stage 1, but with struggle monitoring for 7-tool complexity.
"""

from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition

from stage_2.agents.state import AgentState
from stage_2.agents.react_agent import ReactAgent
from common.model_factory import ModelType
from common.config import config
from common.logging_config import get_logger
from common.monitoring.struggle_analyzer import StruggleAnalyzer

logger = get_logger(__name__)


class AgentWorkflow:
    """
    LangGraph workflow for the sophisticated customer support agent.
    
    Same pattern as Stage 1:
    1. START → Agent (reasoning and tool selection from 7 tools)
    2. Agent → [tools_condition decides] → Tools OR END
    3. Tools → Agent (observation and next action)
    
    The difference: With 7 tools available, the agent will struggle with:
    - Tool selection confusion
    - Sequential processing bottlenecks
    - Context loss across multiple iterations
    """
    
    def __init__(self, model_type: ModelType = None):
        """
        Initialize the workflow with struggle monitoring.
        
        Args:
            model_type: Type of model to use ("openai", "anthropic", or "ollama")
                       If None, uses MODEL_TYPE from config
        """
        # Use config MODEL_TYPE if not explicitly provided
        self.model_type = model_type or config.MODEL_TYPE
        self.agent = ReactAgent(model_type=self.model_type)
        self.workflow = None
        
        # Initialize struggle analyzer (standalone tool)
        self.struggle_analyzer = StruggleAnalyzer(stage=2, enable_logging=True)
        
        logger.info(f"Stage 2 workflow initializing with model_type={self.model_type}, from_config={model_type is None}")
        logger.info("Stage 2 workflow will monitor for agent struggles with 7-tool complexity")
        self._build_graph()
    
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
        
        # Compile the graph (stateless like Stage 1)
        self.workflow = graph.compile()
        
        logger.info("Stage 2 workflow built with struggle monitoring enabled")
    
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
    
    def invoke(self, user_input: str) -> dict:
        """
        Invoke the agent with a user message.
        
        Args:
            user_input: User's message/question
            
        Returns:
            Dictionary with final state including messages and struggle stats
        """
        from langchain_core.messages import HumanMessage
        
        # Reset struggle analyzer for new invocation
        self.struggle_analyzer.reset()
        
        logger.info(f"Stage 2 workflow invoke - input: {user_input[:100]}...")
        
        initial_state = {
            "messages": [HumanMessage(content=user_input)],
            "iterations": 0
        }
        
        try:
            result = self.workflow.invoke(initial_state)
            
            # Add struggle statistics to result
            result["struggle_stats"] = self.get_struggle_stats()
            
            logger.info(f"Stage 2 workflow complete - iterations: {result.get('iterations', 0)}, messages: {len(result.get('messages', []))}")
            
            # Log struggle summary if any detected
            if self.struggle_analyzer.has_struggles():
                summary = self.struggle_analyzer.get_struggle_summary()
                logger.warning(f"Stage 2 struggles detected: {summary}")
            
            return result
            
        except Exception as e:
            logger.error(f"Stage 2 workflow error: {str(e)}")
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
        
        # Reset struggle analyzer for new stream
        self.struggle_analyzer.reset()
        
        logger.info(f"Stage 2 workflow stream start - input: {user_input[:100]}...")
        
        initial_state = {
            "messages": [HumanMessage(content=user_input)],
            "iterations": 0
        }
        
        try:
            for chunk in self.workflow.stream(initial_state):
                # Add struggle stats to chunks for frontend display
                if "agent" in chunk:
                    chunk["struggle_stats"] = self.get_struggle_stats()
                yield chunk
                
        except Exception as e:
            logger.error(f"Stage 2 workflow stream error: {str(e)}")
            raise
