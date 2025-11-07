"""
Shared tools package for all stages.
Contains tools for customer support agents.
"""

# Stage 1 tools
from common.tools.order_lookup import get_order_status, OrderDatabase
from common.tools.faq_retrieval import search_faq, FAQRetriever

# Stage 2 additional tools
from common.tools.customer_account import get_customer_account
from common.tools.refund_processing import process_refund, get_refund_requests, reset_refunds
from common.tools.shipping_modification import modify_shipping, get_shipping_modifications, reset_shipping_modifications
from common.tools.inventory_check import check_inventory, find_similar_products
from common.tools.ticket_creation import create_ticket, get_support_tickets, reset_tickets

__all__ = [
    # Stage 1 tools
    "get_order_status",
    "OrderDatabase", 
    "search_faq",
    "FAQRetriever",
    
    # Stage 2 additional tools
    "get_customer_account",
    "process_refund",
    "get_refund_requests",
    "reset_refunds",
    "modify_shipping", 
    "get_shipping_modifications",
    "reset_shipping_modifications",
    "check_inventory",
    "find_similar_products",
    "create_ticket",
    "get_support_tickets", 
    "reset_tickets"
]

# Convenient tool collections
STAGE_1_TOOLS = [get_order_status, search_faq]

STAGE_2_TOOLS = [
    get_order_status,          # Original tools
    search_faq,
    get_customer_account,      # New tools
    process_refund,
    modify_shipping,
    check_inventory,
    create_ticket
]
