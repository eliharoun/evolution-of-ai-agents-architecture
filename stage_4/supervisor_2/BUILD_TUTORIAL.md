# Building Stage 4 Supervisor v2: Custom Multi-Agent Implementation

Welcome to the custom supervisor tutorial! In Supervisor v1, you used LangGraph's built-in function to create a multi-agent system quickly. Now you'll build the same system from scratch to understand exactly how it works.

This is like the difference between using a library function and implementing it yourself - you'll understand the mechanics behind multi-agent coordination.

## What You'll Learn

- How to wrap agents as tools for other agents to use
- Why the supervisor is just a ReAct agent with high-level tools
- How information flows in multi-agent systems
- How to customize coordination logic
- The mechanics that built-in functions hide
- When to use custom vs built-in implementations

## Prerequisites

Before starting, you should have:
- Completed Stage 4 Supervisor v1 tutorial
- Understanding of the supervisor pattern concept
- Familiarity with ReAct agents
- The three specialist agents from Supervisor v1

## Tutorial Overview

We'll build the custom supervisor in 4 main steps:
1. Understand why we're building this custom version
2. Create specialist tool wrappers (the key innovation)
3. Build the supervisor as a standard ReAct agent
4. Test and compare with Supervisor v1

The key insight: **Specialists are just tools from the supervisor's perspective.**

Let's begin!

---

## Step 1: Understanding the Custom Approach

Before coding, let's understand what we're building and why.

### What Supervisor v1 Hides

In Supervisor v1, you used this:

```python
supervisor = create_supervisor(
    agents=[order_agent, product_agent, account_agent],
    model=model,
    prompt=prompt
)
```

**What happens inside create_supervisor():**
1. Takes specialist agents
2. Wraps them as tools somehow
3. Creates a supervisor somehow
4. Handles coordination somehow

You don't see the "somehow" - it's hidden inside the function.

### What Supervisor v2 Reveals

In Supervisor v2, you'll implement the "somehow" yourself:

```python
# Step 1: Manually wrap specialists as tools
@tool
def specialist_order_operations(request: str) -> str:
    result = order_agent.invoke({"messages": [...]})
    return result["messages"][-1].content

# Step 2: Create supervisor as standard ReAct agent
supervisor = create_react_agent(
    model=model,
    tools=[specialist_order_operations, ...],  # Your wrapped tools
    prompt=prompt
)
```

**Now you see:**
- How specialists become tools
- How supervisor uses them
- How results flow back

### The Key Insight

**Multi-agent coordination is just tool calling.**

From the supervisor's view:
- Specialists look like tools
- Calling a specialist is like calling any tool
- The tool just happens to run a complete agent workflow

From the specialist's view:
- Receives a request
- Does its job
- Returns a response
- Doesn't know it's being used as a tool

This pattern is called "agent composition" - building agents from other agents.

---

## Step 2: Create Specialist Tool Wrappers

This is the heart of the custom implementation. We'll wrap each specialist agent as a tool.

Create `stage_4/supervisor_2/agents/specialist_wrappers.py`:

