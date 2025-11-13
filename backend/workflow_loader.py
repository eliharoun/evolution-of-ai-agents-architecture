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


def load_workflow(stage_num: Union[int, float, str]):
    """
    Dynamically load the appropriate workflow for the given stage.
    
    Args:
        stage_num: Stage identifier (string, int, or float)
            - "1": Simple ReAct
            - "2": Sophisticated ReAct  
            - "3.1": ReWOO pattern
            - "3.2": Reflection pattern
            - "3.3": Plan-and-Execute pattern
            - "4.1.1": Supervisor 1 (built-in)
            - "4.1.2": Supervisor 2 (custom)
        
    Returns:
        Workflow instance for the specified stage
    """
    global current_stage
    
    # Convert to string for consistent comparison
    stage_str = str(stage_num)
    
    if stage_str in workflows and current_stage == stage_str:
        return workflows[stage_str]
    
    logger.info(f"Loading Stage {stage_str} workflow")
    
    try:
        if stage_str in ["1", "1.0"]:
            from stage_1.agents.workflow import AgentWorkflow
            workflow = AgentWorkflow()
            logger.info(f"Stage 1 workflow loaded - tools: {len(workflow.agent.tools)}")
            
        elif stage_str in ["2", "2.0"]:
            from stage_2.agents.workflow import AgentWorkflow
            workflow = AgentWorkflow()
            logger.info(f"Stage 2 workflow loaded - tools: {len(workflow.agent.tools)}")
            
        elif stage_str == "3.1":
            from stage_3.agents.rewoo.workflow import ReWOOWorkflow
            workflow = ReWOOWorkflow()
            logger.info(f"Stage 3.1 (ReWOO) workflow loaded - tools: {len(workflow.agent.tools)}")
            
        elif stage_str == "3.2":
            raise ValueError(f"Stage 3.2 (Reflection) not yet implemented")
            
        elif stage_str == "3.3":
            raise ValueError(f"Stage 3.3 (Plan-and-Execute) not yet implemented")
            
        elif stage_str in ["4.11", "4.1.1"]:
            # Stage 4.1.1: Supervisor 1 (built-in create_supervisor)
            from stage_4.supervisor_1.agents.workflow import SupervisorWorkflow
            workflow = SupervisorWorkflow()
            logger.info(f"Stage 4.1.1 (Supervisor 1 - Built-in) workflow loaded - specialists: {len(workflow.specialists)}")
            
        elif stage_str in ["4.12", "4.1.2"]:
            # Stage 4.1.2: Supervisor 2 (custom implementation)
            from stage_4.supervisor_2.agents.workflow import CustomSupervisorWorkflow
            workflow = CustomSupervisorWorkflow()
            logger.info(f"Stage 4.1.2 (Supervisor 2 - Custom) workflow loaded - specialist tools: {len(workflow.specialist_tools)}")
            
        else:
            raise ValueError(f"Unsupported stage: {stage_str}. Available: 1, 2, 3.1, 3.2 (coming soon), 3.3 (coming soon), 4.1.1 (Supervisor 1), 4.1.2 (Supervisor 2)")
        
        workflows[stage_str] = workflow
        current_stage = stage_str
        return workflow
        
    except Exception as e:
        logger.error(f"Failed to load Stage {stage_num} workflow: {str(e)}")
        raise


def get_current_stage() -> Union[str, None]:
    """Get the currently loaded stage identifier."""
    return current_stage


def get_workflow(stage_num: Union[int, float, str] = None):
    """
    Get a workflow instance.
    
    Args:
        stage_num: Stage identifier (if None, returns current workflow)
        
    Returns:
        Workflow instance or None if not loaded
    """
    if stage_num is None:
        return workflows.get(current_stage)
    return workflows.get(str(stage_num))
