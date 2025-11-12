"""
Streaming response handlers for different agent stages.
"""
import json
import asyncio
from typing import AsyncGenerator, Generator, Union

from common.logging_config import get_logger
from backend.workflow_loader import load_workflow

logger = get_logger(__name__)


async def stream_agent_response(message: str, stage: Union[int, float], thread_id: str = None) -> AsyncGenerator[str, None]:
    """
    Stream agent response with stage-specific handling.
    
    Args:
        message: User's message
        stage: Stage number (1, 2, 3.1, 3.2, 3.3)
        thread_id: Optional thread_id for checkpointing
        
    Yields:
        Server-Sent Events formatted data
    """
    try:
        workflow = load_workflow(stage)
        
        # Send thread_id at start of stream for frontend tracking
        if thread_id:
            initial_event = {"type": "thread_id", "thread_id": thread_id}
            yield f"data: {json.dumps(initial_event)}\n\n"
        
        # Call stream method based on workflow capabilities
        if hasattr(workflow, 'enable_checkpointing') and workflow.enable_checkpointing and thread_id:
            # Workflow supports checkpointing
            stream_chunks = workflow.stream(message, thread_id)
        else:
            # Workflow doesn't support checkpointing (like Stage 1)
            stream_chunks = workflow.stream(message)
        
        for chunk in stream_chunks:
            # Parse the chunk from each node
            for node_name, node_output in chunk.items():
                
                # Stage 3 nodes: plan, tool, solve
                if node_name == "plan":
                    for event in _handle_plan_node(node_output, stage):
                        yield event
                elif node_name == "tool":
                    for event in _handle_tool_node(node_output, stage):
                        yield event
                elif node_name == "solve":
                    async for event in _handle_solve_node(node_output, stage):
                        yield event
                
                # Stage 1/2 nodes: agent, tools
                elif node_name == "agent":
                    async for event in _handle_agent_node(node_output, stage, workflow):
                        yield event
                elif node_name == "tools":
                    for event in _handle_tools_node(node_output, stage):
                        yield event
        
        # Send completion event
        for event in _send_completion_event(stage, workflow):
            yield event
        
    except Exception as e:
        logger.error(f"Stream error: {str(e)}")
        error_event = {"type": "error", "content": str(e)}
        yield f"data: {json.dumps(error_event)}\n\n"


def _handle_plan_node(node_output: dict, stage: Union[int, float]) -> Generator[str, None, None]:
    """Handle ReWOO planner node output."""
    plan_string = node_output.get("plan_string", "")
    if plan_string:
        event_data = {
            "type": "thought",
            "node": "plan",
            "content": f"Planning complete: {len(node_output.get('steps', []))} steps",
            "plan": plan_string,  # Send full plan without truncation
            "stage": stage
        }
        yield f"data: {json.dumps(event_data)}\n\n"


def _handle_tool_node(node_output: dict, stage: Union[int, float]) -> Generator[str, None, None]:
    """Handle ReWOO worker node output."""
    results = node_output.get("results", {})
    if results:
        latest_key = list(results.keys())[-1]
        latest_result = results[latest_key]
        content = f"{latest_key}: {latest_result[:200]}..." if len(latest_result) > 200 else f"{latest_key}: {latest_result}"
        event_data = {
            "type": "observation",
            "node": "tool",
            "content": content,
            "stage": stage
        }
        yield f"data: {json.dumps(event_data)}\n\n"


async def _handle_solve_node(node_output: dict, stage: Union[int, float]) -> AsyncGenerator[str, None]:
    """Handle ReWOO solver node output (final response)."""
    result_text = node_output.get("result", "")
    if result_text:
        yield f"data: {json.dumps({'type': 'response_start'})}\n\n"
        
        # Stream word-by-word
        words = result_text.split(' ')
        for i, word in enumerate(words):
            word_with_space = word + (' ' if i < len(words) - 1 else '')
            event_data = {
                "type": "response_chunk",
                "node": "solve",
                "content": word_with_space,
                "word_index": i,
                "total_words": len(words)
            }
            yield f"data: {json.dumps(event_data)}\n\n"
            await asyncio.sleep(0.05)
        
        yield f"data: {json.dumps({'type': 'response_complete', 'stage': stage})}\n\n"


async def _handle_agent_node(node_output: dict, stage: Union[int, float], workflow) -> AsyncGenerator[str, None]:
    """Handle Stage 1/2 agent node output."""
    messages = node_output.get("messages", [])
    
    if not messages:
        return
    
    msg = messages[-1]
    
    # Check if agent is making tool calls
    if hasattr(msg, "tool_calls") and msg.tool_calls:
        for tool_call in msg.tool_calls:
            event_data = {
                "type": "thought",
                "node": "agent",
                "content": f"Using tool: {tool_call['name']}",
                "tool_call": {
                    "name": tool_call["name"],
                    "args": tool_call["args"]
                },
                "stage": stage,
                "tools_available": len(workflow.agent.tools)
            }
            yield f"data: {json.dumps(event_data)}\n\n"
    
    # Check if agent is providing final response
    elif msg.content:
        yield f"data: {json.dumps({'type': 'response_start'})}\n\n"
        
        # Stream word-by-word
        words = msg.content.split(' ')
        for i, word in enumerate(words):
            word_with_space = word + (' ' if i < len(words) - 1 else '')
            event_data = {
                "type": "response_chunk",
                "node": "agent",
                "content": word_with_space,
                "word_index": i,
                "total_words": len(words)
            }
            yield f"data: {json.dumps(event_data)}\n\n"
            await asyncio.sleep(0.05)
        
        # Signal response completion
        completion_event = {'type': 'response_complete', 'stage': stage}
        
        # Add struggle stats for Stage 2
        if stage == 2 and hasattr(workflow, 'get_struggle_stats'):
            completion_event['struggle_stats'] = workflow.get_struggle_stats()
        
        yield f"data: {json.dumps(completion_event)}\n\n"


def _handle_tools_node(node_output: dict, stage: Union[int, float]) -> Generator[str, None, None]:
    """Handle Stage 1/2 tools node output."""
    messages = node_output.get("messages", [])
    
    if messages:
        for msg in messages:
            if hasattr(msg, "content"):
                # Truncate long tool results
                content = msg.content[:300] + "..." if len(msg.content) > 300 else msg.content
                event_data = {
                    "type": "observation",
                    "node": "tools",
                    "content": content,
                    "full_length": len(msg.content),
                    "stage": stage
                }
                yield f"data: {json.dumps(event_data)}\n\n"


def _send_completion_event(stage: Union[int, float], workflow) -> Generator[str, None, None]:
    """Send completion event with optional struggle stats."""
    completion_data = {"type": "done", "stage": stage}
    
    # Add struggle stats for Stage 2
    if stage == 2 and hasattr(workflow, 'get_struggle_stats'):
        completion_data["struggle_stats"] = workflow.get_struggle_stats()
    
    yield f"data: {json.dumps(completion_data)}\n\n"
