# Building Stage 2: When One Agent Has Too Many Tools

Welcome back! In this tutorial, you'll extend your Stage 1 agent by adding more tools and struggle monitoring. By the end, you'll understand why having more tools can actually make things harder for a single agent.

## What You'll Learn

- How to add new tools to an existing agent
- Why more tools creates complexity
- How to detect when agents struggle
- How to add optional conversation memory (checkpointing)
- When single agents reach their limits

## Prerequisites

Before starting, you should have:
- Completed the Stage 1 tutorial
- A working Stage 1 agent
- Understanding of the ReAct pattern
- Basic understanding of Python classes

## Tutorial Overview

We'll build Stage 2 in 4 main steps:
1. Create 5 new tools (going from 2 to 7 total)
2. Update the agent to use all 7 tools
3. Add struggle monitoring
4. Add optional checkpointing

The key insight: **We're keeping the same architecture, just adding tools.**

Let's start!

---

## Step 1: Create Five New Tools

In Stage 1, we had 2 tools: order lookup and FAQ search. Now we're adding 5 more tools that handle different customer service tasks.

### New Tool 1: Customer Account Lookup

This tool retrieves customer account history and preferences.

Create `common/tools/customer_account.py`:

```python
"""Tool for looking up customer account information."""

from langchain_core.tools import tool
from common.data.customers import CUSTOMERS


@tool
def get_customer_account(order_id: str) -> str:
    """
    Look up customer account information and order history.
    
    Use this when you need to understand customer context,
    preferences, or order history.
    
    Args:
        order_id: Order ID to find the associated customer
    
    Returns:
        Customer account details and order history
    """
    # Clean up order ID
    order_id = order_id.replace("#", "").strip()
    
    # Find customer by order
    customer = None
    for cust in CUSTOMERS.values():
        if order_id in cust["order_history"]:
            customer = cust
            break
    
    if not customer:
        return f"No customer found for order {order_id}"
    
    # Format response
    result = f"Customer: {customer['name']}\n"
    result += f"Email: {customer['email']}\n"
    result += f"Member Since: {customer['member_since']}\n"
    result += f"Lifetime Orders: {len(customer['order_history'])}\n"
    result += f"\nOrder History:\n"
    for order in customer['order_history']:
        result += f"  - Order #{order}\n"
    
    if customer.get('preferences'):
        result += f"\nPreferences:\n"
        for key, value in customer['preferences'].items():
            result += f"  - {key}: {value}\n"
    
    return result
```

**What's happening:**
- Similar structure to order lookup tool from Stage 1
- Searches CUSTOMERS data by order ID
- Returns account history and preferences
- Gives the agent context about the customer

### New Tool 2: Process Refund

This tool initiates refunds for orders.

Create `common/tools/refund_processing.py`:

```python
"""Tool for processing refunds."""

from langchain_core.tools import tool
from common.data.orders import ORDERS


@tool
def process_refund(order_id: str, reason: str) -> str:
    """
    Initiate a refund for a customer order.
    
    Use this when a customer requests a refund for a delivered
    or shipped order.
    
    Args:
        order_id: The order ID to refund
        reason: Brief reason for the refund
    
    Returns:
        Confirmation of refund initiation
    """
    # Clean order ID
    order_id = order_id.replace("#", "").strip()
    
    # Check if order exists
    order = ORDERS.get(order_id)
    
    if not order:
        return f"Cannot process refund: Order {order_id} not found"
    
    # Check if refund is possible based on status
    status = order.get("status", "")
    
    if status == "Processing":
        return f"Cannot refund order #{order_id} - order is still processing. Consider canceling instead."
    
    # Simulate refund processing
    total = order.get("total", 0)
    
    result = f"✓ Refund initiated for order #{order_id}\n"
    result += f"Amount: ${total}\n"
    result += f"Reason: {reason}\n"
    result += f"Refund will be processed within 5-7 business days\n"
    result += f"Customer will receive confirmation email"
    
    return result
```

**Key points:**
- Takes order ID and reason as parameters
- Validates order exists and can be refunded
- Returns confirmation message
- In a real system, this would trigger actual refund processing

### New Tool 3: Modify Shipping

This tool handles shipping changes like address updates or expediting.

Create `common/tools/shipping_modification.py`:

```python
"""Tool for modifying shipping details."""

from langchain_core.tools import tool
from common.data.orders import ORDERS


@tool
def modify_shipping(order_id: str, modification_type: str, details: str = "") -> str:
    """
    Modify shipping details for an order.
    
    Use this when customers want to:
    - Change delivery address
    - Expedite shipping
    - Hold for pickup
    
    Args:
        order_id: The order ID to modify
        modification_type: Type of change (expedite, change_address, hold)
        details: Additional details (new address, etc.)
    
    Returns:
        Confirmation of shipping modification
    """
    # Clean order ID
    order_id = order_id.replace("#", "").strip()
    
    # Check if order exists
    order = ORDERS.get(order_id)
    
    if not order:
        return f"Cannot modify shipping: Order {order_id} not found"
    
    # Check order status
    status = order.get("status", "")
    
    if status == "Delivered":
        return f"Cannot modify shipping for order #{order_id} - already delivered"
    
    if status == "Processing":
        return f"Cannot modify shipping for order #{order_id} - still processing"
    
    # Process modification
    result = f"✓ Shipping modification for order #{order_id}\n"
    
    if modification_type == "expedite":
        result += "Upgraded to overnight shipping\n"
        result += "New estimated delivery: Tomorrow\n"
        result += "Additional charge: $25 (waived for this request)"
    
    elif modification_type == "change_address":
        result += f"Address updated to: {details}\n"
        result += "Delivery carrier has been notified"
    
    elif modification_type == "hold":
        result += "Package will be held at local facility\n"
        result += "Customer can pick up anytime during business hours"
    
    else:
        return f"Unknown modification type: {modification_type}"
    
    return result
```

**What's different:**
- Multiple modification types (expedite, change address, hold)
- More complex logic than previous tools
- Shows how tools can have multiple "modes"

### New Tool 4: Check Inventory

This tool checks product availability and variants.

Create `common/tools/inventory_check.py`:

```python
"""Tool for checking product inventory."""

from langchain_core.tools import tool
from common.data.inventory import INVENTORY


@tool
def check_inventory(product_name: str, color: str = "", size: str = "") -> str:
    """
    Check product availability and variants.
    
    Use this when customers ask about:
    - Product availability
    - Specific colors or sizes
    - Alternative options
    
    Args:
        product_name: Name of the product to check
        color: Optional color variant
        size: Optional size
    
    Returns:
        Inventory details and availability
    """
    # Search for product (case insensitive)
    product = None
    for item in INVENTORY:
        if product_name.lower() in item["name"].lower():
            product = item
            break
    
    if not product:
        return f"Product '{product_name}' not found in inventory"
    
    # Build response
    result = f"Product: {product['name']}\n"
    result += f"Base Price: ${product['price']}\n\n"
    result += "Available Variants:\n"
    
    for variant in product["variants"]:
        # Filter by color if specified
        if color and color.lower() not in variant["color"].lower():
            continue
        
        # Filter by size if specified
        if size and size.upper() != variant["size"]:
            continue
        
        # Show variant details
        stock_status = "In Stock" if variant["in_stock"] else "Out of Stock"
        result += f"  - {variant['color']}, Size {variant['size']}: {stock_status}"
        
        if variant["in_stock"]:
            result += f" ({variant['quantity']} available)\n"
        else:
            result += "\n"
    
    return result
```

**Why this is useful:**
- Helps with product questions
- Supports filtering by color and size
- Shows stock levels

### New Tool 5: Create Support Ticket

This tool escalates complex issues to human support.

Create `common/tools/ticket_creation.py`:

```python
"""Tool for creating support tickets."""

from langchain_core.tools import tool
from datetime import datetime


@tool
def create_ticket(
    issue_description: str,
    customer_email: str = "unknown@example.com",
    priority: str = "medium"
) -> str:
    """
    Create a support ticket for complex issues.
    
    Use this when:
    - Issue is too complex for automated handling
    - Customer needs human assistance
    - Technical problems require investigation
    
    Args:
        issue_description: Detailed description of the issue
        customer_email: Customer's email address
        priority: Ticket priority (low, medium, high)
    
    Returns:
        Ticket confirmation with ticket ID
    """
    # Generate ticket ID (in real system, would be from database)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    ticket_id = f"TICKET-{timestamp}"
    
    result = f"✓ Support ticket created\n"
    result += f"Ticket ID: {ticket_id}\n"
    result += f"Priority: {priority.upper()}\n"
    result += f"Customer: {customer_email}\n"
    result += f"\nIssue: {issue_description}\n\n"
    result += "A support specialist will contact you within:\n"
    
    if priority.lower() == "high":
        result += "- 1 hour"
    elif priority.lower() == "medium":
        result += "- 4 hours"
    else:
        result += "- 24 hours"
    
    return result
```

