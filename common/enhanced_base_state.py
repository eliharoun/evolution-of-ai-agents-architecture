"""
Enhanced state to support pattern-specific data,
retry logic, and performance metrics.
"""
from typing import Any, Dict, Optional
from common.base_state import BaseAgentState


class EnhancedBaseAgentState(BaseAgentState):
    """    
    Enhanced to support pattern-specific data,
    retry logic, and performance metrics.
    Inherits the basic messages and iterations from common.base_state.
    """
    pattern_name: str  # "rewoo", "reflection", or "plan_execute"
    
    # Retry and failure handling
    retry_count: int
    max_retries: int
    last_error: Optional[str]
    
    # Performance tracking
    start_time: Optional[float]
    end_time: Optional[float]
    tool_calls_count: int
    tool_success_count: int
    
    # Pattern-specific data
    pattern_data: Dict[str, Any]  # Store pattern-specific state