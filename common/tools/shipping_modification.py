"""
Shipping modification tool for changing delivery options and addresses.
Stateful tool that tracks shipping changes and updates order delivery.
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, List
from langchain_core.tools import tool

from common.logging_config import get_logger
from common.data.orders import SAMPLE_ORDERS

logger = get_logger(__name__)

# Global state for tracking shipping modifications (stateful behavior)
_shipping_modifications: Dict[str, Dict] = {}


def get_shipping_modifications() -> List[Dict]:
    """Get all shipping modifications."""
    return list(_shipping_modifications.values())


def reset_shipping_modifications():
    """Reset shipping modifications state for testing."""
    global _shipping_modifications
    _shipping_modifications = {}


@tool
def modify_shipping(order_id: str, modification_type: str, new_value: str = None) -> str:
    """
    Modify shipping details for an existing order.
    
    Use this tool when customers want to change shipping address, expedite delivery,
    or modify shipping options for their orders.
    
    Args:
        order_id: The order ID to modify shipping for
        modification_type: Type of modification ("address", "expedite", "standard", "cancel")
        new_value: New value (address for address change, ignored for expedite/standard)
        
    Returns:
        A formatted string with shipping modification confirmation
        
    Example:
        >>> modify_shipping("12345", "expedite")
        "Shipping Modified Successfully\\nOrder #12345: Expedited to overnight delivery..."
    """
    logger.info(f"Shipping modification tool called - order: {order_id}, type: {modification_type}")
    
    try:
        # Check if order exists
        order = SAMPLE_ORDERS.get(order_id)
        if not order:
            return f"Order #{order_id} not found. Cannot modify shipping for non-existent order."
        
        # Check if order can be modified
        if order["status"] == "Delivered":
            return f"Order #{order_id} has already been delivered. Cannot modify shipping for delivered orders."
        
        # Generate modification ID
        modification_id = f"SM{uuid.uuid4().hex[:6].upper()}"
        
        # Process different modification types
        if modification_type == "expedite":
            # Expedite shipping
            new_delivery_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            additional_cost = 15.99
            
            modification = {
                "modification_id": modification_id,
                "order_id": order_id,
                "type": "expedite",
                "original_delivery": order.get("estimated_delivery"),
                "new_delivery": new_delivery_date,
                "additional_cost": additional_cost,
                "status": "confirmed",
                "created_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            result = f"""Shipping Expedited Successfully!

Modification Details:
- Modification ID: {modification_id}
- Order: #{order_id}
- Change: Expedited to overnight delivery
- Original Delivery: {order.get('estimated_delivery', 'Unknown')}
- New Delivery: {new_delivery_date}
- Additional Cost: ${additional_cost:.2f}

Your order will now arrive by {new_delivery_date}!
Additional charges will appear on your original payment method."""
            
        elif modification_type == "address":
            if not new_value:
                return "Address change requires a new address. Please provide the new shipping address."
            
            modification = {
                "modification_id": modification_id,
                "order_id": order_id,
                "type": "address",
                "original_address": order.get("shipping_address"),
                "new_address": new_value,
                "status": "confirmed",
                "created_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            result = f"""Shipping Address Updated Successfully!

Modification Details:
- Modification ID: {modification_id}
- Order: #{order_id}
- Original Address: {order.get('shipping_address', 'Unknown')}
- New Address: {new_value}
- Estimated Delivery: {order.get('estimated_delivery', 'Unknown')} (unchanged)

Your order will now be delivered to the new address."""
            
        elif modification_type == "standard":
            # Change back to standard shipping
            new_delivery_date = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
            
            modification = {
                "modification_id": modification_id,
                "order_id": order_id,
                "type": "standard",
                "original_delivery": order.get("estimated_delivery"),
                "new_delivery": new_delivery_date,
                "cost_saved": 0,  # Assume no refund for downgrade
                "status": "confirmed",
                "created_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            result = f"""Shipping Changed to Standard Successfully!

Modification Details:
- Modification ID: {modification_id}
- Order: #{order_id}
- Change: Downgraded to standard shipping
- New Delivery: {new_delivery_date}

Note: Your order will now take standard delivery time."""
            
        else:
            return f"Unknown modification type: {modification_type}. Supported types: 'expedite', 'address', 'standard'"
        
        # Store modification (stateful change)
        _shipping_modifications[modification_id] = modification
        
        logger.info(
            f"Shipping modification created - ID: {modification_id}, order: {order_id}, type: {modification_type}"
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Shipping modification error for order {order_id}: {str(e)}")
        return f"An error occurred while modifying shipping for order #{order_id}. Please try again or contact customer service."
