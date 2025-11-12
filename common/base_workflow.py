"""
Base workflow class with integrated checkpointing support.
All workflows inherit from this to ensure consistent behavior.
"""
from typing import Optional, Any
from abc import ABC, abstractmethod

from langgraph.graph import StateGraph
from langchain_core.runnables import RunnableConfig

from common.config import config
from common.checkpointing import create_checkpointer, create_thread_config
from common.logging_config import get_logger
from common.model_factory import ModelType

logger = get_logger(__name__)


class BaseWorkflow(ABC):
    """
    Abstract base class for all agent workflows.
    
    Provides:
    - Optional checkpointing support via config
    - Consistent invoke/stream interface
    - Automatic thread_id management
    - Subclass hook for graph building
    """
    
    def __init__(self, enable_checkpointing: Optional[bool] = None):
        """
        Initialize base workflow with optional checkpointing.
        
        Args:
            enable_checkpointing: Enable checkpointing (defaults to config.ENABLE_CHECKPOINTING)
        """
        self.enable_checkpointing = enable_checkpointing or config.ENABLE_CHECKPOINTING
        
        # Initialize checkpointer if enabled
        self.checkpointer = create_checkpointer() if self.enable_checkpointing else None
        
        # Workflow will be set by subclass (compiled graph)
        self.workflow: Optional[Any] = None
        self.agent = None  # Subclasses should set this
        
        # Log checkpointing status prominently
        if self.enable_checkpointing:
            logger.info(f"✓ {self.__class__.__name__} initialized WITH CHECKPOINTING")
            logger.info(f"  Checkpointer: {type(self.checkpointer).__name__}")
        else:
            logger.info(f"  {self.__class__.__name__} initialized WITHOUT checkpointing")
    
    @abstractmethod
    def _build_graph(self):
        """
        Build and compile the graph. Must be implemented by subclasses.
        
        Returns:
            Compiled LangGraph workflow
        """
        pass
    
    def _compile_graph(self, graph: StateGraph):
        """
        Compile graph with optional checkpointing.
        
        Args:
            graph: StateGraph to compile
            
        Returns:
            Compiled graph with or without checkpointer
        """
        if self.checkpointer:
            logger.info("Compiling graph with checkpointing enabled")
            return graph.compile(checkpointer=self.checkpointer)
        else:
            logger.debug("Compiling graph without checkpointing")
            return graph.compile()
    
    def invoke(self, user_input: str, thread_id: Optional[str] = None, **kwargs) -> dict:
        """
        Execute workflow with user input.
        
        Args:
            user_input: User query/task
            thread_id: Optional thread ID (auto-generated if checkpointing enabled)
            **kwargs: Additional arguments for invoke
            
        Returns:
            Final state with result
        """
        # Build config with thread_id if checkpointing enabled
        if self.enable_checkpointing:
            config = create_thread_config(thread_id)
            logger.debug(f"Invoking with checkpointing - thread_id: {config['configurable']['thread_id']}")
            return self._invoke_impl(user_input, config, **kwargs)
        else:
            return self._invoke_impl(user_input, None, **kwargs)
    
    @abstractmethod
    def _invoke_impl(self, user_input: str, config: Optional[RunnableConfig], **kwargs) -> dict:
        """
        Implementation-specific invoke logic. Must be implemented by subclasses.
        
        Args:
            user_input: User query/task
            config: Optional RunnableConfig with thread_id
            **kwargs: Additional arguments
            
        Returns:
            Final state
        """
        pass
    
    def stream(self, user_input: str, thread_id: Optional[str] = None, **kwargs):
        """
        Stream workflow execution.
        
        Args:
            user_input: User query/task
            thread_id: Optional thread ID (auto-generated if checkpointing enabled)
            **kwargs: Additional arguments for stream
            
        Yields:
            State updates as they occur
        """
        # Build config with thread_id if checkpointing enabled
        if self.enable_checkpointing:
            config = create_thread_config(thread_id)
            logger.debug(f"Streaming with checkpointing - thread_id: {config['configurable']['thread_id']}")
            yield from self._stream_impl(user_input, config, **kwargs)
        else:
            yield from self._stream_impl(user_input, None, **kwargs)
    
    @abstractmethod
    def _stream_impl(self, user_input: str, config: Optional[RunnableConfig], **kwargs):
        """
        Implementation-specific stream logic. Must be implemented by subclasses.
        
        Args:
            user_input: User query/task
            config: Optional RunnableConfig with thread_id
            **kwargs: Additional arguments
            
        Yields:
            State updates
        """
        pass
    
    def get_app(self):
        """Get the compiled application."""
        return self.workflow
    
    def get_state(self, thread_id: str):
        """
        Get current state for a thread (requires checkpointing).
        
        Args:
            thread_id: Thread to get state for
            
        Returns:
            StateSnapshot or None
        """
        if not self.enable_checkpointing:
            logger.warning("Checkpointing not enabled, cannot get state")
            return None
        
        config = create_thread_config(thread_id)
        return self.workflow.get_state(config)
    
    def get_state_history(self, thread_id: str, limit: Optional[int] = None):
        """
        Get state history for a thread (requires checkpointing).
        
        Args:
            thread_id: Thread to get history for
            limit: Maximum number of checkpoints to return
            
        Returns:
            List of StateSnapshot objects
        """
        if not self.enable_checkpointing:
            logger.warning("Checkpointing not enabled, cannot get state history")
            return []
        
        config = create_thread_config(thread_id)
        return list(self.workflow.get_state_history(config, limit=limit))
