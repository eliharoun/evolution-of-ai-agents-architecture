# Building Stage 4: Multi-Agent System with Supervisor

Welcome to Stage 4! In this tutorial, you'll learn a completely different way to build AI systems. Instead of making one agent handle everything, you'll create a team of specialist agents coordinated by a supervisor.

Think of it like a real customer service team: you have specialists who handle orders, products, and accounts, plus a team lead who directs customers to the right person.

## What You'll Learn

- How to divide work among specialist agents
- How to create focused agents with specific tools
- How to build a supervisor that coordinates specialists
- How to enable parallel execution
- Why specialization is better than generalization
- How to use LangGraph's built-in supervisor function

## Prerequisites

Before starting, you should have:
- Completed Stages 1, 2, and 3 tutorials
- Understanding of ReAct pattern
- Familiarity with tool creation
- The 7 tools from Stage 2 available

## Tutorial Overview

We'll build the multi-agent system in 5 steps:
1. Understand the multi-agent mental model
2. Create three specialist agents
3. Write prompts for each specialist
4. Build the supervisor coordination
5. Test the team working together

The key insight: **Divide and conquer through specialization.**

Let's start!

---

## Step 1: Understanding Multi-Agent Systems

Before coding, let's understand why we're moving from one agent to many.

### The Single Agent Problem

In Stages 1-3, we had one agent handling everything:

**Stage 2 Issues:**
- 7 tools to choose from
- Confusion about which tool to use
- No clear organization
- Jack of all trades, master of none

**Stage 3 Improvements:**
- Better planning (ReWOO)
- More efficient execution
- But still one agent doing everything

### The Multi-Agent Solution

Instead of one generalist, create a team of specialists:

```
Single Agent Approach:
┌─────────────────────────────┐
│   One Agent                 │
│   - 7 tools                 │
│   - All responsibilities    │
│   - Gets confused           │
└─────────────────────────────┘

Multi-Agent Approach:
┌─────────────────────────────┐
│   Supervisor                │
│   - Coordinates team        │
│   - No tools, just delegates│
└─────────┬───────────────────┘
          ↓
    ┌─────┴─────┬─────────────┐
    ↓           ↓             ↓
┌─────────┐ ┌─────────┐ ┌─────────┐
│ Order   │ │ Product │ │ Account │
│ Agent   │ │ Agent   │ │ Agent   │
│ 3 tools │ │ 2 tools │ │ 2 tools │
└─────────┘ └─────────┘ └─────────┘
```

**Why this works:**
- Each specialist masters their domain
- Supervisor handles coordination
- Clear division of responsibilities
- Can work in parallel

### Real-World Analogy

**Bad customer service:**
One person handles everything:
- Orders, products, accounts, billing, technical support
- Gets overwhelmed
- Makes mistakes
- Slow service

**Good customer service:**
Team with specialists:
- Order specialist handles shipping and tracking
- Product specialist knows inventory
- Account specialist manages customer data
- Team lead directs customers to right person
- Fast, accurate service

We're building the good version!

---

## Step 2: Design Your Specialist Agents

First decision: How do we divide the 7 tools among specialists?

### Division Strategy

**Think about natural groupings:**

1. **Orders** - What's related to order lifecycle?
   - Checking order status
   - Modifying shipping
   - Processing refunds
   - Tools: 3 (order_status, modify_shipping, process_refund)

2. **Products** - What's related to products?
   - Checking inventory
   - Answering product questions (via FAQ)
   - Tools: 2 (check_inventory, search_faq)

3. **Accounts** - What's related to customers?
   - Getting account information
   - Escalating complex issues
   - Tools: 2 (get_customer_account, create_ticket)

**The result:** Three specialists with 2-3 tools each. Much more manageable!

---

## Step 3: Create the Specialist Agents

Now let's build the three specialists.

Create `stage_4/common/specialist_agents.py`:

