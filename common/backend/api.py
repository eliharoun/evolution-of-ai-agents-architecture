"""
Unified FastAPI backend for all stages.
Dynamically selects and loads the appropriate workflow based on configuration.
"""

import json
import sys
from pathlib import Path
from typing import AsyncGenerator, Union
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from common.config import config
from common.logging_config import get_logger, setup_logging

# Setup logging
setup_logging(log_level=config.LOG_LEVEL)
logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Customer Support Agent API - Unified",
    description="Configurable backend supporting all stages",
    version="1.0.0"
)

# Add CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global workflow instances
workflows = {}
current_stage = None


def load_workflow(stage: int):
    """
    Dynamically load the appropriate workflow for the given stage.
    
    Args:
        stage: Stage number (1 or 2)
        
    Returns:
        AgentWorkflow instance for the specified stage
    """
    global current_stage
    
    if stage in workflows and current_stage == stage:
        return workflows[stage]
    
    logger.info(f"Loading Stage {stage} workflow with model_type: {config.MODEL_TYPE}")
    
    try:
        if stage == 1:
            from stage_1.agents.workflow import AgentWorkflow
            workflow = AgentWorkflow()
            logger.info(f"Stage 1 workflow loaded - tools: {len(workflow.agent.tools)}")
            
        elif stage == 2:
            from stage_2.agents.workflow import AgentWorkflow
            workflow = AgentWorkflow()
            logger.info(f"Stage 2 workflow loaded - tools: {len(workflow.agent.tools)}")
            
        else:
            raise ValueError(f"Unsupported stage: {stage}. Available: 1, 2")
        
        workflows[stage] = workflow
        current_stage = stage
        return workflow
        
    except Exception as e:
        logger.error(f"Failed to load Stage {stage} workflow: {str(e)}")
        raise


@app.on_event("startup")
async def startup_event():
    """Initialize with default stage."""
    try:
        # Load default stage (Stage 1)
        load_workflow(1)
        logger.info("Unified API ready - default: Stage 1")
    except Exception as e:
        logger.error(f"API startup error: {str(e)}")
        raise


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "online",
        "service": "Customer Support Agent - Unified Backend",
        "current_stage": current_stage,
        "available_stages": [1, 2],
        "model_type": config.MODEL_TYPE
    }


@app.get("/health")
async def health_check():
    """Detailed health check."""
    workflow = workflows.get(current_stage) if current_stage else None
    
    health_info = {
        "status": "healthy",
        "current_stage": current_stage,
        "available_stages": [1, 2],
        "workflow_initialized": workflow is not None,
        "model_type": workflow.model_type if workflow else None,
        "tools_count": len(workflow.agent.tools) if workflow else 0
    }
    
    # Add struggle stats for Stage 2
    if current_stage == 2 and workflow and hasattr(workflow, 'get_struggle_stats'):
        health_info["struggle_stats"] = workflow.get_struggle_stats()
    
    return health_info


