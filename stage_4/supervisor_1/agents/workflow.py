"""
LangGraph workflow orchestration for Stage 4 Supervisor v1 implementation.

Uses LangGraph's built-in create_supervisor() to coordinate specialist agents.
"""

from typing import Optional
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph_supervisor import create_supervisor

from stage_4.common.specialist_agents import create_all_specialists
from stage_4.common import SUPERVISOR_PROMPT
from common.base_workflow import BaseWorkflow
from common.model_factory import ModelFactory, ModelType
from common.config import config
from common.logging_config import setup_logging, get_logger
from typing import cast

# Setup logging
setup_logging(log_level=config.LOG_LEVEL)
logger = get_logger(__name__)


class SupervisorWorkflow(BaseWorkflow):
    """
    LangGraph workflow for the Supervisor pattern with specialist agents.
    
    Pattern:
    1. Customer query → Supervisor
    2. Supervisor delegates → Specialist(s) 
    3. Specialist(s) execute tools → Return results
    4. Supervisor aggregates → Final response
    
    Features:
    - 3 specialist agents with focused tools
    - Intelligent delegation by supervisor
    - Parallel execution for independent tasks
    - Optional checkpointing for conversation memory
    """
    
    def __init__(
        self,
        model_type: Optional[ModelType] = None,
        enable_checkpointing: Optional[bool] = None
    ):
        """
        Initialize the supervisor workflow.
        
        Args:
            model_type: Model type to use (defaults to config)
            enable_checkpointing: Enable state persistence (defaults to config)
        """
        super().__init__(enable_checkpointing)
        
        # Initialize model
        self.model = ModelFactory.create_model(
            model_type=cast(ModelType, config.DEFAULT_MODEL_TYPE),
            model_name=config.DEFAULT_MODEL_NAME
        )
        
        # Create specialist agents with checkpointer from base class
        logger.info("Creating specialist agents...")
        self.specialists = create_all_specialists(self.model, self.checkpointer)
        logger.info(f"Created {len(self.specialists)} specialist agents")
        
        # Build the supervisor graph
        self.workflow = self._build_graph()
        
        logger.info("Stage 4 Supervisor workflow initialized with parallel delegation support")
    
    def _build_graph(self):
        """
        Build the supervisor graph using LangGraph's create_supervisor.
        
        The supervisor coordinates specialist agents, treating them as tools
        to be invoked when their expertise is needed.
        
        Returns:
            Compiled supervisor graph
        """
        logger.info("Building supervisor graph with LangGraph's create_supervisor...")
        
        # Get specialist agents as a list
        specialist_agents = list(self.specialists.values())
        
        # Create supervisor using built-in function with proper configuration
        supervisor_graph = create_supervisor(
            agents=specialist_agents,
            model=self.model,
            prompt=SUPERVISOR_PROMPT,
            parallel_tool_calls=True,  # Enable parallel delegation for read operations
            output_mode="last_message",  # Only return last message to avoid long histories
            add_handoff_messages=True,  # Add handoff tracking messages
            add_handoff_back_messages=True,  # Add messages when returning to supervisor
            include_agent_name="inline",  # Help supervisor distinguish agent responses
        )
        
        # Compile the supervisor graph
        compiled = supervisor_graph.compile(checkpointer=self.checkpointer)
        
        logger.info("Supervisor graph compiled successfully")
        return compiled
    
    def get_app(self):
        """Get the compiled application."""
        return self.workflow
    
    def _invoke_impl(self, user_input: str, config: Optional[RunnableConfig], **kwargs) -> dict:
        """
        Execute Stage 4 Supervisor workflow with optional checkpointing.
        
        Args:
            user_input: User query/task
            config: Optional config with thread_id (for checkpointing)
            
        Returns:
            Final state with aggregated specialist responses
        """
        logger.info(f"Stage 4 Supervisor invoke - input: {user_input[:100]}...")
        
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
                    initial_state = {"messages": [HumanMessage(content=user_input)]}
            except Exception:
                initial_state = {"messages": [HumanMessage(content=user_input)]}
        else:
            initial_state = {"messages": [HumanMessage(content=user_input)]}
        
        try:
            result = self.workflow.invoke(initial_state, config) if config else self.workflow.invoke(initial_state)
            
            logger.info(f"Stage 4 Supervisor complete - messages: {len(result.get('messages', []))}")
            
            return result
        except Exception as e:
            logger.error(f"Stage 4 Supervisor workflow error: {str(e)}")
            raise
    
    def _stream_impl(self, user_input: str, config: Optional[RunnableConfig], **kwargs):
        """
        Stream Stage 4 Supervisor workflow with optional checkpointing.
        
        Args:
            user_input: User query/task
            config: Optional config with thread_id (for checkpointing)
            
        Yields:
            State updates as they occur
        """
        logger.info(f"Stage 4 Supervisor stream start - input: {user_input[:100]}...")
        
        # Load previous state if checkpointing enabled  
        if config and self.enable_checkpointing:
            try:
                previous_state = self.workflow.get_state(config)
                if previous_state and previous_state.values:
                    initial_state = previous_state.values.copy()
                    initial_state["messages"].append(HumanMessage(content=user_input))
                else:
                    initial_state = {"messages": [HumanMessage(content=user_input)]}
            except Exception:
                initial_state = {"messages": [HumanMessage(content=user_input)]}
        else:
            initial_state = {"messages": [HumanMessage(content=user_input)]}
        
        try:
            stream_method = self.workflow.stream(initial_state, config) if config else self.workflow.stream(initial_state)
            for chunk in stream_method:
                yield chunk
        except Exception as e:
            logger.error(f"Stage 4 Supervisor stream error: {str(e)}")
            raise