```python
"""Specialist agents for multi-agent system."""

from typing import Optional, Any
from langchain_core.language_models import BaseChatModel
from langgraph.prebuilt import create_react_agent

# Import tools
from common.tools import (
    get_order_status,
    modify_shipping,
    process_refund,
    check_inventory,
    search_faq,
    get_customer_account,
    create_ticket,
)

# We'll create prompts in next step
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
    Create the Order Operations specialist.
    
    This agent is an expert in everything order-related:
    - Tracking orders
    - Modifying shipping
    - Processing refunds
    
    It's just a ReAct agent (like Stage 1) but focused!
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
    Create the Product & Inventory specialist.
    
    This agent is an expert in:
    - Product availability
    - Inventory checking
    - FAQ knowledge base
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
    Create the Customer Account specialist.
    
    This agent is an expert in:
    - Customer account information
    - Escalating complex issues
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
    Convenience function to create all specialists at once.
    
    Returns a dictionary mapping names to agents:
    {
        "order_operations": agent,
        "product_inventory": agent,
        "customer_account": agent
    }
    """
    return {
        "order_operations": create_order_operations_agent(model, checkpointer),
        "product_inventory": create_product_inventory_agent(model, checkpointer),
        "customer_account": create_customer_account_agent(model, checkpointer),
    }
```

**What's happening:**

1. **`create_react_agent()`**: LangGraph's built-in function
   - Creates a ReAct agent (like Stage 1)
   - Takes model, tools, and prompt
   - Returns a compiled agent

2. **Each specialist function**:
   - Receives shared model
   - Gets specific tools for their domain
   - Uses specialized prompt
   - Returns ready-to-use agent

3. **`create_all_specialists()`**:
   - Convenience function
   - Creates all three at once
   - Returns dictionary for easy lookup

**The beauty:** Each specialist is just a simple ReAct agent. They're identical in structure to Stage 1, just with different tools and prompts.

---

## Step 4: Write Specialist Prompts

Each specialist needs instructions tailored to their domain.

Create `stage_4/common/specialist_prompts.py`:

```python
"""Prompts for specialist agents."""

# Order Operations Specialist
ORDER_OPERATIONS_PROMPT = """You are an Order Operations Specialist.

Your job is to help with anything related to orders:
- Checking order status and tracking
- Modifying shipping (expedite, change address)
- Processing refunds and returns

Your tools:
- get_order_status: Look up order details
- modify_shipping: Change delivery options
- process_refund: Initiate refunds

Guidelines:
- Always check order status before making changes
- Be empathetic with delayed orders
- Explain what you're doing clearly
- If order is already delivered, explain why changes aren't possible
- Provide realistic timelines

Remember: You're the order expert. Focus on order-related tasks only.
"""

# Product & Inventory Specialist
PRODUCT_INVENTORY_PROMPT = """You are a Product & Inventory Specialist.

Your job is to help with anything related to products:
- Checking product availability and variants
- Answering questions about products
- Searching policies and information in FAQ

Your tools:
- check_inventory: Check product stock and variants
- search_faq: Search knowledge base for policies

Guidelines:
- Always verify actual inventory levels
- Suggest alternatives when items are out of stock
- Be specific about colors, sizes, and variants
- Use FAQ tool for policy questions
- Help customers find what they're looking for

Remember: You're the product expert. Focus on product-related tasks only.
"""

# Customer Account Specialist
CUSTOMER_ACCOUNT_PROMPT = """You are a Customer Account Specialist.

Your job is to help with anything related to customer accounts:
- Looking up account information and history
- Escalating complex issues to human support

Your tools:
- get_customer_account: Get customer details and history
- create_ticket: Create support tickets for complex issues

Guidelines:
- Use account history to provide personalized support
- Respect customer privacy
- Escalate when issues are beyond your capability
- Include all relevant details in tickets
- Be professional and thorough

Remember: You're the account expert. Focus on account-related tasks only.
"""
```

**Understanding the prompts:**

1. **Clear identity**: Each specialist knows their role
2. **Specific tools**: Lists exactly what they can do
3. **Domain guidelines**: Instructions relevant to their area
4. **Focus**: Keeps them in their lane

**Why this matters:**
- Specialists don't try to handle other domains
- Clear boundaries prevent confusion
- Each can be optimized for their area

---

## Step 5: Create the Supervisor Prompt

The supervisor is special - it's customer-facing and coordinates behind the scenes.

Create `stage_4/common/supervisor_prompts.py`:

```python
"""Supervisor prompt for multi-agent coordination."""

SUPERVISOR_PROMPT = """You are a friendly customer support representative.

You work with a team of specialists:
- **order_operations**: Handles orders, shipping, refunds
- **product_inventory**: Handles products, inventory, policies
- **customer_account**: Handles accounts, escalations

Your job:
1. Understand what the customer needs
2. Consult the right specialist(s) to get accurate information
3. Present everything naturally and helpfully

Communication style:
- Warm and empathetic
- Conversational and natural
- Professional but friendly
- Solution-focused

IMPORTANT - Be human, not robotic:

Bad: "I delegated to the order operations specialist."
Good: "Let me check on that order for you."

Bad: "The specialist reports the following data."
Good: "I can see that your order..."

Bad: "Multiple specialists were consulted in parallel."
Good: "I checked on a few things for you..."

Remember: Customers talk to YOU, not a committee. Present specialist 
information as if you personally helped them. Keep responses conversational 
and concise.
"""
```

**What makes this prompt special:**

1. **Customer-facing**: Supervisor is who customers interact with
2. **Coordination**: Knows which specialists to use
3. **Natural presentation**: Hides the delegation mechanics
4. **Examples**: Shows good vs bad communication

**The key:** Seamless coordination that feels like talking to one person.

---

## Step 6: Build the Supervisor Workflow

Now we connect everything using LangGraph's built-in supervisor.

Create `stage_4/supervisor_1/agents/workflow.py`:

```python
"""Supervisor workflow using LangGraph's create_supervisor."""

from typing import Optional
from langchain_core.messages import HumanMessage
from langgraph_supervisor import create_supervisor

from stage_4.common.specialist_agents import create_all_specialists
from stage_4.common.supervisor_prompts import SUPERVISOR_PROMPT
from common.model_factory import ModelFactory, ModelType


class SupervisorWorkflow:
    """
    Multi-agent workflow with supervisor coordination.
    
    Structure:
    - 3 specialist agents (order, product, account)
    - 1 supervisor agent (coordinates specialists)
    """
    
    def __init__(
        self,
        model_type: ModelType = "openai",
        enable_checkpointing: bool = False
    ):
        """Initialize the supervisor workflow."""
        # Create the model
        self.model = ModelFactory.create_model(
            model_type=model_type,
            model_name="gpt-4o-mini",
            temperature=0
        )
        
        # Create checkpointer if needed
        self.checkpointer = None
        if enable_checkpointing:
            from langgraph.checkpoint.memory import MemorySaver
            self.checkpointer = MemorySaver()
        
        # Create all three specialist agents
        print("Creating specialist agents...")
        self.specialists = create_all_specialists(
            self.model,
            self.checkpointer
        )
        print(f"Created {len(self.specialists)} specialists")
        
        # Build the supervisor
        self.workflow = self._build_graph()
        print("Supervisor workflow ready!")
    
    def _build_graph(self):
        """
        Build the supervisor graph.
        
        This is where the magic happens - we use LangGraph's
        create_supervisor() to handle all the coordination logic.
        """
        print("Building supervisor coordination...")
        
        # Get specialists as a list
        specialist_agents = list(self.specialists.values())
        
        # Create supervisor using built-in function
        supervisor_graph = create_supervisor(
            agents=specialist_agents,        # The team
            model=self.model,                # Supervisor's brain
            prompt=SUPERVISOR_PROMPT,        # How to coordinate
            parallel_tool_calls=True,        # Enable parallel work
            output_mode="last_message",      # Clean output
        )
        
        # Compile
        return supervisor_graph.compile(
            checkpointer=self.checkpointer
        )
    
    def run(self, user_input: str, thread_id: str = "default") -> str:
        """Run the multi-agent system."""
        print(f"\n{'='*60}")
        print(f"Customer: {user_input}")
        print(f"{'='*60}\n")
        
        # Create initial state
        initial_state = {
            "messages": [HumanMessage(content=user_input)]
        }
        
        # Configure for checkpointing if enabled
        config = {"configurable": {"thread_id": thread_id}} if self.checkpointer else None
        
        # Execute workflow
        if config:
            result = self.workflow.invoke(initial_state, config)
        else:
            result = self.workflow.invoke(initial_state)
        
        # Extract response
        final_message = result["messages"][-1]
        response = final_message.content
        
        print(f"\nAgent: {response}")
        print(f"{'='*60}\n")
        
        return response
```

**Understanding the code:**

1. **Initialization**:
   - Creates one model (shared by all agents)
   - Creates three specialists
   - Builds supervisor coordination

2. **`create_supervisor()`**:
   - Takes list of specialist agents
   - Takes supervisor's model and prompt
   - Returns a graph that handles coordination
   - We don't write coordination logic - it's built-in!