**When to use this:**
- Complex issues the agent can't handle
- Situations requiring human judgment
- Technical problems
- Escalation path for the agent

### Update the Tool Registry

Now create `common/tools/__init__.py` to export all tools:

```python
"""Tool registry for all stages."""

from common.tools.order_lookup import get_order_status
from common.tools.faq_retrieval import search_faq
from common.tools.customer_account import get_customer_account
from common.tools.refund_processing import process_refund
from common.tools.shipping_modification import modify_shipping
from common.tools.inventory_check import check_inventory
from common.tools.ticket_creation import create_ticket

# Stage 1 tools (2 tools)
STAGE_1_TOOLS = [
    get_order_status,
    search_faq
]

# Stage 2 tools (7 tools)
STAGE_2_TOOLS = [
    get_order_status,
    search_faq,
    get_customer_account,
    process_refund,
    modify_shipping,
    check_inventory,
    create_ticket
]
```

**Why organize this way:**
- Easy to see which tools each stage has
- Simple to import: `from common.tools import STAGE_2_TOOLS`
- Clear progression from Stage 1 to Stage 2

---

## Step 2: Update the Agent for 7 Tools

The agent code is almost identical to Stage 1. The main difference: it now imports and uses 7 tools instead of 2.

### Create the Agent

Create `stage_2/agents/react_agent.py`:

```python
"""ReAct Agent for Stage 2 with 7 tools."""

from langchain_core.messages import SystemMessage, AIMessage

from stage_2.agents.state import AgentState
from common.tools import STAGE_2_TOOLS  # Import all 7 tools
from stage_2.prompts.prompts import SYSTEM_PROMPT
from common.model_factory import ModelFactory, ModelType
from common.logging_config import get_logger

logger = get_logger(__name__)


class ReactAgent:
    """
    ReAct agent with 7 tools.
    
    Same pattern as Stage 1, but now the agent must choose
    between 7 tools instead of 2. This creates complexity:
    - More choices to evaluate
    - More potential for confusion
    - More opportunities for wrong decisions
    """
    
    def __init__(
        self,
        model_type: ModelType,
        model_name: str,
        temperature: float = 0
    ):
        """Initialize the agent with 7 tools."""
        # Create model (same as Stage 1)
        self.model = ModelFactory.create_model(
            model_type=model_type,
            model_name=model_name,
            temperature=temperature
        )
        
        # Now we have 7 tools instead of 2!
        self.tools = STAGE_2_TOOLS
        
        # Bind all 7 tools to the model
        self.model_with_tools = self.model.bind_tools(self.tools)
        
        # Use Stage 2 system prompt
        self.system_prompt = SYSTEM_PROMPT
        
        logger.info(f"Stage 2 agent initialized with {len(self.tools)} tools")
    
    def call_model(self, state: AgentState) -> dict:
        """
        Think and act - same as Stage 1.
        
        The difference: With 7 tools available, the model
        has more to think about, which can lead to:
        - Longer decision times
        - Wrong tool selection
        - Confusion about dependencies
        """
        messages = state["messages"]
        iterations = state.get("iterations", 0)
        
        # Add warning if iterations getting high
        if iterations > 3:
            logger.warning(
                f"High iteration count ({iterations + 1}) - "
                "agent may be struggling with tool selection"
            )
        
        logger.info(
            f"Agent thinking (iteration {iterations + 1}) - "
            f"must choose from {len(self.tools)} tools"
        )
        
        # Add system prompt if needed
        if not any(isinstance(m, SystemMessage) for m in messages):
            messages = [SystemMessage(content=self.system_prompt)] + list(messages)
        
        try:
            # Call the model
            response = self.model_with_tools.invoke(messages)
            
            # Log tool usage with struggle detection
            if hasattr(response, "tool_calls") and response.tool_calls:
                tool_names = [tc["name"] for tc in response.tool_calls]
                
                # Detect potential confusion
                if len(tool_names) > 2:
                    logger.warning(
                        f"Agent calling many tools at once: {tool_names}"
                    )
                
                logger.info(f"Agent using tools: {tool_names}")
            else:
                logger.info("Agent providing final response")
            
            return {
                "messages": [response],
                "iterations": iterations + 1
            }
            
        except Exception as e:
            logger.error(f"Agent error: {e}")
            error_msg = AIMessage(
                content="I apologize, but I encountered an error. "
                       "Let me create a support ticket for you."
            )
            return {
                "messages": [error_msg],
                "iterations": iterations + 1
            }
```