```python
"""Wraps specialist agents as tools for the supervisor."""

from langchain_core.tools import tool
from langchain_core.language_models import BaseChatModel

from stage_4.common.specialist_agents import (
    create_order_operations_agent,
    create_product_inventory_agent,
    create_customer_account_agent,
)


def create_specialist_tool_wrappers(
    model: BaseChatModel,
    checkpointer = None
) -> list:
    """
    Create tool wrappers for all specialists.
    
    This is where the magic happens - we turn agents into tools!
    
    Returns:
        List of wrapped specialist tools
    """
    print("Creating specialist agents...")
    
    # Create the three specialist agents (same as Supervisor v1)
    order_agent = create_order_operations_agent(model, checkpointer)
    product_agent = create_product_inventory_agent(model, checkpointer)
    account_agent = create_customer_account_agent(model, checkpointer)
    
    print("Wrapping specialists as tools...")
    
    # Now wrap each one as a tool
    
    @tool
    def specialist_order_operations(request: str) -> str:
        """
        Consult the Order Operations specialist for order-related queries.
        
        Use this when customers need help with:
        - Checking order status and tracking
        - Modifying shipping (expedite, change address)
        - Processing refunds and returns
        
        Args:
            request: What you need help with regarding orders
            
        Returns:
            The specialist's response
        """
        print(f"\n  → Calling Order Operations specialist")
        print(f"    Request: {request[:60]}...")
        
        # Invoke the specialist agent
        result = order_agent.invoke({
            "messages": [{"role": "user", "content": request}]
        })
        
        # Extract the final response
        final_message = result["messages"][-1]
        response = final_message.content
        
        print(f"  ← Order Operations responded ({len(response)} chars)")
        
        return response
    
    @tool
    def specialist_product_inventory(request: str) -> str:
        """
        Consult the Product & Inventory specialist for product queries.
        
        Use this when customers need help with:
        - Checking product availability and variants
        - Finding product specifications
        - Learning about policies from FAQs
        
        Args:
            request: What you need help with regarding products
            
        Returns:
            The specialist's response
        """
        print(f"\n  → Calling Product & Inventory specialist")
        print(f"    Request: {request[:60]}...")
        
        # Invoke the specialist agent
        result = product_agent.invoke({
            "messages": [{"role": "user", "content": request}]
        })
        
        # Extract the final response
        final_message = result["messages"][-1]
        response = final_message.content
        
        print(f"  ← Product & Inventory responded ({len(response)} chars)")
        
        return response
    
    @tool
    def specialist_customer_account(request: str) -> str:
        """
        Consult the Customer Account specialist for account queries.
        
        Use this when customers need help with:
        - Viewing account information and history
        - Escalating complex issues
        
        Args:
            request: What you need help with regarding accounts
            
        Returns:
            The specialist's response
        """
        print(f"\n  → Calling Customer Account specialist")
        print(f"    Request: {request[:60]}...")
        
        # Invoke the specialist agent
        result = account_agent.invoke({
            "messages": [{"role": "user", "content": request}]
        })
        
        # Extract the final response
        final_message = result["messages"][-1]
        response = final_message.content
        
        print(f"  ← Customer Account responded ({len(response)} chars)")
        
        return response
    
    print(f"Created {3} specialist tool wrappers\n")
    
    # Return as list
    return [
        specialist_order_operations,
        specialist_product_inventory,
        specialist_customer_account,
    ]
```

**Understanding each wrapper:**

1. **Create specialist agent**: Standard agent creation (from Supervisor v1)
2. **Define wrapper function**: Uses `@tool` decorator
3. **Docstring**: Teaches supervisor when to use this specialist
4. **Invoke specialist**: Runs the complete agent workflow
5. **Extract response**: Gets specialist's final message
6. **Return**: Sends back to supervisor

**The pattern for all three:**
- Create agent
- Wrap as tool
- Tool invokes agent
- Return agent's response

**Why this works:**
- Supervisor sees specialists as simple tools
- Each tool call triggers an entire agent workflow
- From supervisor's perspective, no difference from regular tools

---

## Step 3: Build the Custom Supervisor

Now we create the supervisor using standard ReAct agent creation.

Create `stage_4/supervisor_2/agents/workflow.py`:

```python
"""Custom supervisor workflow."""

from typing import Optional
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent

from stage_4.supervisor_2.agents.specialist_wrappers import create_specialist_tool_wrappers
from stage_4.common.supervisor_prompts import SUPERVISOR_PROMPT
from common.model_factory import ModelFactory, ModelType


class CustomSupervisorWorkflow:
    """
    Custom supervisor implementation.
    
    The supervisor is just a ReAct agent where the "tools"
    are wrapped specialist agents.
    """
    
    def __init__(
        self,
        model_type: ModelType = "openai",
        enable_checkpointing: bool = False
    ):
        """Initialize the custom supervisor."""
        # Create model
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
        
        # Create specialist tool wrappers
        print("Setting up custom supervisor...")
        self.specialist_tools = create_specialist_tool_wrappers(
            model=self.model,
            checkpointer=self.checkpointer
        )
        print(f"Supervisor has {len(self.specialist_tools)} specialist tools\n")
        
        # Build the supervisor
        self.workflow = self._build_graph()
    
    def _build_graph(self):
        """
        Build the supervisor as a standard ReAct agent.
        
        This is the key difference from Supervisor v1:
        We use create_react_agent (standard) instead of
        create_supervisor (specialized).
        """
        print("Building supervisor as ReAct agent...")
        
        # Create supervisor as a ReAct agent
        # The "magic": tools are actually wrapped specialists
        supervisor = create_react_agent(
            model=self.model,
            tools=self.specialist_tools,  # Wrapped specialists!
            prompt=SUPERVISOR_PROMPT,
            checkpointer=self.checkpointer,
            name="custom_supervisor"
        )
        
        print("Custom supervisor ready!\n")
        return supervisor
    
    def run(self, user_input: str, thread_id: str = "default") -> str:
        """Run the custom supervisor system."""
        print(f"\n{'='*60}")
        print(f"Customer: {user_input}")
        print(f"{'='*60}\n")
        
        # Create initial state
        initial_state = {
            "messages": [HumanMessage(content=user_input)]
        }
        
        # Configure for checkpointing if enabled
        config = None
        if self.checkpointer:
            config = {"configurable": {"thread_id": thread_id}}
        
        # Execute workflow
        if config:
            result = self.workflow.invoke(initial_state, config)
        else:
            result = self.workflow.invoke(initial_state)
        
        # Extract response
        final_message = result["messages"][-1]
        response = final_message.content
        
        print(f"\n{'='*60}")
        print(f"Supervisor: {response}")
        print(f"{'='*60}\n")
        
        return response
```

**Understanding the code:**

1. **Initialization**:
   - Creates model (same as always)
   - Creates specialist tool wrappers (NEW!)
   - Builds supervisor with wrapped tools

2. **`_build_graph()`**:
   - Uses `create_react_agent()` (standard function)
   - Passes wrapped specialists as tools
   - No special supervisor logic needed!

3. **The key line:**
   ```python
   tools=self.specialist_tools  # These are wrapped specialists
   ```
   - Supervisor thinks these are regular tools
   - Actually, each is a complete agent workflow
   - Transparent to the supervisor

**The insight:** The supervisor is just a regular ReAct agent. The only difference is its tools are wrapped agents instead of simple functions.

---

## Step 4: Test Your Custom Supervisor

Create `stage_4/supervisor_2/demo.py`:

```python
"""Demo for custom supervisor implementation."""

from stage_4.supervisor_2.agents.workflow import CustomSupervisorWorkflow


def main():
    """Run demo scenarios."""
    print("\n" + "="*60)
    print("STAGE 4 SUPERVISOR 2: CUSTOM IMPLEMENTATION")
    print("="*60)
    
    workflow = CustomSupervisorWorkflow(
        model_type="openai",
        enable_checkpointing=False
    )
    
    # Scenario 1: Single specialist
    print("\n--- SCENARIO 1: SINGLE SPECIALIST ---")
    workflow.run("What's the status of order #12345?")
    
    input("Press Enter to continue...")
    
    # Scenario 2: Multiple specialists
    print("\n--- SCENARIO 2: MULTIPLE SPECIALISTS ---")
    workflow.run(
        "Check order #12345, do you have it in blue, "
        "and show me my account history"
    )
    
    input("Press Enter to continue...")
    
    # Scenario 3: Complex coordination
    print("\n--- SCENARIO 3: COMPLEX COORDINATION ---")
    workflow.run(
        "My order #12345 is late, I want expedited shipping or refund, "
        "and do you have it in blue?"
    )
    
    print("\n" + "="*60)
    print("Notice:")
    print("- Supervisor calls specialists as tools")
    print("- Each call runs a complete agent workflow")
    print("- Same results as Supervisor v1, but transparent!")
    print("="*60)


if __name__ == "__main__":
    main()
```

