"""
Refund processing tool for initiating customer refunds.
Stateful tool that tracks refund requests and updates order status.
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, List
from langchain_core.tools import tool

from common.logging_config import get_logger
from common.data.orders import SAMPLE_ORDERS

logger = get_logger(__name__)

# Global state for tracking refunds (stateful behavior)
_refund_requests: Dict[str, Dict] = {}


def get_refund_requests() -> List[Dict]:
    """Get all refund requests."""
    return list(_refund_requests.values())


def reset_refunds():
    """Reset refund state for testing."""
    global _refund_requests
    _refund_requests = {}


@tool
def process_refund(order_id: str, reason: str, amount: float = None) -> str:
    """
    Initiate a refund for a customer order.
    
    Use this tool when a customer requests a refund for their order or items.
    The tool will create a refund request and provide timeline information.
    
    Args:
        order_id: The order ID to process refund for
        reason: Reason for the refund (e.g., "item not as described", "damaged", "wrong size")
        amount: Refund amount (if None, refunds full order amount)
        
    Returns:
        A formatted string with refund confirmation and next steps
        
    Example:
        >>> process_refund("12345", "item not as described")
        "Refund Request #RF789123 Created\\nOrder #12345: $139.97 refund initiated..."
    """
    logger.info(f"Refund processing tool called - order: {order_id}, reason: {reason}")
    
    try:
        # Check if order exists
        order = SAMPLE_ORDERS.get(order_id)
        if not order:
            return f"Order #{order_id} not found. Cannot process refund for non-existent order."
        
        # Check if order can be refunded
        if order["status"] == "Processing":
            return f"Order #{order_id} is still processing. Please cancel the order instead of requesting a refund."
        
        # Generate refund request ID
        refund_id = f"RF{uuid.uuid4().hex[:6].upper()}"
        
        # Determine refund amount
        refund_amount = amount if amount is not None else order["total"]
        
        # Create refund request (stateful change)
        refund_request = {
            "refund_id": refund_id,
            "order_id": order_id,
            "amount": refund_amount,
            "reason": reason,
            "status": "initiated",
            "created_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "estimated_completion": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        }
        
        _refund_requests[refund_id] = refund_request
        
        # Format response
        result = f"""Refund Request Created Successfully!

Refund Details:
- Refund ID: {refund_id}
- Order: #{order_id}
- Amount: ${refund_amount:.2f}
- Reason: {reason}
- Status: Initiated

Timeline:
- Refund initiated today
- Estimated completion: 5-7 business days
- Refund will be credited to original payment method

Next Steps:
1. You'll receive an email confirmation shortly
2. No need to return items yet - wait for return instructions
3. Track your refund status with ID: {refund_id}

Note: Once approved, you'll receive a prepaid return label if item return is required."""
        
        logger.info(
            f"Refund request created - ID: {refund_id}, order: {order_id}, amount: ${refund_amount:.2f}"
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Refund processing error for order {order_id}: {str(e)}")
        return f"An error occurred while processing the refund for order #{order_id}. Please try again or contact customer service."
