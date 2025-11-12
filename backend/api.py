"""
Unified FastAPI backend for all stages.
Clean, modular implementation with separated concerns.
"""
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from common.config import config
from common.logging_config import get_logger, setup_logging
from backend.models import ChatRequest, ChatResponse
from backend.workflow_loader import load_workflow, get_current_stage, get_workflow, workflows
from backend.streaming import stream_agent_response
from backend.response_handler import extract_response
from backend.session_manager import get_session_manager

# Setup logging
setup_logging(log_level=config.LOG_LEVEL)
logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Customer Support Agent API - Unified",
    description="Configurable backend supporting all stages with multiple patterns",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize with configured stage from environment."""
    try:
        stage_num = config.STAGE
        load_workflow(stage_num)
        logger.info(f"API ready - loaded Stage {stage_num}")
    except Exception as e:
        logger.error(f"API startup error: {str(e)}")
        raise


@app.get("/health")
async def health_check():
    """Detailed health check."""
    stage = get_current_stage()
    workflow = get_workflow()
    
    health_info = {
        "status": "healthy",
        "stage": stage,
        "available_stages": [1, 2, 3.1, 3.2, 3.3],
        "workflow_initialized": workflow is not None,
        "default_model": f"{config.DEFAULT_MODEL_TYPE}:{config.DEFAULT_MODEL_NAME}",
        "tools_count": len(workflow.agent.tools) if workflow else 0
    }
    
    # Add struggle stats for Stage 2
    if stage == 2 and workflow and hasattr(workflow, 'get_struggle_stats'):
        health_info["struggle_stats"] = workflow.get_struggle_stats()
    
    return health_info


@app.post("/stage/{stage_num}")
async def switch_stage(stage_num: float):
    """Switch to a different stage."""
    try:
        workflow = load_workflow(stage_num)
        return {
            "message": f"Switched to Stage {stage_num}",
            "stage": stage_num,
            "tools_count": len(workflow.agent.tools),
            "default_model": f"{config.DEFAULT_MODEL_TYPE}:{config.DEFAULT_MODEL_NAME}"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/tools")
async def list_tools(stage_param: float = Query(None, description="Stage to get tools for")):
    """List available tools for the specified stage."""
    target_stage = stage_param or get_current_stage() or 1
    workflow = load_workflow(target_stage)
    
    tools_info = []
    for tool in workflow.agent.tools:
        if hasattr(tool, 'name'):
            # Tool is an object with name and description attributes
            tools_info.append({
                "name": tool.name,
                "description": getattr(tool, 'description', 'No description available')
            })
        elif isinstance(tool, str):
            # Tool is just a string name
            tools_info.append({
                "name": tool,
                "description": "No description available"
            })
        else:
            # Try to get string representation
            tools_info.append({
                "name": str(tool),
                "description": "No description available"
            })
    
    return {
        "tools": tools_info,
        "total_count": len(tools_info),
        "stage": target_stage
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
            },
            3.1: {
                "name": "ReWOO - Reasoning Without Observation",
                "tools_count": 7,
                "description": "Plans all steps upfront, then executes - only 2 LLM calls vs N+1"
            },
            3.2: {
                "name": "Reflection - Self-Critique Pattern",
                "tools_count": 7,
                "description": "Coming soon - Agent reflects on and improves its outputs"
            },
            3.3: {
                "name": "Plan-and-Execute - Hierarchical Planning",
                "tools_count": 7,
                "description": "Coming soon - Separates planning from execution"
            }
        },
        "current_stage": get_current_stage()
    }


@app.post("/checkpointing/{enabled}")
async def toggle_checkpointing(enabled: bool):
    """Enable or disable checkpointing and restart workflow."""
    try:
        current_stage = get_current_stage()
        
        # Check if current workflow supports checkpointing (inherits from BaseWorkflow)
        current_workflow = get_workflow(current_stage)
        stage_supports_checkpointing = hasattr(current_workflow, 'enable_checkpointing')
        
        if enabled and not stage_supports_checkpointing:
            return {
                "message": f"Stage {current_stage} does not support checkpointing. Switch to Stage 2+ to use checkpointing features.",
                "checkpointing_enabled": False,
                "stage": current_stage,
                "workflow_reloaded": False,
                "has_checkpointer": False,
                "error": "Stage not compatible with checkpointing"
            }
        
        # Update config temporarily (not persistent)
        from common.config import config
        config.ENABLE_CHECKPOINTING = enabled
        
        # Force reload workflow with new checkpointing setting by clearing cache
        workflows.pop(current_stage, None)
        workflow = load_workflow(current_stage)
        
        return {
            "message": f"Checkpointing {'enabled' if enabled else 'disabled'} for Stage {current_stage}",
            "checkpointing_enabled": enabled,
            "stage": current_stage,
            "workflow_reloaded": True,
            "has_checkpointer": hasattr(workflow, 'checkpointer') and workflow.checkpointer is not None,
            "stage_supports_checkpointing": stage_supports_checkpointing
        }
    except Exception as e:
        logger.error(f"Error toggling checkpointing: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/checkpointing/status")
async def get_checkpointing_status():
    """Get current checkpointing status."""
    workflow = get_workflow()
    current_stage_num = get_current_stage()
    stage_supports_checkpointing = hasattr(workflow, 'enable_checkpointing') if workflow else False
    
    return {
        "checkpointing_enabled": config.ENABLE_CHECKPOINTING,
        "workflow_has_checkpointer": hasattr(workflow, 'checkpointer') and workflow.checkpointer is not None if workflow else False,
        "workflow_supports_checkpointing": stage_supports_checkpointing,
        "stage_supports_checkpointing": stage_supports_checkpointing,
        "current_stage": current_stage_num,
        "workflow_type": type(workflow).__name__ if workflow else "None"
    }


@app.get("/checkpoint/history/{thread_id}")
async def get_checkpoint_history(thread_id: str, limit: int = Query(10, description="Max checkpoints to return")):
    """
    Get checkpoint history for a thread (requires checkpointing enabled).
    
    Args:
        thread_id: Thread identifier
        limit: Maximum number of checkpoints to return
        
    Returns:
        List of checkpoints with metadata
    """
    workflow = get_workflow()
    
    if not workflow:
        raise HTTPException(status_code=503, detail="Workflow not initialized")
    
    if not workflow.enable_checkpointing:
        raise HTTPException(status_code=400, detail="Checkpointing not enabled")
    
    try:
        history = workflow.get_state_history(thread_id, limit=limit)
        
        # Format checkpoints for frontend
        checkpoints = []
        for i, checkpoint in enumerate(history):
            checkpoint_data = {
                "index": i,
                "checkpoint_id": checkpoint.config.get("configurable", {}).get("checkpoint_id"),
                "step": checkpoint.metadata.get("step", "unknown"),
                "next_nodes": list(checkpoint.next) if checkpoint.next else [],
                "created_at": checkpoint.created_at,
                "has_plan": "plan_string" in checkpoint.values,
                "evidence_count": len(checkpoint.values.get("results", {})),
                "message_count": len(checkpoint.values.get("messages", []))
            }
            checkpoints.append(checkpoint_data)
        
        return {
            "thread_id": thread_id,
            "checkpoint_count": len(checkpoints),
            "checkpoints": checkpoints
        }
        
    except Exception as e:
        logger.error(f"Error getting checkpoint history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/checkpoint/reset/{thread_id}/{checkpoint_id}")
async def reset_to_checkpoint(thread_id: str, checkpoint_id: str):
    """
    Jump to a specific checkpoint state for debugging.
    
    Loads the checkpoint's state so the agent continues from that point.
    Note: Checkpoint history is preserved (not deleted) for inspection.
    
    Args:
        thread_id: Thread identifier
        checkpoint_id: Checkpoint to jump to
        
    Returns:
        Confirmation with checkpoint details
    """
    workflow = get_workflow()
    
    if not workflow:
        raise HTTPException(status_code=503, detail="Workflow not initialized")
    
    if not workflow.enable_checkpointing:
        raise HTTPException(status_code=400, detail="Checkpointing not enabled")
    
    try:
        # Create config with both thread_id and checkpoint_id
        config = {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_id": checkpoint_id,
                "checkpoint_ns": ""
            }
        }
        
        target_state = workflow.workflow.get_state(config)
        
        if not target_state:
            raise HTTPException(status_code=404, detail="Checkpoint not found")
        
        # Update state to the target checkpoint values
        # This effectively truncates history by resetting to that point
        workflow.workflow.update_state(config, target_state.values)
        
        return {
            "message": f"Reset thread {thread_id} to checkpoint {checkpoint_id}",
            "checkpoint_id": checkpoint_id,
            "step": target_state.metadata.get("step", "unknown"),
            "thread_id": thread_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting checkpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat")
async def chat(request: ChatRequest, stage_param: float = Query(None, description="Override stage")):
    """
    Chat with the customer support agent.
    
    Args:
        request: ChatRequest with message and stream flag
        stage_param: Optional stage override (1, 2, 3.1, 3.2, 3.3)
        
    Returns:
        StreamingResponse if stream=True, ChatResponse otherwise
    """
    # Determine which stage to use
    target_stage = stage_param or request.stage or get_current_stage() or 1
    
    # Load appropriate workflow
    workflow = load_workflow(target_stage)
    
    logger.info(f"Chat request - stage: {target_stage}, message: '{request.message[:100]}...', stream: {request.stream}")
    
    # Get or create thread_id for session (enables checkpointing memory)
    session_manager = get_session_manager()
    session_id, thread_id = session_manager.get_or_create_thread_id(request.session_id)
    
    if request.stream:
        return StreamingResponse(
            stream_agent_response(request.message, target_stage, thread_id),
            media_type="text/event-stream"
        )
    else:
        try:
            result = workflow.invoke(request.message, thread_id=thread_id)
            
            # Extract response using helper
            final_response, thought_process = extract_response(result, target_stage)
            
            # Prepare response data
            response_data = {
                "response": final_response,
                "thought_process": thought_process,
                "stage": target_stage,
                "thread_id": thread_id
            }
            
            # Add struggle stats for Stage 2
            if target_stage == 2 and hasattr(workflow, 'get_struggle_stats'):
                response_data["struggle_stats"] = result.get("struggle_stats", {})
            
            return ChatResponse(**response_data)
            
        except Exception as e:
            logger.error(f"Chat error: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    
    # Load stage from config
    load_workflow(config.STAGE)
    
    uvicorn.run(
        app,
        host=config.BACKEND_HOST,
        port=config.BACKEND_PORT,
        log_level=config.LOG_LEVEL.lower()
    )
