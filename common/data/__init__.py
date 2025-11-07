"""
Shared data package for all stages.
Contains mock data for demonstrations.
"""

from common.data.orders import SAMPLE_ORDERS
from common.data.faqs import FAQ_DATA
from common.data.customers import CUSTOMER_ACCOUNTS, get_customer_by_order, get_customer_by_email
from common.data.inventory import (
    PRODUCT_INVENTORY, 
    get_product_inventory, 
    check_availability, 
    update_inventory, 
    reset_inventory
)

__all__ = [
    "SAMPLE_ORDERS", 
    "FAQ_DATA",
    "CUSTOMER_ACCOUNTS",
    "get_customer_by_order",
    "get_customer_by_email", 
    "PRODUCT_INVENTORY",
    "get_product_inventory",
    "check_availability",
    "update_inventory", 
    "reset_inventory"
]
