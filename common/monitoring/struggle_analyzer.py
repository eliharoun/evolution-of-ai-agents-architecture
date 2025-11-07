"""
StruggleAnalyzer - Standalone tool for detecting agent performance issues.

This analyzer can be used by any agent workflow to monitor for common struggle patterns:
- High iteration counts (confusion, inefficiency)
- Tool confusion (parallel or conflicting tool usage)
- Context loss (repeated tool calls, forgetting previous results)

The analyzer is configurable to support different thresholds for different agent types.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from common.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class StruggleThresholds:
    """Configurable thresholds for struggle detection."""
    high_iterations_threshold: int = 4  # >= this many iterations = struggle
    context_loss_threshold: int = 2     # > this many repeats = context loss
    parallel_tools_threshold: int = 2   # >= this many parallel tools = confusion
    
    @classmethod
    def for_stage(cls, stage: int) -> 'StruggleThresholds':
        """Get recommended thresholds for a specific stage."""
        if stage == 1:
            # Stage 1: Only 2 tools, should be very efficient
            return cls(
                high_iterations_threshold=3,
                context_loss_threshold=1,
                parallel_tools_threshold=2
            )
        elif stage == 2:
            # Stage 2: 7 tools, allow more iterations but detect confusion
            return cls(
                high_iterations_threshold=4,
                context_loss_threshold=2,
                parallel_tools_threshold=2
            )
        else:
            # Future stages: Default thresholds
            return cls()


class StruggleAnalyzer:
    """
    Standalone analyzer for detecting agent struggle patterns.
    
    Usage:
        analyzer = StruggleAnalyzer(stage=2)
        analyzer.analyze_iteration(iteration_count=5)
        analyzer.analyze_tool_calls(['get_order_status', 'check_inventory'])
        stats = analyzer.get_stats()
        analyzer.reset()  # For new conversation
    """
    
    def __init__(self, 
                 stage: int = 2, 
                 thresholds: Optional[StruggleThresholds] = None,
                 enable_logging: bool = True):
        """
        Initialize the struggle analyzer.
        
        Args:
            stage: Stage number for default thresholds
            thresholds: Custom thresholds (uses stage default if None)
            enable_logging: Whether to log struggle detections
        """
        self.stage = stage
        self.thresholds = thresholds or StruggleThresholds.for_stage(stage)
        self.enable_logging = enable_logging
        
        # Initialize tracking variables
        self._reset_tracking()
        
        logger.info(f"StruggleAnalyzer initialized for Stage {stage} - thresholds: "
                   f"iterations>={self.thresholds.high_iterations_threshold}, "
                   f"context_loss>{self.thresholds.context_loss_threshold}, "
                   f"parallel>={self.thresholds.parallel_tools_threshold}")
    
    def _reset_tracking(self):
        """Reset all tracking variables."""
        self._indicators = {
            "high_iterations": False,
            "iteration_count": 0,
            "tool_confusion": False,
            "unique_tools": 0,
            "parallel_tool_calls": [],
            "context_loss": False,
            "tool_usage_history": [],
            "repeated_tools": {}
        }
    
    def analyze_iteration(self, iteration_count: int) -> None:
        """
        Analyze iteration count for struggle detection.
        
        Args:
            iteration_count: Current iteration number
        """
        self._indicators["iteration_count"] = iteration_count
        
        # Check for high iteration count
        if iteration_count >= self.thresholds.high_iterations_threshold:
            if not self._indicators["high_iterations"]:
                self._indicators["high_iterations"] = True
                if self.enable_logging:
                    logger.warning(f"🚨 STRUGGLE DETECTED: High iteration count ({iteration_count}) "
                                 f"- agent may be confused with tool selection")
    
    def analyze_tool_calls(self, tool_calls: List[str]) -> None:
        """
        Analyze tool calls for struggle patterns.
        
        Args:
            tool_calls: List of tool names being called in this iteration
        """
        if not tool_calls:
            return
            
        # Track all tool usage for history
        self._indicators["tool_usage_history"].extend(tool_calls)
        
        # Update unique tools count
        unique_tools = set(self._indicators["tool_usage_history"])
        self._indicators["unique_tools"] = len(unique_tools)
        
        # Detect parallel tool usage (potential confusion)
        if len(tool_calls) >= self.thresholds.parallel_tools_threshold:
            if not self._indicators["tool_confusion"]:
                self._indicators["tool_confusion"] = True
                self._indicators["parallel_tool_calls"].append(tool_calls)
                if self.enable_logging:
                    logger.warning(f"🚨 STRUGGLE DETECTED: Parallel tool usage - {tool_calls} "
                                 f"- agent may be confused about dependencies")
        
        # Detect context loss (repeated tool calls)
        tool_counts = {}
        for tool in self._indicators["tool_usage_history"]:
            tool_counts[tool] = tool_counts.get(tool, 0) + 1
        
        for tool, count in tool_counts.items():
            if count > self.thresholds.context_loss_threshold:
                if not self._indicators["context_loss"]:
                    self._indicators["context_loss"] = True
                    self._indicators["repeated_tools"] = tool_counts
                    if self.enable_logging:
                        logger.warning(f"🚨 STRUGGLE DETECTED: Context loss - tool '{tool}' used {count} times "
                                     f"- agent may be forgetting previous results")
                break  # Only trigger once per session
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get current struggle statistics.
        
        Returns:
            Dictionary with struggle indicators and details
        """
        return {
            "high_iterations": self._indicators["high_iterations"],
            "iteration_count": self._indicators["iteration_count"],
            "tool_confusion": self._indicators["tool_confusion"],
            "unique_tools": self._indicators["unique_tools"],
            "context_loss": self._indicators["context_loss"],
            "repeated_tools": self._indicators["repeated_tools"].copy()
        }
    
    def reset(self) -> None:
        """Reset all struggle statistics for new session."""
        if self.enable_logging:
            logger.debug(f"StruggleAnalyzer reset for Stage {self.stage}")
        self._reset_tracking()
    
    def has_struggles(self) -> bool:
        """
        Check if any struggles have been detected.
        
        Returns:
            True if any struggle indicators are active
        """
        return (self._indicators["high_iterations"] or 
                self._indicators["tool_confusion"] or 
                self._indicators["context_loss"])
    
    def get_struggle_count(self) -> int:
        """
        Get total count of active struggles.
        
        Returns:
            Number of different struggle types detected
        """
        count = 0
        if self._indicators["high_iterations"]:
            count += 1
        if self._indicators["tool_confusion"]:
            count += 1
        if self._indicators["context_loss"]:
            count += 1
        return count
    
    def get_struggle_summary(self) -> str:
        """
        Get human-readable summary of detected struggles.
        
        Returns:
            Formatted summary string
        """
        struggles = []
        
        if self._indicators["high_iterations"]:
            struggles.append(f"High Iterations ({self._indicators['iteration_count']})")
            
        if self._indicators["tool_confusion"]:
            struggles.append(f"Tool Confusion ({self._indicators['unique_tools']} tools)")
            
        if self._indicators["context_loss"]:
            repeated = [(tool, count) for tool, count in self._indicators["repeated_tools"].items() 
                       if count > self.thresholds.context_loss_threshold]
            if repeated:
                tool_info = ", ".join([f"{tool}({count}x)" for tool, count in repeated])
                struggles.append(f"Context Loss ({tool_info})")
        
        return "; ".join(struggles) if struggles else "No struggles detected"
