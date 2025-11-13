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
        
        # Track Stage 4 flow per stream (not globally)
        stage4_tools_executed = False
        stage4_chunks_seen = []
        
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
                
                # Track Stage 4 flow
                if str(stage).startswith("4"):
                    stage4_chunks_seen.append(node_name)
                    if node_name == "tools":
                        stage4_tools_executed = True
                    
                    logger.info(f"Stage {stage} stream chunk - node: {node_name}, output_keys: {list(node_output.keys()) if isinstance(node_output, dict) else 'not_dict'}, tools_executed: {stage4_tools_executed}")
                
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
                
                # Stage 4 built-in supervisor nodes (create_supervisor uses different names)
                elif node_name == "supervisor":
                    # Stage 4.1 built-in supervisor node
                    async for event in _handle_supervisor_node(node_output, stage):
                        yield event
                elif node_name in ["order_operations", "product_inventory", "customer_account"]:
                    # Stage 4.1 built-in specialist nodes
                    for event in _handle_specialist_node(node_name, node_output, stage):
                        yield event
                
                # Stage 4 custom supervisor nodes (create_react_agent uses agent/tools)
                elif node_name == "agent":
                    if str(stage).startswith("4"):
                        # Pass tools execution state to handler
                        async for event in _handle_stage4_agent_node(node_output, stage, stage4_tools_executed):
                            yield event
                    else:
                        # Regular Stage 1/2 agent handling
                        async for event in _handle_agent_node(node_output, stage, workflow):
                            yield event
                elif node_name == "tools":
                    if str(stage).startswith("4"):
                        # Stage 4: Show specialist delegations in thought process
                        for event in _handle_stage4_tools_node(node_output, stage):
                            yield event
                    else:
                        # Regular Stage 1/2 tools handling
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



async def _handle_supervisor_node(node_output: dict, stage: Union[int, float]) -> AsyncGenerator[str, None]:
    """Handle Stage 4 built-in supervisor node output."""
    global _stage4_builtin_final_response_started
    
    # Handle case where node_output might be None (coordination phase)
    if not node_output or not isinstance(node_output, dict):
        logger.info(f"Stage 4 supervisor node - coordination phase (empty output)")
        return
        
    messages = node_output.get("messages", [])
    
    if not messages:
        return
    
    msg = messages[-1]
    
    # Check if supervisor is delegating to specialists
    if hasattr(msg, "tool_calls") and msg.tool_calls:
        for tool_call in msg.tool_calls:
            # Extract specialist consultation info
            specialist_name = tool_call["name"]
            args = tool_call.get("args", {})
            
            event_data = {
                "type": "thought",
                "node": "supervisor",
                "content": f"Delegating to specialist: {tool_call['name']}",
                "tool_call": {
                    "name": specialist_name,
                    "args": args
                },
                "stage": stage
            }
            yield f"data: {json.dumps(event_data)}\n\n"
    
    # Handle supervisor responses - stream substantial content
    elif msg.content and len(msg.content.strip()) > 20:  # Only filter very short responses
        logger.info(f"Streaming Stage 4 supervisor response: {msg.content[:100]}...")
        
        yield f"data: {json.dumps({'type': 'response_start'})}\n\n"
        
        # Stream word-by-word
        words = msg.content.split(' ')
        for i, word in enumerate(words):
            word_with_space = word + (' ' if i < len(words) - 1 else '')
            event_data = {
                "type": "response_chunk",
                "node": "supervisor",
                "content": word_with_space,
                "word_index": i,
                "total_words": len(words)
            }
            yield f"data: {json.dumps(event_data)}\n\n"
            await asyncio.sleep(0.05)
        
        yield f"data: {json.dumps({'type': 'response_complete', 'stage': stage})}\n\n"


