"""
Shared specialist agents for Stage 4 multi-agent implementations.

Each specialist is a ReAct agent focused on a specific domain with a subset of tools.
These agents are used by both Supervisor v1 (built-in) and Supervisor v2 (custom).
"""

from typing import Optional, Any
from langchain_core.language_models import BaseChatModel
from langgraph.prebuilt import create_react_agent

# Import tools from common
from common.tools import (
    get_order_status,
    modify_shipping,
    process_refund,
    check_inventory,
    search_faq,
    get_customer_account,
    create_ticket,
)

# Import prompts from common (shared)
from stage_4.common.specialist_prompts import (
    ORDER_OPERATIONS_PROMPT,
    PRODUCT_INVENTORY_PROMPT,
    CUSTOMER_ACCOUNT_PROMPT,
)


def create_order_operations_agent(
    model: BaseChatModel,
    checkpointer: Optional[Any] = None
):
    """
    Create the Order Operations specialist agent.
    
    This agent handles the complete order lifecycle:
    - Order tracking and status
    - Shipping modifications (expedite, address changes)
    - Refund processing
    
    Args:
        model: Language model instance to use
        checkpointer: Optional checkpoint saver for state persistence
        
    Returns:
        Compiled ReAct agent specialized in order operations
    """
    return create_react_agent(
        model=model,
        tools=[get_order_status, modify_shipping, process_refund],
        prompt=ORDER_OPERATIONS_PROMPT,
        name="order_operations",
        checkpointer=checkpointer,
    )


def create_product_inventory_agent(
    model: BaseChatModel,
    checkpointer: Optional[Any] = None
):
    """
    Create the Product & Inventory specialist agent.
    
    This agent handles product-related queries:
    - Product availability and variants
    - FAQ knowledge base (specs, policies, returns)
    
    Args:
        model: Language model instance to use
        checkpointer: Optional checkpoint saver for state persistence
        
    Returns:
        Compiled ReAct agent specialized in products and inventory
    """
    return create_react_agent(
        model=model,
        tools=[check_inventory, search_faq],
        prompt=PRODUCT_INVENTORY_PROMPT,
        name="product_inventory",
        checkpointer=checkpointer,
    )


def create_customer_account_agent(
    model: BaseChatModel,
    checkpointer: Optional[Any] = None
):
    """
    Create the Customer Account specialist agent.
    
    This agent handles account management and escalations:
    - Customer account information and history
    - Complex issue escalation via ticket creation
    
    Args:
        model: Language model instance to use
        checkpointer: Optional checkpoint saver for state persistence
        
    Returns:
        Compiled ReAct agent specialized in account management
    """
    return create_react_agent(
        model=model,
        tools=[get_customer_account, create_ticket],
        prompt=CUSTOMER_ACCOUNT_PROMPT,
        name="customer_account",
        checkpointer=checkpointer,
    )


def create_all_specialists(
    model: BaseChatModel,
    checkpointer: Optional[Any] = None
) -> dict[str, Any]:
    """
    Create all specialist agents with a single model instance.
    
    This is the main entry point for creating the specialist agent team.
    All agents share the same model configuration but have different tools
    and prompts based on their specialization.
    
    Args:
        model: Language model instance to use for all specialists
        checkpointer: Optional checkpoint saver for state persistence
        
    Returns:
        Dictionary mapping agent names to compiled agents:
        - "order_operations": Order Operations Agent
        - "product_inventory": Product & Inventory Agent  
        - "customer_account": Customer Account Agent
    """
    return {
        "order_operations": create_order_operations_agent(model, checkpointer),
        "product_inventory": create_product_inventory_agent(model, checkpointer),
        "customer_account": create_customer_account_agent(model, checkpointer),
    }
