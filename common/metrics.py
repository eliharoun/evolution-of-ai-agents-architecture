"""
Performance metrics tracking for Stage 3 patterns.
Provides comprehensive metrics comparison between different agent patterns.
"""

import time
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class PatternType(Enum):
    """Enumeration of supported agent patterns."""
    REWOO = "rewoo"
    REFLECTION = "reflection"
    PLAN_EXECUTE = "plan_execute"
    REACT = "react"  # For comparison with Stage 2


@dataclass
class ExecutionMetrics:
    """Metrics for a single agent execution."""
    
    pattern_type: PatternType
    session_id: str
    start_time: float
    end_time: Optional[float] = None
    total_iterations: int = 0
    tool_calls_count: int = 0
    tool_success_count: int = 0
    retry_count: int = 0
    success: bool = False
    error_message: Optional[str] = None
    
    # Pattern-specific metrics
    planning_time: Optional[float] = None
    execution_time: Optional[float] = None
    reflection_iterations: int = 0
    plan_revisions: int = 0
    
    # Response quality metrics
    response_length: Optional[int] = None
    context_preservation: Optional[float] = None  # 0-1 score
    
    def __post_init__(self):
        if self.end_time is None:
            self.end_time = time.time()
    
    @property
    def total_execution_time(self) -> float:
        """Calculate total execution time."""
        if self.end_time and self.start_time:
            return self.end_time - self.start_time
        return 0.0
    
    @property
    def tool_success_rate(self) -> float:
        """Calculate tool success rate."""
        if self.tool_calls_count == 0:
            return 0.0
        return self.tool_success_count / self.tool_calls_count
    
    @property
    def efficiency_score(self) -> float:
        """Calculate efficiency score based on iterations and time."""
        if self.total_execution_time == 0:
            return 0.0
        
        # Lower iterations and faster execution = higher efficiency
        base_score = 1.0
        iteration_penalty = max(0, (self.total_iterations - 1) * 0.1)
        time_penalty = max(0, (self.total_execution_time - 5) * 0.02)  # Penalty after 5 seconds
        
        return max(0.0, base_score - iteration_penalty - time_penalty)


