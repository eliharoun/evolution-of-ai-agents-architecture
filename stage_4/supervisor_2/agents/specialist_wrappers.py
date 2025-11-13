"""
Specialist agent tool wrappers for Stage 4 Supervisor v2 implementation.

This module wraps specialist ReAct agents as tools that the supervisor can call.
This is the key pattern for custom supervisor implementations - specialists
become tools at the supervisor level.
"""

from typing import Any
from langchain_core.tools import tool
from langchain_core.language_models import BaseChatModel

from stage_4.common.specialist_agents import (
    create_order_operations_agent,
    create_product_inventory_agent,
    create_customer_account_agent,
)
from common.logging_config import get_logger

logger = get_logger(__name__)


def create_specialist_tool_wrappers(
    model: BaseChatModel,
    checkpointer: Any = None
) -> list:
    """
    Create tool wrappers for all specialist agents.
    
    Each specialist agent is wrapped as a tool that the supervisor can invoke.
    This provides the custom supervisor with high-level capabilities while
    hiding the complexity of individual tool execution.
    
    Args:
        model: Language model instance for specialists
        checkpointer: Optional checkpoint saver
        
    Returns:
        List of wrapped specialist tools for supervisor
    """
    logger.info("Creating specialist agent tool wrappers...")
    
    # Create the specialist agents
    order_agent = create_order_operations_agent(model, checkpointer)
    product_agent = create_product_inventory_agent(model, checkpointer)
    account_agent = create_customer_account_agent(model, checkpointer)
    
    # Define tool wrappers
    @tool
    def specialist_order_operations(request: str) -> str:
        """
        Consult the Order Operations specialist for order-related queries.
        
        Use this when customers need help with:
        - Checking order status and tracking
        - Modifying shipping (expedite, change address)
        - Processing refunds and returns
        
        The specialist has access to order databases and can perform order modifications.
        
        Args:
            request: Natural language request about orders (e.g., "Check status of order #12345")
            
        Returns:
            Specialist's response with order information and actions taken
            
        Example:
            >>> specialist_order_operations("What's the status of order #12345?")
            "Order #12345 was delivered on November 8, 2025..."
        """
        logger.info(f"Supervisor consulting Order Operations - request: {request[:100]}...")
        
        try:
            result = order_agent.invoke({
                "messages": [{"role": "user", "content": request}]
            })
            
            # Extract the final message from the specialist
            final_message = result["messages"][-1]
            response = final_message.content if hasattr(final_message, "content") else str(final_message)
            
            logger.info(f"Order Operations response received - length: {len(response)}")
            return response
            
        except Exception as e:
            logger.error(f"Order Operations consultation error: {str(e)}")
            return f"Error consulting order specialist: {str(e)}"
    
    @tool
    def specialist_product_inventory(request: str) -> str:
        """
        Consult the Product & Inventory specialist for product-related queries.
        
        Use this when customers need help with:
        - Checking product availability and variants
        - Finding product specifications and details
        - Learning about policies (returns, shipping, warranties) from FAQs
        
        The specialist has access to inventory systems and the knowledge base.
        
        Args:
            request: Natural language request about products (e.g., "Do you have this in blue?")
            
        Returns:
            Specialist's response with product information
            
        Example:
            >>> specialist_product_inventory("Do you have the t-shirt in blue, size M?")
            "Yes, the Classic Cotton T-Shirt is available in blue, size M..."
        """
        logger.info(f"Supervisor consulting Product & Inventory - request: {request[:100]}...")
        
        try:
            result = product_agent.invoke({
                "messages": [{"role": "user", "content": request}]
            })
            
            # Extract the final message from the specialist
            final_message = result["messages"][-1]
            response = final_message.content if hasattr(final_message, "content") else str(final_message)
            
            logger.info(f"Product & Inventory response received - length: {len(response)}")
            return response
            
        except Exception as e:
            logger.error(f"Product & Inventory consultation error: {str(e)}")
            return f"Error consulting product specialist: {str(e)}"
    
    @tool
    def specialist_customer_account(request: str) -> str:
        """
        Consult the Customer Account specialist for account-related queries.
        
        Use this when customers need help with:
        - Viewing account information and order history
        - Escalating complex issues to human support
        - Account-related questions that need personalized context
        
        The specialist has access to customer databases and ticketing systems.
        
        Args:
            request: Natural language request about accounts (e.g., "Show my account history")
            
        Returns:
            Specialist's response with account information
            
        Example:
            >>> specialist_customer_account("What's my account history for order #12345?")
            "Your account shows you ordered this item on November 1, 2025..."
        """
        logger.info(f"Supervisor consulting Customer Account - request: {request[:100]}...")
        
        try:
            result = account_agent.invoke({
                "messages": [{"role": "user", "content": request}]
            })
            
            # Extract the final message from the specialist
            final_message = result["messages"][-1]
            response = final_message.content if hasattr(final_message, "content") else str(final_message)
            
            logger.info(f"Customer Account response received - length: {len(response)}")
            return response
            
        except Exception as e:
            logger.error(f"Customer Account consultation error: {str(e)}")
            return f"Error consulting account specialist: {str(e)}"
    
    logger.info("Created 3 specialist tool wrappers for supervisor")
    
    return [
        specialist_order_operations,
        specialist_product_inventory,
        specialist_customer_account,
    ]