**Run it:**
```bash
python stage_4/supervisor_2/demo.py
```

**What you'll see:**
- Supervisor analyzing query
- Calling specialists (showing "→" and "←")
- Each specialist running its workflow
- Final synthesized response

The logging shows the flow clearly!

---

## Step 5: Understanding the Execution Flow

Let's trace through a query to see how everything connects.

### Example Query
"Check order #12345 and do you have it in blue?"

### Detailed Trace

**Phase 1: Supervisor Receives Query**
```
Customer message arrives
    ↓
Supervisor (ReAct agent):
- Reads: "Check order #12345 and do you have it in blue?"
- Sees available tools:
  * specialist_order_operations (looks like a tool)
  * specialist_product_inventory (looks like a tool)
  * specialist_customer_account (looks like a tool)
- Thinks: "Two tasks: order status + product availability"
- Decides: "I'll use specialist_order_operations and specialist_product_inventory"
```

**Phase 2: First Tool Call (Order Specialist)**
```
Supervisor calls tool:
{
  name: "specialist_order_operations",
  args: {request: "Check order #12345"}
}
    ↓
Tool wrapper receives call:
- Gets request: "Check order #12345"
- Invokes: order_agent.invoke(...)
    ↓
Order Operations agent (full ReAct workflow):
- Iteration 1: Thinks: "Need get_order_status tool"
- Iteration 1: Calls: get_order_status("12345")
- Iteration 2: Observes: Order details
- Iteration 2: Responds: "Order #12345 delivered Nov 4..."
    ↓
Tool wrapper extracts response:
- Gets: "Order #12345 delivered Nov 4..."
- Returns to supervisor
    ↓
Supervisor receives tool result:
- Sees: ToolMessage with order details
- Stores: In message history
```

**Phase 3: Second Tool Call (Product Specialist)**
```
Supervisor calls tool:
{
  name: "specialist_product_inventory",
  args: {request: "Do you have it in blue?"}
}
    ↓
Tool wrapper receives call:
- Gets request: "Do you have it in blue?"
- Invokes: product_agent.invoke(...)
    ↓
Product & Inventory agent (full ReAct workflow):
- Iteration 1: Thinks: "Need check_inventory tool"
- Iteration 1: Calls: check_inventory("jeans", "blue")
- Iteration 2: Observes: "Blue variant available, 5 in stock"
- Iteration 2: Responds: Formatted availability info
    ↓
Tool wrapper extracts response:
- Gets: Availability information
- Returns to supervisor
    ↓
Supervisor receives tool result:
- Sees: ToolMessage with product details
- Stores: In message history
```

**Phase 4: Supervisor Synthesizes**
```
Supervisor now has:
- ToolMessage 1: Order information
- ToolMessage 2: Product availability

Supervisor (final iteration):
- Thinks: "I have everything I need"
- Synthesizes: Combines both results naturally
- Responds: "Your order was delivered on Nov 4! And yes, we have it in blue with 5 units in stock."
```

**Total flow:** Customer → Supervisor → Specialists → Supervisor → Customer

---

## Step 6: The Pattern Revealed

Now you understand the pattern. Let's make it explicit.

### The Tool Wrapping Pattern

**Template for wrapping any agent as a tool:**

```python
# Step 1: Create the agent
my_agent = create_some_agent(model, tools, prompt)

# Step 2: Wrap as tool
@tool
def specialist_my_domain(request: str) -> str:
    """Description of what this specialist does."""
    # Invoke the agent
    result = my_agent.invoke({
        "messages": [{"role": "user", "content": request}]
    })
    
    # Extract and return response
    return result["messages"][-1].content

# Step 3: Use as tool for another agent
supervisor = create_react_agent(
    model=model,
    tools=[specialist_my_domain, ...],
    prompt=supervisor_prompt
)
```

**This pattern is universal:**
- Works for any agent
- Works for any number of specialists
- Works with any underlying pattern (ReAct, ReWOO, etc.)

### Layered Agent Architecture

