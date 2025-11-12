"""
Response handlers for extracting final responses from workflow results.
"""
from typing import Union


def extract_response(result: dict, target_stage: Union[int, float]) -> tuple[str, list]:
    """
    Extract final response and thought process from workflow result.
    
    Args:
        result: Workflow invocation result
        target_stage: Stage number that was executed
        
    Returns:
        Tuple of (final_response, thought_process)
    """
    # Stage 3 uses 'result' field directly
    if target_stage in [3.1, 3.2, 3.3]:
        return _extract_stage3_response(result)
    else:
        # Stage 1/2 uses messages
        return _extract_stage12_response(result)


def _extract_stage3_response(result: dict) -> tuple[str, list]:
    """Extract response from Stage 3 workflows (ReWOO, Reflection, Plan-Execute)."""
    final_response = result.get("result", "")
    thought_process = []
    
    # Add plan as thought process
    if "plan_string" in result:
        thought_process.append({
            "type": "plan",
            "content": result["plan_string"]
        })
    
    # Add tool executions
    if "results" in result:
        for step_name, step_result in result["results"].items():
            thought_process.append({
                "type": "tool_result",
                "step": step_name,
                "content": step_result[:200] + "..." if len(step_result) > 200 else step_result
            })
    
    return final_response, thought_process


def _extract_stage12_response(result: dict) -> tuple[str, list]:
    """Extract response from Stage 1/2 workflows (ReAct)."""
    messages = result.get("messages", [])
    final_response = ""
    thought_process = []
    
    # Parse messages to extract response and thought process
    for msg in messages:
        if hasattr(msg, "type"):
            if msg.type == "ai":
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    # Agent decided to use tools
                    for tool_call in msg.tool_calls:
                        thought_process.append({
                            "type": "tool_call",
                            "tool": tool_call["name"],
                            "args": tool_call["args"]
                        })
                elif msg.content:
                    # Final response from agent
                    final_response = msg.content
                    thought_process.append({
                        "type": "response",
                        "content": msg.content
                    })
            elif msg.type == "tool":
                # Tool result
                thought_process.append({
                    "type": "tool_result",
                    "content": msg.content[:200] + "..." if len(msg.content) > 200 else msg.content
                })
    
    return final_response, thought_process