**Key differences from Stage 1:**
1. Uses `STAGE_2_TOOLS` (7 tools) instead of manually listing 2
2. Adds warning logs when iterations get high
3. Detects when agent calls many tools at once
4. Otherwise, the logic is identical

**The lesson:** More tools doesn't require architectural changes, but it does create operational challenges.

---

## Step 3: Add Struggle Monitoring

Now for something completely new: automatically detecting when the agent struggles.

### Create the Struggle Analyzer

Create `common/monitoring/struggle_analyzer.py`:

```python
"""Detects when agents struggle with tool selection."""

from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class StruggleThresholds:
    """Thresholds for detecting struggles."""
    high_iterations_threshold: int = 4
    context_loss_threshold: int = 2
    parallel_tools_threshold: int = 2


class StruggleAnalyzer:
    """
    Watches agent behavior and detects struggle patterns.
    
    Detects three types of struggles:
    1. High Iterations: Agent takes too many steps
    2. Tool Confusion: Uses multiple tools when one would do
    3. Context Loss: Repeats same tool, forgetting results
    """
    
    def __init__(self, stage: int = 2):
        """Initialize the analyzer."""
        self.stage = stage
        self.thresholds = StruggleThresholds()
        self._reset_tracking()
    
    def _reset_tracking(self):
        """Reset all tracking variables."""
        self._indicators = {
            "high_iterations": False,
            "iteration_count": 0,
            "tool_confusion": False,
            "unique_tools": 0,
            "context_loss": False,
            "tool_usage_history": [],
            "repeated_tools": {}
        }
    
    def analyze_iteration(self, iteration_count: int):
        """Check if iteration count indicates struggle."""
        self._indicators["iteration_count"] = iteration_count
        
        # High iteration = agent is confused
        if iteration_count >= self.thresholds.high_iterations_threshold:
            self._indicators["high_iterations"] = True
            print(f"⚠️  Struggle: High iterations ({iteration_count})")
    
    def analyze_tool_calls(self, tool_calls: List[str]):
        """Check tool usage patterns for struggles."""
        if not tool_calls:
            return
        
        # Track all tool usage
        self._indicators["tool_usage_history"].extend(tool_calls)
        
        # Count unique tools used
        unique = set(self._indicators["tool_usage_history"])
        self._indicators["unique_tools"] = len(unique)
        
        # Parallel tools = confusion
        if len(tool_calls) >= self.thresholds.parallel_tools_threshold:
            self._indicators["tool_confusion"] = True
            print(f"⚠️  Struggle: Tool confusion ({tool_calls})")
        
        # Count tool repetitions
        tool_counts = {}
        for tool in self._indicators["tool_usage_history"]:
            tool_counts[tool] = tool_counts.get(tool, 0) + 1
        
        # Repeated tools = context loss
        for tool, count in tool_counts.items():
            if count > self.thresholds.context_loss_threshold:
                self._indicators["context_loss"] = True
                self._indicators["repeated_tools"] = tool_counts
                print(f"⚠️  Struggle: Context loss ('{tool}' used {count}x)")
                break
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current struggle statistics."""
        return {
            "high_iterations": self._indicators["high_iterations"],
            "iteration_count": self._indicators["iteration_count"],
            "tool_confusion": self._indicators["tool_confusion"],
            "unique_tools": self._indicators["unique_tools"],
            "context_loss": self._indicators["context_loss"],
            "repeated_tools": self._indicators["repeated_tools"].copy()
        }
    
    def reset(self):
        """Reset for new conversation."""
        self._reset_tracking()
    
    def has_struggles(self) -> bool:
        """Check if any struggles detected."""
        return (
            self._indicators["high_iterations"] or
            self._indicators["tool_confusion"] or
            self._indicators["context_loss"]
        )
```

**What this does:**
1. **Tracks** every iteration and tool call
2. **Detects** three struggle patterns
3. **Reports** statistics for display

