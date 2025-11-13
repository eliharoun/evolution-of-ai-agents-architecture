"""
Retry logic utility for Stage 3 patterns using LangChain middleware.
Leverages built-in ToolRetryMiddleware and ModelFallbackMiddleware.
"""

import logging
from typing import Dict, Any, Optional, List, Type
from langchain.agents.middleware import ToolRetryMiddleware, ModelFallbackMiddleware

logger = logging.getLogger(__name__)


def create_tool_retry_middleware(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    tools: Optional[List[str]] = None
):
    """
    Create LangChain's built-in ToolRetryMiddleware for Stage 3 patterns.
    
    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay before first retry
        max_delay: Maximum delay between retries
        backoff_factor: Exponential backoff multiplier
        jitter: Whether to add random jitter to delays
        tools: Optional list of tool names to apply retry to (None = all tools)
        
    Returns:
        Configured ToolRetryMiddleware instance
    """
    return ToolRetryMiddleware(
        max_retries=max_retries,
        tools=tools,
        initial_delay=initial_delay,
        max_delay=max_delay,
        backoff_factor=backoff_factor,
        jitter=jitter,
        on_failure="return_message"  # Let LLM handle failures gracefully
    )


def create_model_fallback_middleware(*fallback_models: str):
    """
    Create LangChain's built-in ModelFallbackMiddleware.
    
    Args:
        *fallback_models: Model names to fallback to in order
        
    Returns:
        Configured ModelFallbackMiddleware instance
    """
    return ModelFallbackMiddleware(*fallback_models)


class PatternRetryConfig:
    """Configuration for pattern-level retry behavior."""
    
    def __init__(
        self,
        max_retries: int = 2,
        initial_delay: float = 1.0,
        max_delay: float = 30.0,
        backoff_multiplier: float = 2.0,
        jitter: bool = True
    ):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.backoff_multiplier = backoff_multiplier
        self.jitter = jitter


class PatternRetryManager:
    """
    Manages pattern-level retry logic for advanced agent patterns.
    
    Uses custom retry logic for pattern-specific failures while
    leveraging LangChain middleware for tool-level retries.
    """
    
    def __init__(self, config: Optional[PatternRetryConfig] = None):
        self.config = config or PatternRetryConfig()
    
    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for retry with exponential backoff."""
        import time
        
        delay = self.config.initial_delay * (self.config.backoff_multiplier ** attempt)
        delay = min(delay, self.config.max_delay)
        
        if self.config.jitter:
            import random
            delay *= (0.5 + random.random() * 0.5)
        
        return delay
    
    def retry_pattern_execution(
        self,
        pattern_func,
        state: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute pattern with retry logic.
        
        Args:
            pattern_func: Pattern execution function
            state: Current state
            **kwargs: Additional arguments
            
        Returns:
            Dictionary with result and retry metadata
        """
        import time
        
        last_exception = None
        retry_count = 0
        
        while retry_count <= self.config.max_retries:
            try:
                start_time = time.time()
                result = pattern_func(state, **kwargs)
                end_time = time.time()
                
                return {
                    'success': True,
                    'result': result,
                    'retry_count': retry_count,
                    'execution_time': end_time - start_time,
                    'error': None
                }
                
            except Exception as e:
                last_exception = e
                logger.warning(
                    f"Pattern execution failed (attempt {retry_count + 1}): {str(e)}"
                )
                
                if retry_count < self.config.max_retries:
                    delay = self.calculate_delay(retry_count)
                    logger.info(f"Retrying pattern in {delay:.2f} seconds...")
                    time.sleep(delay)
                
                retry_count += 1
        
        # All retries exhausted
        logger.error(f"Pattern execution failed after {retry_count} attempts: {str(last_exception)}")
        return {
            'success': False,
            'result': None,
            'retry_count': retry_count,
            'execution_time': 0,
            'error': str(last_exception)
        }


def get_recommended_retry_middleware() -> List:
    """
    Get recommended retry middleware configuration for Stage 3 patterns.
    
    Returns:
        List of configured middleware instances
    """
    middleware = []
    
    # Tool-level retries
    tool_retry = create_tool_retry_middleware(
        max_retries=3,
        initial_delay=1.0,
        max_delay=60.0,
        backoff_factor=2.0,
        jitter=True
    )
    if tool_retry:
        middleware.append(tool_retry)
    
    # Model fallback for reliability
    model_fallback = create_model_fallback_middleware(
        "gpt-4o-mini",  # Fallback to smaller model
        "gpt-3.5-turbo"  # Final fallback
    )
    if model_fallback:
        middleware.append(model_fallback)
    
    return middleware