You can stack agents infinitely:

```
Level 1 agents: Use database tools
    ↓ wrapped as tools
Level 2 agents: Use Level 1 agents
    ↓ wrapped as tools
Level 3 agents: Use Level 2 agents
    ↓ wrapped as tools
Level N agents: Use Level N-1 agents
```

Each level abstracts complexity from below.

**Real-world example:**
- Data agents: Query databases
- Domain agents: Use data agents
- Supervisor: Uses domain agents
- Meta-supervisor: Uses multiple supervisors

You could build a whole hierarchy!

---

## Step 7: Customizing the Wrappers

The power of custom implementation is in customization. Here are patterns you can use.

### Pattern 1: Add Context

Pass additional context from supervisor to specialist:

```python
@tool
def specialist_order_operations(request: str) -> str:
    """Specialist with context."""
    # Get supervisor's conversation history
    supervisor_context = get_supervisor_history()
    
    # Add context to request
    enhanced_request = f"Context: {supervisor_context}\n\nRequest: {request}"
    
    result = order_agent.invoke({
        "messages": [{"role": "user", "content": enhanced_request}]
    })
    
    return result["messages"][-1].content
```

**Use case:** Specialist needs broader context to answer well.

### Pattern 2: Preprocess Requests

Validate or transform requests before calling specialist:

```python
@tool
def specialist_order_operations(request: str) -> str:
    """Specialist with preprocessing."""
    # Extract order ID
    order_id = extract_order_id(request)
    
    # Validate
    if not order_id:
        return "Please provide an order number"
    
    if not is_valid_order_id(order_id):
        return f"Invalid order number: {order_id}"
    
    # Call specialist with validated input
    result = order_agent.invoke(...)
    return result["messages"][-1].content
```

**Use case:** Ensure specialists receive clean, validated input.

### Pattern 3: Post-process Responses

Format or filter specialist responses:

```python
@tool
def specialist_order_operations(request: str) -> str:
    """Specialist with post-processing."""
    result = order_agent.invoke(...)
    response = result["messages"][-1].content
    
    # Format for supervisor
    formatted = format_response(response)
    
    # Add metadata
    enhanced = f"[Order Operations]: {formatted}"
    
    return enhanced
```

**Use case:** Standardize response format across specialists.

### Pattern 4: Add Error Handling

Handle specialist failures gracefully:

```python
@tool
def specialist_order_operations(request: str) -> str:
    """Specialist with error handling."""
    try:
        result = order_agent.invoke(...)
        return result["messages"][-1].content
    
    except TimeoutError:
        return "Order system temporarily unavailable. Please try again."
    
    except DatabaseError as e:
        return f"Unable to access order data: {e}"
    
    except Exception as e:
        # Log error
        log_error(f"Order Operations failed: {e}")
        # Return helpful message
        return "I encountered an issue. Let me create a support ticket for you."
```

**Use case:** Different error handling for different specialists.

---

## Step 8: Comparing Implementations

Let's compare Supervisor v1 and Supervisor v2 side by side.

### Code Comparison

**Supervisor v1 (Built-in):**
```python
# In workflow.py
from langgraph_supervisor import create_supervisor

supervisor = create_supervisor(
    agents=specialists,
    model=model,
    prompt=prompt,
    parallel_tool_calls=True
)

# That's it! ~10 lines total
```

**Supervisor v2 (Custom):**
```python
# In specialist_wrappers.py (~100 lines)
@tool
def specialist_order_operations(request: str) -> str:
    result = order_agent.invoke(...)
    return result["messages"][-1].content

# Repeat for each specialist

# In workflow.py (~50 lines)
specialist_tools = create_specialist_tool_wrappers(model)

supervisor = create_react_agent(
    model=model,
    tools=specialist_tools,
    prompt=prompt
)

# Total: ~150 lines
```

**More code, but educational value is higher.**

### Behavior Comparison

Run the same query through both:

```bash
# Supervisor v1
python -c "
from stage_4.supervisor_1.agents.workflow import SupervisorWorkflow
w = SupervisorWorkflow()
w.run('Check order #12345 and find it in blue')
"

# Supervisor v2
python -c "
from stage_4.supervisor_2.agents.workflow import CustomSupervisorWorkflow
w = CustomSupervisorWorkflow()
w.run('Check order #12345 and find it in blue')
"
```

**Results should be nearly identical!**

The difference:
- Supervisor v2 shows delegation clearly in logs
- Supervisor v1 hides the coordination
- Both produce same customer response

---

## Step 9: When to Use Each Approach

Now you understand both. When should you use each?

### Use Built-in (Supervisor v1) When:

**Production systems:**
- Need reliability
- Want quick deployment
- Standard patterns work
- Team prefers established tools

**Time-constrained projects:**
- Fast iteration needed
- Prototyping quickly
- MVP development

**Standard use cases:**
- Common coordination patterns
- No special requirements
- Follow best practices

### Use Custom (Supervisor v2) When:

**Learning and education:**
- Understanding how things work
- Building intuition
- Teaching others
- Research projects

**Custom requirements:**
- Need specific coordination logic
- Non-standard information flow
- Unique error handling
- Special logging or monitoring

**Novel patterns:**
- Experimenting with new approaches
- Building custom coordination strategies
- Extending multi-agent patterns

### The Recommendation:

**For most production use: Supervisor v1**
- Faster to build
- Well-tested
- Maintained by experts

**For learning: Supervisor v2**
- Understand mechanics
- Build intuition
- Enable innovation

**For advanced needs: Start with 2, optimize with 1**
- Prototype custom behavior
- Validate approach
- Then use built-in for production if possible

---

## Common Issues

### Issue 1: Tool not being called
**Problem**: Supervisor doesn't consult specialists
**Solution**: Check tool docstrings are clear and relevant

### Issue 2: Infinite loops
**Problem**: Specialist calls supervisor, supervisor calls specialist
**Solution**: Ensure specialists don't have supervisor as a tool

### Issue 3: Context loss between calls
**Problem**: Second specialist doesn't know about first
**Solution**: Supervisor's ReAct loop handles this naturally via message history

### Issue 4: Response format issues
**Problem**: Specialist returns structured data, supervisor expects text
**Solution**: Add formatting in wrapper's return statement

---

## What You've Accomplished

You've built a custom multi-agent supervisor and learned:

✅ How to wrap agents as tools for other agents
✅ Why multi-agent coordination is just tool calling
✅ How to build layered agent architectures
✅ How to customize every aspect of coordination
✅ The mechanics behind built-in supervisor functions
✅ When to use custom vs built-in implementations

## Key Takeaways

**Wrapping agents as tools:**
```python
# Create agent
agent = create_react_agent(model, tools, prompt)

# Wrap as tool
@tool
def specialist_tool(request: str) -> str:
    result = agent.invoke({"messages": [...]})
    return result["messages"][-1].content
```

**Building custom supervisor:**
```python
# Create wrapped tools
tools = [specialist1, specialist2, specialist3]

# Create supervisor (just a ReAct agent!)
supervisor = create_react_agent(
    model=model,
    tools=tools,
    prompt=supervisor_prompt
)
```

**The pattern:**
- Agents at one level become tools at next level
- Each level abstracts complexity
- Coordination is just tool selection and calling

## Next Steps

You've mastered both supervisor implementations. Now explore:

1. **Add a fourth specialist**: Try adding a billing specialist
2. **Customize a wrapper**: Add preprocessing or post-processing
3. **Compare performance**: Time Supervisor v1 vs Supervisor v2
4. **Build hierarchies**: Create a supervisor of supervisors

**Other multi-agent patterns to explore:**
- Pipeline: Sequential specialist chain
- Collaborative: Specialists communicate directly
- Hybrid: Mix coordination patterns

**Production considerations:**
- Evaluation and testing
- Monitoring and logging
- Error handling and recovery
- Scaling and deployment

The lesson: **Understanding implementation enables innovation. Build it yourself to truly master it.**