3. **Key parameters**:
   - `parallel_tool_calls=True`: Specialists can work simultaneously
   - `output_mode="last_message"`: Clean, simple output

**The magic:** LangGraph handles all the complex coordination logic. We just provide the pieces.

---

## Step 7: Test Your Multi-Agent System

Create `stage_4/supervisor_1/demo.py`:

```python
"""Demo showing multi-agent coordination."""

from stage_4.supervisor_1.agents.workflow import SupervisorWorkflow


def main():
    """Run demo scenarios."""
    print("\n" + "="*60)
    print("STAGE 4: MULTI-AGENT SYSTEM")
    print("="*60)
    
    workflow = SupervisorWorkflow(
        model_type="openai",
        enable_checkpointing=False
    )
    
    # Scenario 1: Single specialist
    print("\n--- SINGLE SPECIALIST QUERY ---")
    workflow.run("What's the status of order #12345?")
    print("→ Only Order Operations specialist was needed")
    
    input("Press Enter for multi-specialist scenario...")
    
    # Scenario 2: Multiple specialists
    print("\n--- MULTI-SPECIALIST QUERY ---")
    workflow.run(
        "Check order #12345, do you have it in blue, "
        "and show me my account history"
    )
    print("→ All three specialists worked in parallel!")
    
    input("Press Enter for complex scenario...")
    
    # Scenario 3: Complex coordination
    print("\n--- COMPLEX SCENARIO ---")
    workflow.run(
        "My order #12345 is late, I want expedited shipping or a refund, "
        "and do you have it in blue instead?"
    )
    print("→ Supervisor coordinated order and product specialists")


if __name__ == "__main__":
    main()
```

**Run it:**
```bash
python stage_4/supervisor_1/demo.py
```

**What you'll see:**
1. Supervisor analyzing the query
2. Specialists being called
3. Results being combined
4. Natural final response

---

## Step 8: Understanding Execution Flow

Let's trace through a complex example step by step.

### Example Query
"Check my order #12345 and do you have it in blue?"

### Detailed Execution

**Phase 1: Supervisor Receives Query**
```
Input: "Check my order #12345 and do you have it in blue?"

Supervisor analyzes:
"This has two parts:
1. Order status - need Order Operations
2. Product availability - need Product & Inventory"
```

**Phase 2: Supervisor Delegates (Parallel)**
```
Supervisor → order_operations: "Check order #12345"
Supervisor → product_inventory: "Check if available in blue"

Both specialists work at the same time!
```

**Phase 3: Order Operations Works**
```
Order Operations agent:
1. Receives: "Check order #12345"
2. Thinks: "Need to use get_order_status"
3. Executes: get_order_status("12345")
4. Gets: "Order delivered Nov 4, Blue Jeans Size 32..."
5. Returns: Formatted order information
```

**Phase 4: Product & Inventory Works (Simultaneously)**
```
Product & Inventory agent:
1. Receives: "Check if available in blue"
2. Thinks: "Need product context... checking inventory for blue items"
3. Executes: check_inventory("jeans", "blue")
4. Gets: "Blue variant available, 5 in stock"
5. Returns: Availability information
```

**Phase 5: Supervisor Synthesizes**
```
Supervisor receives:
- From Order Operations: Order details
- From Product & Inventory: Blue variant available

Supervisor combines:
"Your order #12345 was delivered on November 4th! And yes, 
we do have those jeans available in blue with 5 units in stock. 
Would you like to order a pair?"
```

**Phase 6: Customer Gets Response**

Natural, complete answer addressing both questions. Customer doesn't know multiple agents were involved.

---

## Step 9: Understanding Parallel Execution

The supervisor can run specialists in parallel when their tasks are independent.

### When Parallel Execution Happens

**Independent tasks:**
```
Query: "Check order #12345 and inventory for blue shirts"

Supervisor thinks:
"Order check doesn't depend on inventory check"
"These can run simultaneously"

Timeline:
0s: Both specialists start
2s: Both specialists finish
Total: 2 seconds
```

**Dependent tasks:**
```
Query: "Refund order #12345"

Supervisor thinks:
"Need to check order status first"
"Then can process refund"

Timeline:
0s: Order Operations checks status
2s: Order Operations processes refund
Total: 2 seconds (sequential)
```

**The supervisor decides automatically** based on task dependencies.

