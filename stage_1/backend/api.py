"""
FastAPI backend for the customer support agent.
Provides REST API endpoints with streaming support and thought process tracking.
"""

import json
import sys
from pathlib import Path
from typing import AsyncGenerator
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from stage_1.agents.workflow import AgentWorkflow
from common.config import config
from common.logging_config import get_logger, setup_logging

# Setup logging
setup_logging(log_level=config.LOG_LEVEL)
logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Customer Support Agent API",
    description="Stage 1: Simple ReAct Agent for Customer Support",
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

# Global workflow instance
workflow: AgentWorkflow = None


@app.on_event("startup")
async def startup_event():
    """Initialize the agent workflow on startup."""
    global workflow
    
    logger.info(f"API starting with model_type: {config.MODEL_TYPE}")
    
    try:
        # Use MODEL_TYPE from config (can be overridden by .env)
        workflow = AgentWorkflow()  # Uses config.MODEL_TYPE by default
        logger.info(f"API ready with model_type: {config.MODEL_TYPE}")
    except Exception as e:
        logger.error(f"API startup error: {str(e)}")
        raise


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "online",
        "service": "Customer Support Agent",
        "stage": "1",
        "description": "Simple ReAct Agent with Order Lookup and FAQ Retrieval"
    }


@app.get("/health")
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "workflow_initialized": workflow is not None,
        "model_type": workflow.model_type if workflow else None
    }


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str
    stream: bool = True


class ChatResponse(BaseModel):
    """Response model for non-streaming chat."""
    response: str
    thought_process: list


@app.post("/chat")
async def chat(request: ChatRequest):
    """
    Chat with the customer support agent.
    
    Args:
        request: ChatRequest with message and stream flag
        
    Returns:
        StreamingResponse if stream=True, ChatResponse otherwise
    """
    if not workflow:
        raise HTTPException(status_code=503, detail="Agent workflow not initialized")
    
    logger.info(f"Chat request - message: '{request.message[:100]}...', stream: {request.stream}")
    
    if request.stream:
        # Return streaming response
        return StreamingResponse(
            stream_agent_response(request.message),
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
            
            return ChatResponse(
                response=final_response,
                thought_process=thought_process
            )
            
        except Exception as e:
            logger.error(f"Chat error: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))


async def stream_agent_response(message: str) -> AsyncGenerator[str, None]:
    """
    Stream agent response with thought process.
    
    Args:
        message: User's message
        
    Yields:
        Server-Sent Events formatted data
    """
    try:
        # Initialize workflow if not already done (for testing)
        global workflow
        if workflow is None:
            workflow = AgentWorkflow()
        
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
                                    }
                                }
                                yield f"data: {json.dumps(event_data)}\n\n"
                        
                        # Check if agent is providing final response
                        elif msg.content:
                            # Stream response word-by-word
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
                                
                                # Small delay for realistic typing effect (optional)
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
                                    "full_length": len(msg.content)
                                }
                                yield f"data: {json.dumps(event_data)}\n\n"
        
        # Send completion event
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
        
    except Exception as e:
        logger.error(f"Stream error: {str(e)}")
        error_event = {
            "type": "error",
            "content": str(e)
        }
        yield f"data: {json.dumps(error_event)}\n\n"


@app.get("/tools")
async def list_tools():
    """List available tools."""
    if not workflow:
        raise HTTPException(status_code=503, detail="Agent workflow not initialized")
    
    tools_info = []
    for tool in workflow.agent.tools:
        tools_info.append({
            "name": tool.name,
            "description": tool.description
        })
    
    return {"tools": tools_info}


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app,
        host=config.BACKEND_HOST,
        port=config.BACKEND_PORT,
        log_level=config.LOG_LEVEL.lower()
    )
