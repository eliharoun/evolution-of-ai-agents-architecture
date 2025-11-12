"""
Workflow loader for dynamically loading stage-specific workflows.
"""
from typing import Union

from common.config import config
from common.logging_config import get_logger

logger = get_logger(__name__)

# Global workflow instances
workflows = {}
current_stage = None


def load_workflow(stage_num: Union[int, float]):
    """
    Dynamically load the appropriate workflow for the given stage.
    
    Args:
        stage_num: Stage number
            - 1: Simple ReAct
            - 2: Sophisticated ReAct  
            - 3.1: ReWOO pattern
            - 3.2: Reflection pattern
            - 3.3: Plan-and-Execute pattern
        
    Returns:
        Workflow instance for the specified stage
    """
    global current_stage
    
    if stage_num in workflows and current_stage == stage_num:
        return workflows[stage_num]
    
    logger.info(f"Loading Stage {stage_num} workflow")
    
    try:
        if stage_num == 1:
            from stage_1.agents.workflow import AgentWorkflow
            workflow = AgentWorkflow()
            logger.info(f"Stage 1 workflow loaded - tools: {len(workflow.agent.tools)}")
            
        elif stage_num == 2:
            from stage_2.agents.workflow import AgentWorkflow
            workflow = AgentWorkflow()
            logger.info(f"Stage 2 workflow loaded - tools: {len(workflow.agent.tools)}")
            
        elif stage_num == 3.1:
            from stage_3.agents.rewoo.workflow import ReWOOWorkflow
            workflow = ReWOOWorkflow()
            logger.info(f"Stage 3.1 (ReWOO) workflow loaded - tools: {len(workflow.agent.tools)}")
            
        elif stage_num == 3.2:
            raise ValueError(f"Stage 3.2 (Reflection) not yet implemented")
            
        elif stage_num == 3.3:
            raise ValueError(f"Stage 3.3 (Plan-and-Execute) not yet implemented")
            
        else:
            raise ValueError(f"Unsupported stage: {stage_num}. Available: 1, 2, 3.1, 3.2 (coming soon), 3.3 (coming soon)")
        
        workflows[stage_num] = workflow
        current_stage = stage_num
        return workflow
        
    except Exception as e:
        logger.error(f"Failed to load Stage {stage_num} workflow: {str(e)}")
        raise


def get_current_stage() -> Union[int, float, None]:
    """Get the currently loaded stage number."""
    return current_stage


def get_workflow(stage_num: Union[int, float] = None):
    """
    Get a workflow instance.
    
    Args:
        stage_num: Stage number (if None, returns current workflow)
        
    Returns:
        Workflow instance or None if not loaded
    """
    if stage_num is None:
        stage_num = current_stage
    return workflows.get(stage_num)