---

## Step 10: The Power of Built-in Functions

This implementation uses `create_supervisor()` from LangGraph. Let's understand what that gives us.

### What create_supervisor() Does

**Automatically handles:**
- Routing logic (which specialist for what)
- Parallel execution (when possible)
- Message passing (specialist ↔ supervisor)
- State management (tracking who did what)
- Error handling (specialist failures)

**We just provide:**
- List of specialists
- Supervisor's model
- Coordination prompt

**The code is simple:**
```python
supervisor_graph = create_supervisor(
    agents=specialist_agents,
    model=self.model,
    prompt=SUPERVISOR_PROMPT,
    parallel_tool_calls=True,
)
```

That's it! LangGraph does the rest.

### Advantages

**Quick Setup:**
- Minimal code
- Few opportunities for bugs
- Fast to implement

**Production Ready:**
- Well-tested by LangGraph team
- Handles edge cases
- Regular updates

**Standard Patterns:**
- Industry best practices
- Common coordination strategies
- Known to work well

### Trade-offs

**Less Transparency:**
- Don't see coordination logic
- Harder to debug delegation
- Black box behavior

**Less Customization:**
- Standard patterns only
- Can't easily modify routing
- Limited flexibility

**For learning:** This is why Stage 4 has Supervisor v2 - to show how it works under the hood.

---

## Comparing Approaches

### Stage 2: One Agent, 7 Tools
```
Customer: "Order #12345, is it in blue?"

Single agent:
- Thinks: "Which tool first?"
- Uses: get_order_status
- Thinks: "What next?"
- Uses: check_inventory
- Thinks: "Done?"
- Responds

Problems: Tool confusion, many LLM calls
```

### Stage 4: Supervisor + 3 Specialists
```
Customer: "Order #12345, is it in blue?"

Supervisor:
- Analyzes: "Two domains: order and product"
- Delegates: order_operations AND product_inventory (parallel)

Order specialist:
- Focused: Only thinks about orders
- Uses: get_order_status
- Returns: Order info

Product specialist:
- Focused: Only thinks about products
- Uses: check_inventory
- Returns: Availability info

Supervisor:
- Combines: Both results
- Responds: Natural answer

Benefits: No confusion, parallel execution, clear organization
```

The difference is structural, not just implementation.

---

## Common Issues

### Issue 1: Specialists doing wrong tasks
**Problem**: Order specialist trying to check inventory
**Solution**: Check specialist prompts emphasize their scope

### Issue 2: Supervisor not delegating
**Problem**: Supervisor tries to answer directly
**Solution**: Ensure supervisor prompt emphasizes consulting specialists

### Issue 3: Responses mentioning "specialists"
**Problem**: "The order operations specialist reports..."
**Solution**: Supervisor prompt should teach natural presentation

### Issue 4: Import errors
**Problem**: Can't find specialist_agents or prompts
**Solution**: Ensure common/ directory is in Python path

---

## What You've Accomplished

You've built a multi-agent system and learned:

✅ How to divide tools among specialist agents
✅ How to create focused agents with domain expertise
✅ How to build a supervisor that coordinates specialists
✅ How to enable parallel execution for efficiency
✅ Why specialization beats generalization
✅ How to use LangGraph's built-in supervisor function

## Key Takeaways

**Creating specialists:**
```python
specialist = create_react_agent(
    model=model,
    tools=[tool1, tool2],
    prompt=specialist_prompt,
    name="specialist_name"
)
```

**Creating supervisor:**
```python
supervisor = create_supervisor(
    agents=[specialist1, specialist2, specialist3],
    model=model,
    prompt=supervisor_prompt,
    parallel_tool_calls=True
)
```

**The pattern:**
- Divide tools by domain
- Create specialist for each domain
- Supervisor coordinates
- Present naturally to customers

## Next Steps

You've learned the quick, built-in approach. Now go deeper:

**Explore Supervisor v2:**
- See how coordination actually works
- Understand delegation logic
- Learn to customize behavior
- Build it from scratch

**Try modifications:**
1. Add a 4th specialist (e.g., billing)
2. Adjust specialist boundaries
3. Modify coordination prompts
4. Test with complex scenarios

**Compare patterns:**
- Single agent (Stages 1-3)
- Multi-agent (Stage 4)
- Which works better for what?

The lesson: **Specialization + coordination > one generalist**