class MetricsTracker:
    """
    Tracks and analyzes performance metrics for different agent patterns.
    
    Provides comprehensive comparison and analysis capabilities.
    """
    
    def __init__(self):
        self._metrics: List[ExecutionMetrics] = []
        self._active_executions: Dict[str, ExecutionMetrics] = {}
    
    def start_execution(
        self, 
        pattern_type: PatternType,
        session_id: str
    ) -> ExecutionMetrics:
        """
        Start tracking execution for a session.
        
        Args:
            pattern_type: Type of pattern being executed
            session_id: Unique session identifier
            
        Returns:
            ExecutionMetrics object for tracking
        """
        metrics = ExecutionMetrics(
            pattern_type=pattern_type,
            session_id=session_id,
            start_time=time.time()
        )
        
        self._active_executions[session_id] = metrics
        logger.info(f"Started tracking {pattern_type.value} execution for session {session_id}")
        
        return metrics
    
    def update_metrics(self, session_id: str, **kwargs) -> Optional[ExecutionMetrics]:
        """
        Update metrics for an active execution.
        
        Args:
            session_id: Session to update
            **kwargs: Metric values to update
            
        Returns:
            Updated ExecutionMetrics object or None if not found
        """
        if session_id not in self._active_executions:
            logger.warning(f"No active execution found for session {session_id}")
            return None
        
        metrics = self._active_executions[session_id]
        
        for key, value in kwargs.items():
            if hasattr(metrics, key):
                setattr(metrics, key, value)
        
        return metrics
    
    def finish_execution(
        self, 
        session_id: str, 
        success: bool = True,
        error_message: Optional[str] = None,
        **final_metrics
    ) -> Optional[ExecutionMetrics]:
        """
        Complete execution tracking and store final metrics.
        
        Args:
            session_id: Session to complete
            success: Whether execution was successful
            error_message: Optional error message if failed
            **final_metrics: Additional final metrics
            
        Returns:
            Completed ExecutionMetrics object
        """
        if session_id not in self._active_executions:
            logger.warning(f"No active execution found for session {session_id}")
            return None
        
        metrics = self._active_executions.pop(session_id)
        metrics.end_time = time.time()
        metrics.success = success
        metrics.error_message = error_message
        
        # Apply any final metric updates
        for key, value in final_metrics.items():
            if hasattr(metrics, key):
                setattr(metrics, key, value)
        
        self._metrics.append(metrics)
        
        logger.info(
            f"Completed {metrics.pattern_type.value} execution for session {session_id} "
            f"- Success: {success}, Time: {metrics.total_execution_time:.2f}s, "
            f"Iterations: {metrics.total_iterations}"
        )
        
        return metrics
    
    def get_pattern_comparison(self) -> Dict[PatternType, Dict[str, float]]:
        """
        Generate comparison metrics between different patterns.
        
        Returns:
            Dictionary with pattern comparison data
        """
        comparison = {}
        
        for pattern_type in PatternType:
            pattern_metrics = [m for m in self._metrics if m.pattern_type == pattern_type]
            
            if pattern_metrics:
                comparison[pattern_type] = {
                    'avg_execution_time': sum(m.total_execution_time for m in pattern_metrics) / len(pattern_metrics),
                    'avg_iterations': sum(m.total_iterations for m in pattern_metrics) / len(pattern_metrics),
                    'avg_tool_calls': sum(m.tool_calls_count for m in pattern_metrics) / len(pattern_metrics),
                    'success_rate': sum(1 for m in pattern_metrics if m.success) / len(pattern_metrics),
                    'avg_tool_success_rate': sum(m.tool_success_rate for m in pattern_metrics) / len(pattern_metrics),
                    'avg_efficiency_score': sum(m.efficiency_score for m in pattern_metrics) / len(pattern_metrics),
                    'execution_count': len(pattern_metrics)
                }
            else:
                comparison[pattern_type] = {
                    'avg_execution_time': 0.0,
                    'avg_iterations': 0.0,
                    'avg_tool_calls': 0.0,
                    'success_rate': 0.0,
                    'avg_tool_success_rate': 0.0,
                    'avg_efficiency_score': 0.0,
                    'execution_count': 0
                }
        
        return comparison
    
    def get_session_metrics(self, session_id: str) -> Optional[ExecutionMetrics]:
        """
        Get metrics for a specific session.
        
        Args:
            session_id: Session to get metrics for
            
        Returns:
            ExecutionMetrics object or None if not found
        """
        for metrics in self._metrics:
            if metrics.session_id == session_id:
                return metrics
        return None
    
    def get_pattern_metrics(self, pattern_type: PatternType) -> List[ExecutionMetrics]:
        """
        Get all metrics for a specific pattern type.
        
        Args:
            pattern_type: Pattern to get metrics for
            
        Returns:
            List of ExecutionMetrics objects
        """
        return [m for m in self._metrics if m.pattern_type == pattern_type]
    
    def generate_comparison_report(self) -> str:
        """
        Generate a detailed comparison report between patterns.
        
        Returns:
            Formatted comparison report
        """
        comparison = self.get_pattern_comparison()
        
        report = "# Stage 3 Pattern Comparison Report\n\n"
        report += "| Pattern | Avg Time (s) | Avg Iterations | Avg Tool Calls | Success Rate | Efficiency Score | Executions |\n"
        report += "|---------|--------------|----------------|----------------|--------------|------------------|------------|\n"
        
        for pattern_type, metrics in comparison.items():
            report += (
                f"| {pattern_type.value.upper()} | "
                f"{metrics['avg_execution_time']:.2f} | "
                f"{metrics['avg_iterations']:.1f} | "
                f"{metrics['avg_tool_calls']:.1f} | "
                f"{metrics['success_rate']:.1%} | "
                f"{metrics['avg_efficiency_score']:.2f} | "
                f"{metrics['execution_count']} |\n"
            )
        
        report += "\n## Key Insights\n"
        
        # Find best performing pattern
        if comparison:
            best_efficiency = max(
                comparison.items(),
                key=lambda x: x[1]['avg_efficiency_score']
            )
            fastest = min(
                comparison.items(),
                key=lambda x: x[1]['avg_execution_time'] if x[1]['execution_count'] > 0 else float('inf')
            )
            
            report += f"- **Most Efficient Pattern**: {best_efficiency[0].value.upper()}\n"
            report += f"- **Fastest Pattern**: {fastest[0].value.upper()}\n"
        
        return report
    
    def clear_metrics(self, pattern_type: Optional[PatternType] = None):
        """
        Clear stored metrics.
        
        Args:
            pattern_type: Optional pattern type to clear (None = clear all)
        """
        if pattern_type:
            self._metrics = [m for m in self._metrics if m.pattern_type != pattern_type]
            logger.info(f"Cleared metrics for pattern {pattern_type.value}")
        else:
            self._metrics.clear()
            logger.info("Cleared all metrics")


# Global metrics tracker instance
metrics_tracker = MetricsTracker()
