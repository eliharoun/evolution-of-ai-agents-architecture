"""
LangGraph workflow orchestration for Stage 4 Supervisor 2 implementation.

This is a CUSTOM supervisor implementation that provides full transparency
into how specialist coordination works. Instead of using create_supervisor(),
we manually create a ReAct agent with wrapped specialist tools.

Key Educational Differences from Supervisor 1:
1. Specialists are wrapped as tools explicitly (visible in code)
2. Uses standard create_react_agent (not create_supervisor)
3. Full control over delegation logic
4. Can customize information flow between supervisor and specialists
"""

from typing import Optional
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.prebuilt import create_react_agent

from stage_4.supervisor_2.agents.specialist_wrappers import create_specialist_tool_wrappers
from stage_4.common import SUPERVISOR_PROMPT
from common.base_workflow import BaseWorkflow
from common.model_factory import ModelFactory, ModelType
from common.config import config
from common.logging_config import get_logger
from typing import cast

logger = get_logger(__name__)


class CustomSupervisorWorkflow(BaseWorkflow):
    """
    Custom implementation of the Supervisor pattern for educational purposes.
    
    Pattern (Tool Calling):
    1. Customer query → Supervisor (ReAct agent)
    2. Supervisor calls specialist tools (wrapped agents)
    3. Specialist agents execute their domain tools → Return results
    4. Supervisor processes tool results → Final response
    
    Educational Value:
    - See exactly how specialists are wrapped as tools
    - Understand the supervisor as just a ReAct agent with high-level tools
    - Full transparency in delegation and aggregation
    - Can customize information flow at every step
    
    Differences from Supervisor 1:
    - Supervisor 1: Uses create_supervisor() (black box)
    - Supervisor 2: Uses create_react_agent() with wrapped specialists (transparent)
    """
    
    def __init__(
        self,
        model_type: Optional[ModelType] = None,
        enable_checkpointing: Optional[bool] = None
    ):
        """
        Initialize the custom supervisor workflow.
        
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
        
        # Create specialist tool wrappers (this is the key custom pattern)
        logger.info("Creating specialist tool wrappers for custom supervisor...")
        self.specialist_tools = create_specialist_tool_wrappers(
            model=self.model,
            checkpointer=self.checkpointer
        )
        logger.info(f"Created {len(self.specialist_tools)} specialist tool wrappers")
        
        # Build the supervisor as a ReAct agent
        self.workflow = self._build_graph()
        
        logger.info("Stage 4 Custom Supervisor workflow initialized (educational implementation)")
    
    def _build_graph(self):
        """
        Build the custom supervisor using standard create_react_agent.
        
        The supervisor is simply a ReAct agent where the "tools" are wrapped
        specialist agents. This makes the delegation pattern fully transparent.
        
        Returns:
            Compiled supervisor ReAct agent
        """
        logger.info("Building custom supervisor as ReAct agent with specialist tools...")
        
        # Create supervisor as a standard ReAct agent
        # The "magic" is that tools are actually full agents wrapped as tools
        supervisor = create_react_agent(
            model=self.model,
            tools=self.specialist_tools,  # Wrapped specialist agents
            prompt=SUPERVISOR_PROMPT,
            checkpointer=self.checkpointer,
            name="custom_supervisor"
        )
        
        logger.info("Custom supervisor compiled successfully")
        return supervisor
    
    def get_app(self):
        """Get the compiled application."""
        return self.workflow
    
    def _invoke_impl(self, user_input: str, config: Optional[RunnableConfig], **kwargs) -> dict:
        """
        Execute Stage 4 Custom Supervisor workflow with optional checkpointing.
        
        Args:
            user_input: User query/task
            config: Optional config with thread_id (for checkpointing)
            
        Returns:
            Final state with aggregated specialist responses
        """
        logger.info(f"Stage 4 Custom Supervisor invoke - input: {user_input[:100]}...")
        
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
            
            logger.info(f"Stage 4 Custom Supervisor complete - messages: {len(result.get('messages', []))}")
            
            return result
        except Exception as e:
            logger.error(f"Stage 4 Custom Supervisor workflow error: {str(e)}")
            raise
    
    def _stream_impl(self, user_input: str, config: Optional[RunnableConfig], **kwargs):
        """
        Stream Stage 4 Custom Supervisor workflow with optional checkpointing.
        
        Args:
            user_input: User query/task
            config: Optional config with thread_id (for checkpointing)
            
        Yields:
            State updates as they occur
        """
        logger.info(f"Stage 4 Custom Supervisor stream start - input: {user_input[:100]}...")
        
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
            logger.error(f"Stage 4 Custom Supervisor stream error: {str(e)}")
            raise