@app.post("/stage/{stage_num}")
async def switch_stage(stage_num: int):
    """Switch to a different stage."""
    try:
        workflow = load_workflow(stage_num)
        return {
            "message": f"Switched to Stage {stage_num}",
            "stage": stage_num,
            "tools_count": len(workflow.agent.tools),
            "model_type": workflow.model_type
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/struggles")
async def get_struggle_stats():
    """Get current struggle statistics (Stage 2 only)."""
    if current_stage != 2:
        return {"message": f"Struggle stats only available for Stage 2 (current: Stage {current_stage})"}
    
    workflow = workflows.get(2)
    if not workflow or not hasattr(workflow, 'get_struggle_stats'):
        raise HTTPException(status_code=503, detail="Stage 2 workflow not initialized")
    
    return {
        "struggle_stats": workflow.get_struggle_stats(),
        "description": {
            "high_iterations": "Agent took many iterations to complete task",
            "tool_confusion_events": "Agent used conflicting tools simultaneously", 
            "sequential_bottlenecks": "Agent processed sequentially instead of in parallel",
            "context_loss_events": "Agent repeated previous actions, forgetting context"
        }
    }


@app.post("/struggles/reset")
async def reset_struggle_stats():
    """Reset struggle statistics (Stage 2 only)."""
    if current_stage != 2:
        return {"message": f"Struggle stats only available for Stage 2 (current: Stage {current_stage})"}
    
    workflow = workflows.get(2)
    if not workflow or not hasattr(workflow, 'reset_struggle_stats'):
        raise HTTPException(status_code=503, detail="Stage 2 workflow not initialized")
    
    workflow.reset_struggle_stats()
    return {"message": "Struggle statistics reset successfully"}


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str
    stream: bool = True
    stage: int = None  # Optional stage override


class ChatResponse(BaseModel):
    """Response model for non-streaming chat."""
    response: str
    thought_process: list
    stage: int
    struggle_stats: dict = None


@app.post("/chat")
async def chat(request: ChatRequest, stage: int = Query(None, description="Override stage for this request")):
    """
    Chat with the customer support agent.
    
    Args:
        request: ChatRequest with message and stream flag
        stage: Optional stage override (1 or 2)
        
    Returns:
        StreamingResponse if stream=True, ChatResponse otherwise
    """
    # Determine which stage to use
    target_stage = stage or request.stage or current_stage or 1
    
    # Load appropriate workflow
    workflow = load_workflow(target_stage)
    
    logger.info(f"Chat request - stage: {target_stage}, message: '{request.message[:100]}...', stream: {request.stream}")
    
    if request.stream:
        # Return streaming response
        return StreamingResponse(
            stream_agent_response(request.message, target_stage),
            media_type="text/event-stream"
        )
    else:
        # Return complete response
        try:
            result = workflow.invoke(request.message)
            
            # Extract final response
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
            
            # Prepare response
            response_data = {
                "response": final_response,
                "thought_process": thought_process,
                "stage": target_stage
            }
            
            # Add struggle stats for Stage 2
            if target_stage == 2 and hasattr(workflow, 'get_struggle_stats'):
                response_data["struggle_stats"] = result.get("struggle_stats", {})
            
            return ChatResponse(**response_data)
            
        except Exception as e:
            logger.error(f"Chat error: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))


async def stream_agent_response(message: str, stage: int) -> AsyncGenerator[str, None]:
    """
    Stream agent response with stage-specific handling.
    
    Args:
        message: User's message
        stage: Stage number (1 or 2)
        
    Yields:
        Server-Sent Events formatted data
    """
    try:
        workflow = load_workflow(stage)
        
        for chunk in workflow.stream(message):
            # Parse the chunk from each node
            for node_name, node_output in chunk.items():
                
                if node_name == "agent":
                    # Agent node output
                    messages = node_output.get("messages", [])
                    
                    if messages:
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
                            # Stream response word-by-word (ChatGPT-style)
                            yield f"data: {json.dumps({'type': 'response_start'})}\n\n"
                            
                            # Split response into words for streaming
                            words = msg.content.split(' ')
                            for i, word in enumerate(words):
                                # Add space after word (except for last word)
                                word_with_space = word + (' ' if i < len(words) - 1 else '')
                                
                                event_data = {
                                    "type": "response_chunk",
                                    "node": "agent", 
                                    "content": word_with_space,
                                    "word_index": i,
                                    "total_words": len(words)
                                }
                                yield f"data: {json.dumps(event_data)}\n\n"
                                
                                # Small delay for realistic typing effect
                                import asyncio
                                await asyncio.sleep(0.05)  # 50ms delay between words
                            
                            # Signal response completion
                            yield f"data: {json.dumps({'type': 'response_complete'})}\n\n"
                
                elif node_name == "tools":
                    # Tools node output
                    messages = node_output.get("messages", [])
                    
                    if messages:
                        for msg in messages:
                            if hasattr(msg, "content"):
                                # Truncate long tool results for streaming
                                content = msg.content[:300] + "..." if len(msg.content) > 300 else msg.content
                                
                                event_data = {
                                    "type": "observation",
                                    "node": "tools",
                                    "content": content,
                                    "full_length": len(msg.content),
                                    "stage": stage
                                }
                                yield f"data: {json.dumps(event_data)}\n\n"
        
        # Send completion event
        completion_data = {"type": "done", "stage": stage}
        
        # Add struggle stats for Stage 2
        if stage == 2 and hasattr(workflow, 'get_struggle_stats'):
            completion_data["struggle_stats"] = workflow.get_struggle_stats()
        
        yield f"data: {json.dumps(completion_data)}\n\n"
        
    except Exception as e:
        logger.error(f"Stream error: {str(e)}")
        error_event = {
            "type": "error",
            "content": str(e)
        }
        yield f"data: {json.dumps(error_event)}\n\n"


@app.get("/tools")
async def list_tools(stage: int = Query(None, description="Stage to get tools for")):
    """List available tools for the specified stage."""
    target_stage = stage or current_stage or 1
    workflow = load_workflow(target_stage)
    
    tools_info = []
    for tool in workflow.agent.tools:
        tools_info.append({
            "name": tool.name,
            "description": tool.description
        })
    
    return {
        "tools": tools_info,
        "total_count": len(tools_info),
        "stage": target_stage,
        "note": f"Stage {target_stage} tools" + (f" (vs {len(workflows[1].agent.tools) if 1 in workflows else 2} in Stage 1)" if target_stage == 2 else "")
    }


@app.get("/stages")
async def list_stages():
    """List all available stages and their info."""
    return {
        "available_stages": {
            1: {
                "name": "Foundation - Simple ReAct Agent",
                "tools_count": 2,
                "description": "Basic ReAct agent with order lookup and FAQ search"
            },
            2: {
                "name": "Sophisticated Single Agent", 
                "tools_count": 7,
                "description": "Same ReAct agent with tool complexity that reveals limitations"
            }
        },
        "current_stage": current_stage
    }


if __name__ == "__main__":
    import os
    import uvicorn
    
    # Allow stage selection via environment
    stage = int(os.getenv("STAGE", "1"))
    load_workflow(stage)
    
    uvicorn.run(
        app,
        host=config.BACKEND_HOST,
        port=config.BACKEND_PORT,
        log_level=config.LOG_LEVEL.lower()
    )
