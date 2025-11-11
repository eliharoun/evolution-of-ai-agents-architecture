"""
Checkpointing utility for Stage 3 patterns using LangGraph built-in persistence.
Provides in-memory state persistence within conversation sessions.
"""

from typing import Optional, Dict, Any, List
import uuid
import logging
from langgraph.checkpoint.memory import InMemorySaver

logger = logging.getLogger(__name__)


def create_checkpointer():
    """
    Create a LangGraph in-memory checkpointer.
    
    Returns:
        InMemorySaver: LangGraph's built-in in-memory checkpointer
    """
    return InMemorySaver()


def create_thread_config(thread_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Create a thread configuration for LangGraph checkpointing.
    
    Args:
        thread_id: Optional thread ID. If not provided, generates a new one.
        
    Returns:
        Configuration dictionary for LangGraph
    """
    if thread_id is None:
        thread_id = str(uuid.uuid4())
    
    return {"configurable": {"thread_id": thread_id}}


def get_checkpoint_config(thread_id: str, checkpoint_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Create a checkpoint configuration for accessing specific checkpoint.
    
    Args:
        thread_id: Thread identifier
        checkpoint_id: Optional checkpoint identifier
        
    Returns:
        Configuration dictionary for accessing checkpoint
    """
    config = {"configurable": {"thread_id": thread_id}}
    if checkpoint_id:
        config["configurable"]["checkpoint_id"] = checkpoint_id
    return config


class CheckpointHelper:
    """
    Helper class for working with LangGraph checkpoints.
    
    This class provides convenience methods for managing checkpoints
    using LangGraph's built-in persistence mechanisms.
    """
    
    def __init__(self, graph):
        """
        Initialize checkpoint helper with compiled graph.
        
        Args:
            graph: Compiled LangGraph with checkpointer
        """
        self.graph = graph
    
    def get_current_state(self, thread_id: str):
        """
        Get the current state of a thread.
        
        Args:
            thread_id: Thread to get state for
            
        Returns:
            StateSnapshot object or None if not found
        """
        try:
            config = create_thread_config(thread_id)
            return self.graph.get_state(config)
        except Exception as e:
            logger.error(f"Error getting current state for thread {thread_id}: {e}")
            return None
    
    def get_state_history(self, thread_id: str, limit: Optional[int] = None):
        """
        Get the state history for a thread.
        
        Args:
            thread_id: Thread to get history for
            limit: Maximum number of checkpoints to return
            
        Returns:
            List of StateSnapshot objects
        """
        try:
            config = create_thread_config(thread_id)
            history = list(self.graph.get_state_history(config, limit=limit))
            return history
        except Exception as e:
            logger.error(f"Error getting state history for thread {thread_id}: {e}")
            return []
    
    def update_state(self, thread_id: str, values: Dict[str, Any], as_node: Optional[str] = None):
        """
        Update the state of a thread.
        
        Args:
            thread_id: Thread to update
            values: Values to update the state with
            as_node: Optional node name to update as
            
        Returns:
            Updated configuration
        """
        try:
            config = create_thread_config(thread_id)
            return self.graph.update_state(config, values, as_node=as_node)
        except Exception as e:
            logger.error(f"Error updating state for thread {thread_id}: {e}")
            return None
