"""
ReWOO Workflow Implementation.
Workflow Structure:
START → plan → tool → (loop back to tool OR → solve) → END
"""
from typing import Optional, cast
from langgraph.graph import StateGraph, START, END
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage

from stage_3.agents.rewoo.state import ReWOOState
from stage_3.agents.rewoo.rewoo_agent import ReWOOAgent
from common.base_workflow import BaseWorkflow
from common.config import config
from common.model_factory import ModelType


class ReWOOWorkflow(BaseWorkflow):
    """
    LangGraph workflow for ReWOO pattern.
    
    Graph structure:
    - plan: Creates complete plan with placeholders
    - tool: Executes tools with variable substitution (loops until all done)
    - solve: Integrates evidence into final answer
    """
    
    def __init__(self):
        """Initialize ReWOO workflow with models from config."""
        super().__init__()
        # Load model configurations from config
        self.agent = ReWOOAgent(
            planner_model_type=cast(ModelType, config.PLANNER_MODEL_TYPE),
            planner_model_name=config.PLANNER_MODEL_NAME,
            solver_model_type=cast(ModelType, config.SOLVER_MODEL_TYPE),
            solver_model_name=config.SOLVER_MODEL_NAME
        )
        self.workflow = self._build_graph()
    
    def _build_graph(self):
        """
        Build the LangGraph workflow.
        
        Graph structure:
        START → plan → tool → [conditional: tool OR solve] → END
        """
        # Create state graph
        graph = StateGraph(ReWOOState)
        
        # Add nodes
        graph.add_node("plan", self.agent.get_plan) # Planner: sees what tools are available and plans which to use
        graph.add_node("tool", self.agent.tool_execution)
        graph.add_node("solve", self.agent.solve)
        
        # Add edges
        graph.add_edge(START, "plan")
        graph.add_edge("plan", "tool")
        graph.add_edge("solve", END)
        
        # Add conditional edge: tool loops back to itself OR goes to solve
        graph.add_conditional_edges(
            "tool",
            self._route,
            {
                "tool": "tool",  # Loop back for more tools
                "solve": "solve"  # All tools executed, go to solver
            }
        )
        
        # Compile base class method
        return self._compile_graph(graph)
    
    def _route(self, state: ReWOOState) -> str:
        """
        Routing function for conditional edge.
        
        Determines if we need to execute more tools or move to solver.
        
        Args:
            state: Current ReWOO state
            
        Returns:
            "tool" if more steps to execute, "solve" if all done
        """
        _step = self.agent._get_current_task(state)
        if _step is None:
            # All tasks executed already, move to solver
            return "solve"
        else:
            # More tasks to execute, loop back to tool node
            return "tool"
    
    def _create_initial_state(self, user_input: str) -> dict:
        """
        Create initial state for ReWOO workflow.
        
        Args:
            user_input: User query/task
            
        Returns:
            Initial state dictionary
        """
        return {
            "task": user_input,
            "messages": [HumanMessage(content=user_input)],
            "iterations": 0,
            "results": {}
        }
    
    def _invoke_impl(self, user_input: str, **kwargs) -> dict:
        """
        Execute ReWOO workflow implementation.
        
        Args:
            user_input: User query/task
            
        Returns:
            Final state with result
        """
        # Invoke with initial state using user input
        initial_state = self._create_initial_state(user_input)
        return self.workflow.invoke(initial_state)
    
    def _stream_impl(self, user_input: str, config: Optional[RunnableConfig], **kwargs):
        """
        Stream ReWOO workflow execution implementation.
        
        Args:
            user_input: User query/task
            config: Optional config with thread_id (for checkpointing)
            
        Yields:
            State updates as they occur
        """
       
        # Stream with initial state using user input
        initial_state = self._create_initial_state(user_input)
        for chunk in self.workflow.stream(initial_state):
            yield chunk
