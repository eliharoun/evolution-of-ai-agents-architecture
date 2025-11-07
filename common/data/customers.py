"""
Customer account data for the online clothing retailer.
Contains customer profiles, preferences, and order history.
"""

from datetime import datetime, timedelta
from typing import Dict, List

# Generate dynamic dates
today = datetime.now()

CUSTOMER_ACCOUNTS = {
    "customer_12345": {  # Linked to order #12345
        "customer_id": "customer_12345",
        "email": "john.doe@email.com",
        "name": "John Doe",
        "phone": "+1-555-123-4567",
        "created_date": (today - timedelta(days=365)).strftime("%Y-%m-%d"),
        "tier": "Gold",  # Bronze, Silver, Gold, Platinum
        "preferences": {
            "size": "M",
            "preferred_colors": ["navy", "black", "grey"],
            "style": "casual",
            "communication": "email"
        },
        "past_orders": [
            {
                "order_id": "12345",
                "date": (today - timedelta(days=10)).strftime("%Y-%m-%d"),
                "total": 139.97,
                "status": "delivered",
                "satisfaction_score": 5
            },
            {
                "order_id": "11234",
                "date": (today - timedelta(days=45)).strftime("%Y-%m-%d"),
                "total": 89.99,
                "status": "delivered", 
                "satisfaction_score": 4
            },
            {
                "order_id": "11001",
                "date": (today - timedelta(days=120)).strftime("%Y-%m-%d"),
                "total": 159.98,
                "status": "delivered",
                "satisfaction_score": 5
            }
        ],
        "total_spent": 389.94,
        "orders_count": 3,
        "returns_count": 0,
        "complaints_count": 0
    },
    "customer_12346": {  # Linked to order #12346
        "customer_id": "customer_12346", 
        "email": "sarah.smith@email.com",
        "name": "Sarah Smith",
        "phone": "+1-555-234-5678",
        "created_date": (today - timedelta(days=180)).strftime("%Y-%m-%d"),
        "tier": "Silver",
        "preferences": {
            "size": "S",
            "preferred_colors": ["pink", "white", "light blue"],
            "style": "trendy",
            "communication": "text"
        },
        "past_orders": [
            {
                "order_id": "12346",
                "date": (today - timedelta(days=3)).strftime("%Y-%m-%d"),
                "total": 59.99,
                "status": "shipped",
                "satisfaction_score": None
            },
            {
                "order_id": "11567",
                "date": (today - timedelta(days=30)).strftime("%Y-%m-%d"),
                "total": 79.99,
                "status": "delivered",
                "satisfaction_score": 3
            }
        ],
        "total_spent": 139.98,
        "orders_count": 2,
        "returns_count": 1,  # Had issues before
        "complaints_count": 1
    },
    "customer_12347": {  # Linked to order #12347
        "customer_id": "customer_12347",
        "email": "mike.wilson@email.com", 
        "name": "Mike Wilson",
        "phone": "+1-555-345-6789",
        "created_date": today.strftime("%Y-%m-%d"),  # New customer
        "tier": "Bronze",
        "preferences": {
            "size": "L",
            "preferred_colors": ["black", "brown", "burgundy"],
            "style": "professional",
            "communication": "email"
        },
        "past_orders": [
            {
                "order_id": "12347", 
                "date": today.strftime("%Y-%m-%d"),
                "total": 239.98,
                "status": "processing",
                "satisfaction_score": None
            }
        ],
        "total_spent": 239.98,
        "orders_count": 1,
        "returns_count": 0,
        "complaints_count": 0
    }
}


def get_customer_by_order(order_id: str) -> Dict:
    """
    Get customer data by their order ID.
    
    Args:
        order_id: Order ID to look up customer for
        
    Returns:
        Customer data dictionary or None if not found
    """
    # Map order IDs to customer IDs
    order_to_customer = {
        "12345": "customer_12345",
        "12346": "customer_12346", 
        "12347": "customer_12347",
        "12348": "customer_12345",  # John's second order
        "12349": "customer_12345"   # John's third order
    }
    
    customer_id = order_to_customer.get(order_id)
    if customer_id:
        return CUSTOMER_ACCOUNTS.get(customer_id)
    return None


def get_customer_by_email(email: str) -> Dict:
    """
    Get customer data by email address.
    
    Args:
        email: Customer email address
        
    Returns:
        Customer data dictionary or None if not found
    """
    for customer in CUSTOMER_ACCOUNTS.values():
        if customer["email"].lower() == email.lower():
            return customer
    return None
