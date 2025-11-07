"""
Ticket creation tool for escalating complex customer issues.
Stateful tool that creates support tickets for human agent follow-up.
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, List
from langchain_core.tools import tool

from common.logging_config import get_logger

logger = get_logger(__name__)

# Global state for tracking tickets (stateful behavior)
_support_tickets: Dict[str, Dict] = {}


def get_support_tickets() -> List[Dict]:
    """Get all support tickets."""
    return list(_support_tickets.values())


def reset_tickets():
    """Reset tickets state for testing."""
    global _support_tickets
    _support_tickets = {}


@tool
def create_ticket(
    customer_info: str,
    issue_summary: str, 
    priority: str = "medium",
    category: str = "general"
) -> str:
    """
    Create a support ticket for complex issues that require human agent assistance.
    
    Use this tool when customer issues are too complex for automated resolution,
    require human judgment, or involve multiple failed attempts at resolution.
    
    Args:
        customer_info: Customer identifier (name, email, order ID, etc.)
        issue_summary: Brief summary of the customer's issue and what they need
        priority: Priority level ("low", "medium", "high", "urgent")
        category: Issue category ("billing", "shipping", "product", "technical", "complaint")
        
    Returns:
        A formatted string with ticket creation confirmation
        
    Example:
        >>> create_ticket("john.doe@email.com", "Complex shipping issue with multiple orders", "high")
        "Support Ticket #TK789123 Created\\nPriority: High\\nEstimated response: 4 hours..."
    """
    logger.info(f"Ticket creation tool called - customer: {customer_info}, priority: {priority}")
    
    try:
        # Generate ticket ID
        ticket_id = f"TK{uuid.uuid4().hex[:6].upper()}"
        
        # Determine response time based on priority
        response_times = {
            "low": {"hours": 48, "description": "2 business days"},
            "medium": {"hours": 24, "description": "1 business day"},
            "high": {"hours": 4, "description": "4 hours"},
            "urgent": {"hours": 1, "description": "1 hour"}
        }
        
        response_info = response_times.get(priority, response_times["medium"])
        
        # Create ticket (stateful change)
        ticket = {
            "ticket_id": ticket_id,
            "customer_info": customer_info,
            "issue_summary": issue_summary,
            "priority": priority,
            "category": category,
            "status": "open",
            "created_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "assigned_agent": None,
            "estimated_response": (datetime.now() + timedelta(hours=response_info["hours"])).strftime("%Y-%m-%d %H:%M:%S"),
            "notes": []
        }
        
        _support_tickets[ticket_id] = ticket
        
        # Format response
        result = f"""Support Ticket Created Successfully!

Ticket Details:
- Ticket ID: {ticket_id}
- Customer: {customer_info}
- Issue: {issue_summary}
- Priority: {priority.title()}
- Category: {category.title()}
- Status: Open

Response Timeline:
- Created: {ticket['created_date']}
- Estimated Response: {response_info['description']}
- Target Resolution: Within 24-72 hours (depending on complexity)

What Happens Next:
1. Your ticket has been assigned to our specialized support team
2. A human agent will review your case within {response_info['description']}
3. You'll receive updates via email/phone based on your preferences
4. Reference your ticket with ID: {ticket_id}

Important: Keep this ticket ID for future reference. Our team will contact you soon with a resolution."""
        
        # Add note about escalation
        if priority in ["high", "urgent"]:
            result += f"\n\n🚨 High Priority Alert: This ticket has been marked as {priority} priority and will be handled by our senior support team."
        
        logger.info(
            f"Support ticket created - ID: {ticket_id}, priority: {priority}, category: {category}"
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Ticket creation error: {str(e)}")
        return "An error occurred while creating your support ticket. Please try again or contact our support line directly."
