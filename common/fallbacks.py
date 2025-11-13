"""
Fallback handling for Stage 3 patterns using LangChain/LangGraph built-in functionality.
Leverages interrupt-based human-in-the-loop and middleware for robust fallback handling.
"""

import logging
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from langgraph.types import interrupt

logger = logging.getLogger(__name__)


class FallbackStrategy(ABC):
    """Abstract base class for fallback strategies."""
    
    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the fallback strategy.
        
        Args:
            context: Context information about the failure
            
        Returns:
            Dictionary with fallback result
        """
        pass


class InterruptBasedFallback(FallbackStrategy):
    """
    Uses LangGraph's interrupt() for human-in-the-loop workflow.
    
    This strategy implements the LangGraph interrupt pattern for
    seamless human handoff with context preservation.
    """
    
    def __init__(self, timeout_seconds: float = 30.0):
        self.timeout_seconds = timeout_seconds
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute interrupt-based fallback using LangGraph's interrupt system.
        
        Pauses graph execution and waits for human intervention.
        """
        logger.info("Executing LangGraph interrupt-based fallback")
        
        # Create comprehensive interrupt payload
        interrupt_payload = {
            'type': 'human_handoff_request',
            'message': (
                "I'm having difficulty processing this customer request and need "
                "human assistance to provide the best possible service."
            ),
            'customer_request': context.get('user_message', ''),
            'failure_context': {
                'pattern_failures': context.get('pattern_failures', []),
                'retry_count': context.get('retry_count', 0),
                'execution_time': context.get('execution_time', 0),
                'error_details': context.get('last_error', '')
            },
            'support_ticket': {
                'id': f"TICKET-{context.get('session_id', 'UNKNOWN')}",
                'priority': self._determine_priority(context),
                'category': 'technical_assistance'
            },
            'instructions': {
                'for_agent': (
                    "A human customer service representative will take over. "
                    "Please provide a response that addresses the customer's needs."
                ),
                'for_human': (
                    "This customer request requires human attention. The AI agent "
                    "encountered technical difficulties. Please provide an appropriate "
                    "response to help the customer."
                )
            }
        }
        
        try:
            # Use LangGraph's interrupt to pause and wait for human input
            human_response = interrupt(interrupt_payload)
            
            return {
                'success': True,
                'response': human_response,
                'handoff_type': 'langgraph_interrupt',
                'requires_resume': True,
                'original_context': context
            }
            
        except Exception as e:
            logger.error(f"Interrupt-based fallback failed: {e}")
            return self._simple_fallback_response(context)
    
    def _determine_priority(self, context: Dict[str, Any]) -> str:
        """Determine support ticket priority based on failure context."""
        retry_count = context.get('retry_count', 0)
        execution_time = context.get('execution_time', 0)
        
        if retry_count >= 3 or execution_time > self.timeout_seconds:
            return 'high'
        elif retry_count >= 2:
            return 'medium'
        else:
            return 'low'
    
    def _simple_fallback_response(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Provide simple fallback when interrupt is not available."""
        return {
            'success': True,
            'response': (
                "I apologize for the technical difficulty. A customer service "
                "representative will assist you shortly. Your request has been "
                f"logged with ticket ID: TICKET-{context.get('session_id', 'UNKNOWN')}"
            ),
            'handoff_type': 'simple_fallback',
            'requires_resume': False
        }


class HumanHandoffFallback(FallbackStrategy):
    """
    Traditional fallback that simulates human handoff.
    
    Used when LangGraph interrupts are not available or not desired.
    """
    
    def __init__(self, handoff_message: Optional[str] = None):
        self.handoff_message = handoff_message or (
            "I apologize for any confusion. Let me connect you with one of our "
            "human customer service representatives who can assist you better."
        )
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute traditional human handoff fallback."""
        logger.info("Executing traditional human handoff fallback")
        
        ticket_id = f"SUPPORT-{context.get('session_id', 'UNKNOWN')}"
        
        return {
            'success': True,
            'response': self.handoff_message,
            'handoff_type': 'human_support',
            'ticket_id': ticket_id,
            'context': context.get('user_message', ''),
            'pattern_failures': context.get('pattern_failures', [])
        }


class SimpleResponseFallback(FallbackStrategy):
    """
    Simple response fallback with predefined message.
    
    Used when advanced patterns fail and we need a basic response.
    """
    
    def __init__(self, message: Optional[str] = None):
        self.message = message or (
            "I apologize, but I'm having difficulty processing your request at the moment. "
            "Please try rephrasing your question or contact customer support for assistance."
        )
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute simple response fallback."""
        logger.info("Executing simple response fallback")
        
        return {
            'success': True,
            'response': self.message,
            'fallback_type': 'simple_response',
            'original_request': context.get('user_message', ''),
            'failures': context.get('pattern_failures', [])
        }


class TimeoutFallback(FallbackStrategy):
    """
    Timeout-based fallback strategy.
    
    Triggers when patterns take too long to execute.
    """
    
    def __init__(self, timeout_seconds: float = 30.0):
        self.timeout_seconds = timeout_seconds
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute timeout fallback."""
        execution_time = context.get('execution_time', 0)
        logger.warning(f"Pattern timed out after {execution_time:.2f}s (limit: {self.timeout_seconds}s)")
        
        return {
            'success': True,
            'response': (
                "Your request is taking longer than expected to process. "
                "Our system is working on it, but I can connect you with "
                "human support if you need immediate assistance."
            ),
            'fallback_type': 'timeout',
            'execution_time': execution_time,
            'timeout_limit': self.timeout_seconds
        }


class FallbackHandler:
    """
    Main fallback handler that manages different fallback strategies.
    
    Coordinates fallback selection and execution based on failure context.
    """
    
    def __init__(self):
        self.strategies: Dict[str, FallbackStrategy] = {
            'human_handoff': HumanHandoffFallback(),
            'simple_response': SimpleResponseFallback(),
            'timeout': TimeoutFallback()
        }
        self.default_strategy = 'human_handoff'
    
    def register_strategy(self, name: str, strategy: FallbackStrategy):
        """
        Register a new fallback strategy.
        
        Args:
            name: Strategy name
            strategy: Fallback strategy instance
        """
        self.strategies[name] = strategy
        logger.info(f"Registered fallback strategy: {name}")
    
    def set_default_strategy(self, strategy_name: str):
        """
        Set the default fallback strategy.
        
        Args:
            strategy_name: Name of strategy to use as default
        """
        if strategy_name in self.strategies:
            self.default_strategy = strategy_name
            logger.info(f"Set default fallback strategy: {strategy_name}")
        else:
            logger.error(f"Unknown fallback strategy: {strategy_name}")
    
    def execute_fallback(
        self, 
        context: Dict[str, Any], 
        strategy_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute appropriate fallback strategy.
        
        Args:
            context: Context information about the failure
            strategy_name: Specific strategy to use (optional)
            
        Returns:
            Fallback execution result
        """
        # Determine strategy to use
        if strategy_name and strategy_name in self.strategies:
            strategy = self.strategies[strategy_name]
        elif 'timeout' in context and context['timeout']:
            strategy = self.strategies['timeout']
        else:
            strategy = self.strategies[self.default_strategy]
        
        logger.info(f"Executing fallback strategy: {strategy.__class__.__name__}")
        
        try:
            return strategy.execute(context)
        except Exception as e:
            logger.error(f"Fallback strategy failed: {e}")
            
            # Ultimate fallback - simple response
            return {
                'success': True,
                'response': (
                    "I apologize for the technical difficulty. "
                    "Please contact customer support for assistance."
                ),
                'fallback_type': 'emergency',
                'error': str(e)
            }
    
    def should_fallback(self, context: Dict[str, Any]) -> bool:
        """
        Determine if fallback should be triggered.
        
        Args:
            context: Execution context with metrics
            
        Returns:
            True if fallback should be triggered
        """
        # Check for timeout
        execution_time = context.get('execution_time', 0)
        timeout_limit = context.get('timeout_limit', 30.0)
        if execution_time > timeout_limit:
            return True
        
        # Check for excessive retries
        total_retries = context.get('total_retries', 0)
        if total_retries >= 5:  # Configurable threshold
            return True
        
        # Check for pattern-specific failures
        pattern_failures = context.get('pattern_failures', [])
        if len(pattern_failures) >= 3:  # All patterns failed
            return True
        
        return False


# Default fallback handler instance
default_fallback_handler = FallbackHandler()
