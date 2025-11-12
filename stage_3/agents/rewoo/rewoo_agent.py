"""
ReWOO Agent Implementation.

ReWOO = Reasoning Without Observation
- Planner: Creates complete plan upfront with placeholders (#E1, #E2, etc.)
- Worker: Executes tools with variable substitution
- Solver: Integrates all evidence into final answer
"""
import re
from typing import Dict, Optional

from langchain_core.prompts import ChatPromptTemplate

from common.model_factory import ModelFactory, ModelType
from common.tools import (
    get_order_status,
    search_faq,
    get_customer_account,
    process_refund,
    modify_shipping,
    check_inventory,
    create_ticket
)
from stage_3.agents.rewoo.utils.tool_invocation import invoke_tool_with_params

from common.config import config
from common.logging_config import get_logger, setup_logging

from stage_3.agents.rewoo.state import ReWOOState
from stage_3.agents.rewoo.utils.rewoo_prompts import PLANNER_PROMPT, SOLVER_PROMPT

# Setup logging
setup_logging(log_level=config.LOG_LEVEL)
logger = get_logger(__name__)

class ReWOOAgent:
    """
    ReWOO (Reasoning Without Observation) agent.
    
    Three main components:
    1. Planner: Creates complete plan with placeholders
    2. Worker: Executes tools with variable substitution
    3. Solver: Integrates evidence for final answer
    """

    # Regex pattern to parse plan steps
    REGEX_PATTERN = r"Plan:\s*(.+)\s*(#E\d+)\s*=\s*(\w+)\s*\[([^\]]+)\]"
    
    def __init__(self, planner_model_type: ModelType, planner_model_name: str, solver_model_type: ModelType, solver_model_name: str):
        """Initialize ReWOO agent with model and tools."""
        self.planner_model = ModelFactory.create_model(planner_model_type, planner_model_name)
        self.solver_model = ModelFactory.create_model(solver_model_type, solver_model_name)
        
        # Initialize tools
        self.tools = {
            'OrderStatus': get_order_status,
            'SearchFAQ': search_faq,
            'CustomerAccount': get_customer_account,
            'ProcessRefund': process_refund,
            'ModifyShipping': modify_shipping,
            'CheckInventory': check_inventory,
            'CreateTicket': create_ticket,
        }
        
        # Create planner chain
        planner_prompt_template = ChatPromptTemplate.from_messages([
            ("user", PLANNER_PROMPT)
        ])

        # Create a pipeline that takes a prompt template, sends it through a model, and returns a response
        self.planner = planner_prompt_template | self.planner_model
    
    def get_plan(self, state: ReWOOState) -> Dict:
        """
        Planner node: Generate complete plan with tool placeholders.
        
        Args:
            state: Current ReWOO state with task
            
        Returns:
            Dict with 'steps' and 'plan_string' updates
        """
        task = state["task"]
        result = self.planner.invoke({"task": task})
        
        # Parse plan using regex to extract steps
        matches = re.findall(self.REGEX_PATTERN, result.content)
        
        # Example Matches (ie. steps) for User query "What's the status of order #12345? If delivered, can I still return it?"
        # [
        #     {
        #         "description": "Check the current status of order #12345.",
        #         "step_name": "#E1",
        #         "tool": "OrderStatus",
        #         "tool_input": "12345"
        #     },
        #     {
        #         "description": "Analyze the order status to determine if it has been delivered.",
        #         "step_name": "#E2",
        #         "tool": "LLM",
        #         "tool_input": "Is order #12345 delivered based on #E1?"
        #     },
        #     {
        #         "description": "If delivered, check the return policy for this order.",
        #         "step_name": "#E3",
        #         "tool": "SearchFAQ",
        #         "tool_input": "return policy for delivered orders"
        #     }
        # ]
        return {
            "steps": matches,
            "plan_string": result.content
        }
    
    def _get_current_task(self, state: ReWOOState) -> Optional[int]:
        """
        Used by Worker Node (Executor) to determine which step to execute next.
        
        Returns:
            Step number (1-indexed) or None if all done
        """
        if "results" not in state or state["results"] is None:
            return 1 # No steps executed yet, start with Step #1
        if len(state["results"]) == len(state["steps"]):
            return None # All planned steps executed
        else:
            return len(state["results"]) + 1 # Move to the next step
    
    def tool_execution(self, state: ReWOOState) -> Dict:
        """
        Worker Node (Executor): Execute tools with variable substitution.
        
        Args:
            state: Current ReWOO state with steps and results
            
        Returns:
            Dict with updated 'results'
        """
        # Get step number that will be executed next
        _step = self._get_current_task(state)
        if _step is None:
            return {} # No remaining steps
        
        # Extracts information about the current step from the workflow state.
        # Example 1: step_name: #E1, tool: OrderStatus, tool_input: 12345
        # Example 2: step_name: #E2, tool: LLM, tool_input: Is order #12345 delivered based on #E1?
        _, step_name, tool, tool_input = state["steps"][_step - 1]

        # Retrieves previous step results if available. Results are produced by the tools
        # Example of results from Step #1
        # {
        #     "#E1": "Order #12345 Details:\n\n"
        #         "Status: Delivered\n"
        #         "Order Date: 2025-11-01\n"
        #         "Estimated Delivery: 2025-11-08\n"
        #         "Delivered On: 2025-11-08\n"
        #         "Tracking Number: TRK123456789\n\n"
        #         "Items Ordered:\n"
        #         "- Classic Cotton T-Shirt: 100% organic cotton, navy blue, size M (Qty: 2, $29.99)\n"
        #         "- Slim Fit Jeans: Dark wash denim, size 32x32 (Qty: 1, $79.99)\n\n"
        #         "Total: $139.97\n"
        #         "Shipping Address: 123 Main St, Seattle, WA 98101"
        # }
        _results = (state["results"] or {}) if "results" in state else {}
        
        # Variable substitution: replace #E references with actual results
        # Thus adding the result of the previous step to the current step tool input if needed
        for k, v in _results.items():
            tool_input = tool_input.replace(k, v) # Eg. Replaces #E1 with Result of step #1 (for order status) in the example above
        
        # Execute the appropriate tool
        if tool == "LLM":
            # LLM tool for reasoning
            result = self.planner_model.invoke(tool_input)
            result_str = result.content if hasattr(result, 'content') else str(result)
        elif tool in self.tools:
            # Execute tool using parameter mapping
            result = invoke_tool_with_params(self.tools[tool], tool_input)
            result_str = str(result)
        else:
            raise ValueError(f"Unknown tool: {tool}")
        
        _results[step_name] = result_str
        return {"results": _results}
    
    def solve(self, state: ReWOOState) -> Dict:
        """
        Solver node: Integrate evidence into final answer.
        
        Args:
            state: Complete ReWOO state with all results
            
        Returns:
            Dict with 'result' field containing final answer
        """
        # Reconstruct plan with actual results
        plan = ""
        for _plan, step_name, tool, tool_input in state["steps"]:
            _results = (state["results"] or {}) if "results" in state else {}
            
            # Variable substitution in display
            for k, v in _results.items():
                tool_input = tool_input.replace(k, v)
                step_name = step_name.replace(k, v)
            
            plan += f"Plan: {_plan}\n{step_name} = {tool}[{tool_input}]\n"
        
        # Add evidence to plan
        plan += "\nEvidence:\n"
        for step_name, result in state.get("results", {}).items():
            plan += f"{step_name} = {result}\n"
        
        # Solve with full context
        prompt = SOLVER_PROMPT.format(plan=plan, task=state["task"])
        result = self.solver_model.invoke(prompt)
        
        return {"result": result.content}