**When it triggers:**
- High iterations: 4+ iterations
- Tool confusion: 2+ tools called at once
- Context loss: Same tool used 3+ times

### Integrate into Workflow

Update `stage_2/agents/workflow.py` to use struggle monitoring:

```python
"""Workflow with struggle monitoring."""

from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition

from stage_2.agents.state import AgentState
from stage_2.agents.react_agent import ReactAgent
from common.monitoring.struggle_analyzer import StruggleAnalyzer


class AgentWorkflow:
    """Workflow with struggle monitoring."""
    
    def __init__(self):
        """Initialize workflow and monitoring."""
        self.agent = ReactAgent()
        self.struggle_analyzer = StruggleAnalyzer(stage=2)
        self.workflow = self._build_graph()
    
    def _agent_with_monitoring(self, state: AgentState) -> dict:
        """
        Wrapper that adds struggle detection.
        
        This is the key innovation in Stage 2:
        We monitor the agent as it works.
        """
        iterations = state.get("iterations", 0)
        
        # Check iteration count
        self.struggle_analyzer.analyze_iteration(iterations)
        
        # Call agent (same as always)
        result = self.agent.call_model(state)
        
        # Check tool calls
        new_messages = result.get("messages", [])
        if new_messages:
            msg = new_messages[-1]
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                tool_names = [tc["name"] for tc in msg.tool_calls]
                self.struggle_analyzer.analyze_tool_calls(tool_names)
        
        return result
    
    def _build_graph(self):
        """Build graph - same structure as Stage 1."""
        graph = StateGraph(AgentState)
        
        # Use wrapped agent with monitoring
        graph.add_node("agent", self._agent_with_monitoring)
        graph.add_node("tools", ToolNode(self.agent.tools))
        
        graph.add_edge(START, "agent")
        graph.add_conditional_edges(
            "agent",
            tools_condition,
            {"tools": "tools", END: END}
        )
        graph.add_edge("tools", "agent")
        
        return graph.compile()
    
    def run(self, user_input: str) -> str:
        """Run the agent and return results with struggle stats."""
        # Reset monitoring for new conversation
        self.struggle_analyzer.reset()
        
        print(f"\nUser: {user_input}\n")
        
        # Run workflow
        result = self.workflow.invoke({
            "messages": [HumanMessage(content=user_input)],
            "iterations": 0
        })
        
        # Get final response
        response = result["messages"][-1].content
        
        # Show struggle stats
        if self.struggle_analyzer.has_struggles():
            print("\n" + "="*60)
            print("STRUGGLES DETECTED:")
            stats = self.struggle_analyzer.get_stats()
            if stats["high_iterations"]:
                print(f"  ⚠️  High iterations: {stats['iteration_count']}")
            if stats["tool_confusion"]:
                print(f"  ⚠️  Tool confusion: {stats['unique_tools']} tools")
            if stats["context_loss"]:
                print(f"  ⚠️  Context loss: {stats['repeated_tools']}")
            print("="*60 + "\n")
        
        print(f"Agent: {response}\n")
        return response
```

**The magic:**
- Wraps the agent node with monitoring
- Same graph structure as Stage 1
- Automatically detects and reports struggles
- No changes needed to agent logic

---

## Step 4: Test Your Stage 2 Agent

Create `stage_2/demo.py` to see it in action:

```python
"""Demo showing Stage 2 agent struggles."""

from stage_2.agents.workflow import AgentWorkflow


def main():
    """Run demo scenarios."""
    print("\n" + "="*60)
    print("STAGE 2: AGENT WITH 7 TOOLS")
    print("="*60)
    
    workflow = AgentWorkflow()
    
    # Simple scenario (works fine)
    print("\n--- SIMPLE SCENARIO (Should work smoothly) ---")
    workflow.run("What's the status of order #12345?")
    
    input("Press Enter for complex scenario...")
    
    # Complex scenario (triggers struggles)
    print("\n--- COMPLEX SCENARIO (Will trigger struggles) ---")
    workflow.run(
        "My order #12345 hasn't arrived, I want a refund or "
        "expedited shipping, and do you have it in blue?"
    )
    
    print("\nNotice the difference!")
    print("- Simple query: Fast, no struggles")
    print("- Complex query: Multiple iterations, tool confusion")


if __name__ == "__main__":
    main()
```

**Run it:**
```bash
python stage_2/demo.py
```