def _handle_specialist_node(specialist_name: str, node_output: dict, stage: Union[int, float]) -> Generator[str, None, None]:
    """Handle Stage 4 specialist node output with detailed interaction info."""
    # Handle case where node_output might be None
    if not node_output or not isinstance(node_output, dict):
        logger.info(f"Stage 4 specialist {specialist_name} - empty or invalid output: {type(node_output)}")
        return
        
    messages = node_output.get("messages", [])
    
    if not messages:
        return
    
    msg = messages[-1]
    
    # Format specialist name for display
    display_name = specialist_name.replace('_', ' ').title()
    specialist_emoji = {"order_operations": "📦", "product_inventory": "🛍️", "customer_account": "👤"}.get(specialist_name, "🤖")
    
    # Check if specialist is using tools
    if hasattr(msg, "tool_calls") and msg.tool_calls:
        for tool_call in msg.tool_calls:
            # Extract meaningful info from tool arguments
            tool_name = tool_call['name']
            args = tool_call.get('args', {})
            
            # Format tool arguments for better understanding
            args_summary = ""
            if tool_name == "get_order_status" and "order_id" in args:
                args_summary = f"for order #{args['order_id']}"
            elif tool_name == "check_inventory" and "product" in args:
                product = args.get('product', 'item')
                color = args.get('color', '')
                args_summary = f"for {product}" + (f" in {color}" if color else "")
            elif tool_name == "search_faq" and "query" in args:
                query = args['query'][:50] + "..." if len(args['query']) > 50 else args['query']
                args_summary = f'for "{query}"'
            
            event_data = {
                "type": "observation",
                "node": "specialist",
                "content": f"{specialist_emoji} {display_name}: Using {tool_name} {args_summary}",
                "specialist": specialist_name,
                "tool_call": {
                    "name": tool_call["name"],
                    "args": tool_call["args"]
                },
                "stage": stage
            }
            yield f"data: {json.dumps(event_data)}\n\n"
    
    # Check if specialist is providing response back to supervisor
    elif msg.content:
        # Show detailed response with key findings
        content_preview = msg.content
        
        # Extract key information for summary
        if "delivered" in content_preview.lower():
            key_info = "Order delivered"
        elif "in stock" in content_preview.lower() or "available" in content_preview.lower():
            key_info = "Product availability checked"
        elif "faq" in content_preview.lower() or "policy" in content_preview.lower():
            key_info = "Policy information found"
        else:
            key_info = "Analysis completed"
        
        # Show both summary and preview
        event_data = {
            "type": "observation", 
            "node": "specialist",
            "content": f"{specialist_emoji} {display_name}: {key_info}",
            "specialist": specialist_name,
            "response_detail": content_preview[:200] + "..." if len(content_preview) > 200 else content_preview,
            "stage": stage
        }
        yield f"data: {json.dumps(event_data)}\n\n"



async def _handle_stage4_agent_node(node_output: dict, stage: Union[int, float], tools_executed: bool) -> AsyncGenerator[str, None]:
    """Handle Stage 4 supervisor agent node output."""
    # Handle case where node_output might be None
    if not node_output or not isinstance(node_output, dict):
        logger.info(f"Stage 4 custom agent node - empty or invalid output: {type(node_output)}")
        return
        
    messages = node_output.get("messages", [])
    
    if not messages:
        return
    
    msg = messages[-1]
    
    # Check if supervisor is delegating to specialists
    if hasattr(msg, "tool_calls") and msg.tool_calls:
        # This is delegation phase
        for tool_call in msg.tool_calls:
            event_data = {
                "type": "thought",
                "node": "agent",
                "content": f"Delegating to specialist: {tool_call['name']}",
                "tool_call": {
                    "name": tool_call["name"],
                    "args": tool_call.get("args", {})
                },
                "stage": stage
            }
            yield f"data: {json.dumps(event_data)}\n\n"
    
    # Handle final supervisor response (after specialists have executed) 
    elif msg.content and tools_executed:
        # For Stage 4, always stream the response after tools have executed
        # (The supervisor may have tool_calls in message history but not be making new calls)
        logger.info(f"Streaming Stage 4 supervisor response (after specialists completed): {msg.content[:100]}...")
        
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
        
        yield f"data: {json.dumps({'type': 'response_complete', 'stage': stage})}\n\n"
    else:
        # Log skipped responses for debugging
        logger.info(f"Stage 4 agent - skipping response (tools_executed: {tools_executed}, has_content: {bool(msg.content)}, has_tool_calls: {hasattr(msg, 'tool_calls')})")


def _handle_stage4_tools_node(node_output: dict, stage: Union[int, float]) -> Generator[str, None, None]:
    """Handle Stage 4 specialist tools node output."""
    # Handle case where node_output might be None
    if not node_output or not isinstance(node_output, dict):
        logger.info(f"Stage 4 tools node - empty or invalid output: {type(node_output)}")
        return
        
    messages = node_output.get("messages", [])
    
    if not messages:
        return
    
    # For Stage 4, tools node contains specialist responses
    # Show these as specialist completions, not detailed responses
    for msg in messages:
        if hasattr(msg, "content") and hasattr(msg, "name"):
            tool_name = msg.name
            specialist_name = tool_name.replace('specialist_', '').replace('transfer_to_', '')
            display_name = specialist_name.replace('_', ' ').title()
            
            event_data = {
                "type": "observation",
                "node": "tools", 
                "content": f"✅ {display_name} specialist completed analysis",
                "specialist": specialist_name,
                "stage": stage
            }
            yield f"data: {json.dumps(event_data)}\n\n"


def _send_completion_event(stage: Union[int, float], workflow) -> Generator[str, None, None]:
    """Send completion event with optional struggle stats."""
    completion_data = {"type": "done", "stage": stage}
    
    # Add struggle stats for Stage 2
    if str(stage) == "2" and hasattr(workflow, 'get_struggle_stats'):
        completion_data["struggle_stats"] = workflow.get_struggle_stats()
    
    yield f"data: {json.dumps(completion_data)}\n\n"
