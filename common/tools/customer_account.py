"""
Customer account tool for viewing customer history and account details.
Enables agents to access customer profiles, order history, and preferences.
"""

from typing import Optional
from langchain_core.tools import tool

from common.logging_config import get_logger
from common.data.customers import get_customer_by_order, get_customer_by_email, CUSTOMER_ACCOUNTS

logger = get_logger(__name__)


@tool
def get_customer_account(identifier: str, lookup_type: str = "order_id") -> str:
    """
    Look up customer account information and order history.
    
    Use this tool when you need to understand a customer's background, past orders,
    preferences, or account status to provide personalized service.
    
    Args:
        identifier: Customer identifier (order ID, email, or customer ID)
        lookup_type: Type of lookup ("order_id", "email", or "customer_id")
        
    Returns:
        A formatted string with customer account details and history
        
    Example:
        >>> get_customer_account("12345", "order_id")
        "Customer: John Doe (Gold tier)\\nOrder History: 3 orders, $389.94 total..."
    """
    logger.info(f"Customer account tool called - identifier: {identifier}, type: {lookup_type}")
    
    try:
        customer = None
        
        if lookup_type == "order_id":
            customer = get_customer_by_order(identifier)
        elif lookup_type == "email":
            customer = get_customer_by_email(identifier)
        elif lookup_type == "customer_id":
            customer = CUSTOMER_ACCOUNTS.get(identifier)
        
        if not customer:
            return f"Customer not found for {lookup_type}: {identifier}. Please verify the information and try again."
        
        # Format customer account details
        result = f"""Customer Account: {customer['name']}

Contact Information:
- Email: {customer['email']}
- Phone: {customer['phone']}
- Member Since: {customer['created_date']}
- Tier: {customer['tier']}

Preferences:
- Size: {customer['preferences']['size']}
- Preferred Colors: {', '.join(customer['preferences']['preferred_colors'])}
- Style: {customer['preferences']['style']}
- Communication: {customer['preferences']['communication']}

Account Summary:
- Total Orders: {customer['orders_count']}
- Total Spent: ${customer['total_spent']:.2f}
- Returns: {customer['returns_count']}
- Complaints: {customer['complaints_count']}

Recent Order History:"""

        # Add recent orders
        for order in customer['past_orders'][-3:]:  # Last 3 orders
            satisfaction = f"★{order['satisfaction_score']}/5" if order['satisfaction_score'] else "Not rated"
            result += f"\n- Order #{order['order_id']}: ${order['total']:.2f} ({order['status']}) - {satisfaction}"
        
        logger.info(
            f"Customer account found - name: {customer['name']}, tier: {customer['tier']}, orders: {customer['orders_count']}"
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Customer account lookup error for {identifier}: {str(e)}")
        return f"An error occurred while looking up customer account. Please try again later."