**What to observe:**
1. Simple query: 1-2 iterations, single tool, no struggles
2. Complex query: 4+ iterations, multiple tools, struggles detected

---

## Understanding What You Built

### The Key Insight

Stage 2 proves that **more capabilities ≠ better performance**.

**Same architecture:**
- State: Identical
- ReAct pattern: Identical
- Graph structure: Identical

**Different results:**
- Stage 1 (2 tools): Smooth operation
- Stage 2 (7 tools): Struggles appear

**Why?**
- More choices = harder decisions
- No planning capability
- Sequential processing
- Context limitations

### When Struggles Happen

**High Iterations:**
```
User: "Complex request..."
Agent: Calls tool 1
Agent: Calls tool 2
Agent: Calls tool 3
Agent: Still not sure... calls tool 4
Struggle Analyzer: "⚠️  High iterations (4)"
```

**Tool Confusion:**
```
User: "My order is late, refund or expedite?"
Agent: Calls BOTH process_refund AND modify_shipping at once
Struggle Analyzer: "⚠️  Tool confusion"
```

**Context Loss:**
```
Agent: Calls check_inventory for "blue"
Agent: Calls check_inventory for "blue" again (forgot result)
Agent: Calls check_inventory for "blue" third time
Struggle Analyzer: "⚠️  Context loss"
```

### The Struggle Monitoring System

**How it works:**
1. Wraps agent calls with monitoring
2. Tracks iterations and tool calls
3. Compares against thresholds
4. Detects patterns
5. Reports findings

**Why it matters:**
- Makes problems visible
- Helps identify improvements
- Shows when agents need help
- Motivates better solutions

---

## Adding Optional Checkpointing

Checkpointing adds conversation memory. The agent can remember previous messages.

### Update Workflow for Checkpointing

```python
from langgraph.checkpoint.memory import MemorySaver

class AgentWorkflow:
    def __init__(self, enable_checkpointing: bool = False):
        self.agent = ReactAgent()
        self.struggle_analyzer = StruggleAnalyzer(stage=2)
        self.enable_checkpointing = enable_checkpointing
        self.workflow = self._build_graph()
    
    def _build_graph(self):
        graph = StateGraph(AgentState)
        # ... add nodes and edges ...
        
        # Compile with optional checkpointing
        if self.enable_checkpointing:
            checkpointer = MemorySaver()
            return graph.compile(checkpointer=checkpointer)
        else:
            return graph.compile()
```

**What this does:**
- If enabled: Saves state after each message
- Agent can reference previous messages
- Follow-up questions work naturally

**Example:**
```python
# First message
workflow.run("What's order #12345?", thread_id="user-123")

# Second message - agent remembers!
workflow.run("What order did I just ask about?", thread_id="user-123")
# Agent: "You asked about order #12345"
```

---

## Common Issues

### Issue 1: Agent still works fine with 7 tools
**Problem**: Not seeing struggles
**Solution**: Try more complex queries with multiple sub-tasks

### Issue 2: Too many struggle warnings
**Problem**: Warnings on every query
**Solution**: Adjust thresholds in StruggleThresholds class

### Issue 3: Imports not found
**Problem**: Can't import STAGE_2_TOOLS
**Solution**: Make sure `common/tools/__init__.py` exports them

---

## What You've Accomplished

You've built Stage 2 and learned:

✅ How to add new tools to an existing agent
✅ Why more tools creates complexity
✅ How to detect agent struggles automatically
✅ How to add conversation memory (checkpointing)
✅ When single agents reach their limits

## Key Takeaways

**Adding tools is easy:**
```python
@tool
def my_new_tool(param: str) -> str:
    """What it does."""
    return result

STAGE_2_TOOLS = existing_tools + [my_new_tool]
```

**Monitoring struggles:**
```python
analyzer = StruggleAnalyzer()
analyzer.analyze_iteration(iterations)
analyzer.analyze_tool_calls(tool_calls)
stats = analyzer.get_stats()
```

**The limitation:**
More tools without better planning = struggles

## Next Steps

You've seen the problem. Now see the solutions:

**Stage 3** introduces advanced patterns that handle complexity:
- ReWOO: Plans all tool calls upfront
- Reflection: Self-evaluates responses
- Plan-and-Execute: Creates adaptive plans

These patterns handle the complex scenarios that break Stage 2.

The lesson: **Don't just add tools - add planning!**