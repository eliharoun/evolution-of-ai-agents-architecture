# Stage 4 Supervisor v2: Understanding How Coordination Really Works

## What We're Building

Supervisor v2 builds the exact same multi-agent system as Supervisor v1, but this time we implement the coordination logic ourselves instead of using LangGraph's built-in function. This lets you see exactly how the supervisor pattern works under the hood.

Think of Supervisor v1 as using a pre-built team management system, while Supervisor v2 is building that system from scratch to understand how it works.

## What This Stage Achieves

By the end of Stage 4 Supervisor v2, you'll understand:
- How specialists are wrapped as tools the supervisor can call
- Why the supervisor is just a ReAct agent with high-level tools
- How information flows between supervisor and specialists
- How to customize every aspect of coordination
- The mechanics behind multi-agent systems

This stage is about education - learning how the magic actually works.

## The Key Difference from Supervisor v1

Both implementations create the same system (1 supervisor + 3 specialists), but:

**Supervisor v1 (Built-in):**
```python
supervisor = create_supervisor(
    agents=specialists,  # LangGraph handles everything
    model=model,
    prompt=prompt
)
```
- Quick setup
- Coordination logic hidden
- Black box

**Supervisor v2 (Custom):**
```python
# Wrap each specialist as a tool
@tool
def specialist_order_operations(request: str) -> str:
    return order_agent.invoke(request)

# Create supervisor as regular ReAct agent
supervisor = create_react_agent(
    model=model,
    tools=[specialist_order_operations, ...],  # Wrapped specialists
    prompt=prompt
)
```
- More code
- Coordination logic visible
- Fully transparent

**Same result, different path.** Supervisor v2 shows you what Supervisor v1 hides.

## Folder Structure

```
stage_4/
├── supervisor_2/                    # Custom supervisor implementation
│   ├── agents/
│   │   ├── workflow.py             # Supervisor using create_react_agent()
│   │   └── specialist_wrappers.py  # KEY: Wraps specialists as tools
│   ├── demo.py                      # Run this to see custom implementation
│   └── README.md                   # This file
│
├── common/                          # Shared with Supervisor v1
│   ├── specialist_agents.py        # Same three specialists
│   ├── specialist_prompts.py       # Same prompts
│   └── supervisor_prompts.py       # Same supervisor prompt
```

Both Supervisor v1 and v2 use:
- Same specialist agents (Order, Product, Account)
- Same prompts
- Same tools (7 total)

Only the supervisor coordination differs.

## Component Breakdown

### 1. Specialist Agents (common/specialist_agents.py)

Same three specialists as Supervisor v1:
- Order Operations (3 tools)
- Product & Inventory (2 tools)
- Customer Account (2 tools)

**No changes here** - specialists are identical between both implementations.

### 2. Specialist Wrappers (agents/specialist_wrappers.py)

This is the new component that makes Supervisor v2 educational.

**What it does:**
Converts specialist agents into tools the supervisor can call.

**How it works:**
```python
# Create the specialist agent
order_agent = create_order_operations_agent(model)

# Wrap it as a tool
@tool
def specialist_order_operations(request: str) -> str:
    """
    Consult the Order Operations specialist.
    
    The supervisor reads this description to know when to use it.
    """
    # Invoke the specialist agent
    result = order_agent.invoke({
        "messages": [{"role": "user", "content": request}]
    })
    
    # Extract and return the specialist's answer
    return result["messages"][-1].content
```

**Breaking it down:**

1. **`@tool` decorator**: Makes the function a LangChain tool
2. **Docstring**: The supervisor reads this to understand what the specialist does
3. **`invoke()` call**: Runs the complete specialist ReAct workflow
4. **Extract response**: Gets the specialist's final answer
5. **Return**: Sends answer back to supervisor

**The insight:** A specialist tool is just a function that runs an entire agent workflow!

**All three specialists are wrapped this way:**
- `specialist_order_operations`
- `specialist_product_inventory`
- `specialist_customer_account`

### 3. Custom Supervisor (agents/workflow.py)

The supervisor is built as a standard ReAct agent.

**The key code:**
```python
supervisor = create_react_agent(
    model=self.model,
    tools=self.specialist_tools,  # These are wrapped specialists!
    prompt=SUPERVISOR_PROMPT,
    checkpointer=self.checkpointer,
    name="custom_supervisor"
)
```

**What this means:**
- The supervisor is just a ReAct agent (like Stage 1)
- Its "tools" are actually full specialist agents
- When supervisor calls a tool, it triggers a complete agent workflow
- The supervisor doesn't know specialists are agents - they look like tools!

**The flow:**
```
Supervisor's perspective:
"I have three tools: specialist_order_operations, specialist_product_inventory, specialist_customer_account"
"Customer wants order info, I'll call specialist_order_operations tool"

What actually happens:
1. Supervisor calls specialist_order_operations("Check order #12345")
2. Tool wrapper invokes Order Operations agent
3. Order Operations agent runs its ReAct loop with its tools
4. Order Operations agent returns final answer
5. Tool wrapper passes answer back to supervisor
6. Supervisor sees: "Tool returned: Order details..."
```

**The genius:** Multi-agent coordination is just tool calling with wrapped agents!

### 4. Supervisor Prompt (common/supervisor_prompts.py)

Same prompt as Supervisor v1 - no changes needed.

**Why?**
- The supervisor's job is the same
- Coordinate specialists naturally
- Present information to customers
- The implementation doesn't change the role

## How the Components Work Together

Let's trace through a query: "Check order #12345 and do you have it in blue?"

### Step 1: Supervisor Receives Query

```
Customer: "Check order #12345 and do you have it in blue?"

Supervisor (ReAct agent):
- Sees message
- Reads system prompt
- Sees available tools:
  * specialist_order_operations
  * specialist_product_inventory
  * specialist_customer_account
- Thinks: "Need order info and product info"
```

### Step 2: Supervisor Calls First Tool

```
Supervisor decides:
"I'll call specialist_order_operations tool with request"

Tool call:
{
  "name": "specialist_order_operations",
  "args": {"request": "Check order #12345"}
}
```

### Step 3: Specialist Wrapper Invokes Agent

```
specialist_order_operations tool wrapper:
1. Receives request from supervisor
2. Creates message for Order Operations agent
3. Invokes: order_agent.invoke({"messages": [...]})
4. Order Operations agent runs its ReAct loop:
   - Thinks: "Need get_order_status"
   - Calls: get_order_status("12345")
   - Observes: Order details
   - Responds: Formatted answer
5. Wrapper extracts final message
6. Returns to supervisor
```

### Step 4: Supervisor Receives First Result

```
Supervisor sees:
Tool result: "Order #12345 delivered Nov 4..."

Supervisor thinks:
"Got order info. Still need product info."
```

### Step 5: Supervisor Calls Second Tool

```
Supervisor decides:
"I'll call specialist_product_inventory tool"

Tool call:
{
  "name": "specialist_product_inventory",
  "args": {"request": "Do you have it in blue?"}
}
```

### Step 6: Second Specialist Works

```
specialist_product_inventory tool wrapper:
1. Receives request
2. Invokes Product & Inventory agent
3. Agent runs ReAct loop with check_inventory
4. Returns availability info
5. Wrapper passes to supervisor
```

### Step 7: Supervisor Synthesizes

```
Supervisor has:
- Order info from first specialist
- Product info from second specialist

Supervisor formulates:
"Your order #12345 was delivered on November 4th! 
And yes, we have it in blue with 5 units in stock."
```

### Step 8: Customer Gets Answer

Natural, complete response. No mention of specialists or tools.

## Why This Implementation is Educational

### Shows the Pattern Clearly

**The pattern:** Agents can be tools for other agents

```
Layer 1: Basic tools (get_order_status, check_inventory, etc.)
    ↓ used by
Layer 2: Specialist agents (order_operations, product_inventory, etc.)
    ↓ wrapped as tools
Layer 3: Supervisor agent (coordinates specialists)
```

Each layer builds on the previous one.

### Demystifies "Magic"

**What seems magical:**
- Supervisor coordinates multiple agents
- Specialists work in parallel
- Results are synthesized automatically

**What's actually happening:**
- Supervisor calls tools (which happen to be agents)
- Each tool call runs a complete agent workflow
- Tool results are combined using standard ReAct logic

No magic - just layered tool calling!

### Enables Customization

Because you control the wrappers, you can:

**Modify information flow:**
```python
@tool
def specialist_order_operations(request: str) -> str:
    # Add context from supervisor
    full_request = f"Context: {supervisor_context}\n{request}"
    result = order_agent.invoke(...)
    return result
```

**Add preprocessing:**
```python
@tool
def specialist_order_operations(request: str) -> str:
    # Extract order ID first
    order_id = extract_order_id(request)
    # Validate before calling specialist
    if not validate_order_id(order_id):
        return "Invalid order ID"
    result = order_agent.invoke(...)
    return result
```

**Add post-processing:**
```python
@tool
def specialist_order_operations(request: str) -> str:
    result = order_agent.invoke(...)
    response = result["messages"][-1].content
    # Format or filter response
    return format_for_supervisor(response)
```

**Add error handling:**
```python
@tool
def specialist_order_operations(request: str) -> str:
    try:
        result = order_agent.invoke(...)
        return result["messages"][-1].content
    except SpecificError as e:
        # Custom error handling per specialist
        return handle_order_error(e)
```

Full control over every interaction!

## Comparing Supervisor v1 and Supervisor v2

### Code Comparison

**Supervisor v1:**
```python
# Just one function call
supervisor = create_supervisor(
    agents=specialists,
    model=model,
    prompt=prompt,
    parallel_tool_calls=True
)
```

**Supervisor v2:**
```python
# Multiple steps visible
# 1. Wrap specialists as tools
wrapped_tools = create_specialist_tool_wrappers(model)

# 2. Create supervisor as ReAct agent
supervisor = create_react_agent(
    model=model,
    tools=wrapped_tools,
    prompt=prompt
)
```

**More code, but you see every step.**

### Feature Comparison

| Feature | Supervisor v1 | Supervisor v2 |
|---------|--------------|--------------|
| Lines of code | ~150 | ~200 |
| Setup time | 5 minutes | 15 minutes |
| Transparency | Hidden | Full |
| Customization | Limited | Complete |
| Debugging | Harder | Easier |
| Learning value | Lower | Higher |
| Production ready | Immediate | Needs testing |

### When to Use Each

**Use Supervisor v1 when:**
- Building production systems
- Speed is important
- Standard patterns suffice
- Don't need customization

**Use Supervisor v2 when:**
- Learning how things work
- Need custom coordination
- Building novel patterns
- Research or experimentation

## Running Stage 4 Supervisor v2

### Quick Start

```bash
# From project root
python stage_4/supervisor_2/demo.py
```

This runs the same scenarios as Supervisor v1 but with custom implementation.

### Using the Web Interface

```bash
# Terminal 1: Start backend with Stage 4.2
STAGE=4.2 uvicorn backend.api:app --reload

# Terminal 2: Open frontend/index.html in your browser
```

The behavior looks identical to Supervisor v1 - that's the point! Same results, different implementation.

### Configuration

Edit `.env`:
- `STAGE`: Set to 4.2 for Supervisor v2
- `MODEL_TYPE`: openai or anthropic
- `ENABLE_CHECKPOINTING`: Optional conversation memory

## What Stage 4 Supervisor v2 Teaches

### Agents as Tools

The key insight: **Agents can be tools for other agents.**

**Standard tool:**
```python
@tool
def get_order_status(order_id: str) -> str:
    return query_database(order_id)
```

**Agent as tool:**
```python
@tool
def specialist_order_operations(request: str) -> str:
    return order_agent.invoke(request)
```

Both are tools from the supervisor's perspective!

### Layered Architecture

Multi-agent systems are just layers:

**Layer 1: Basic tools**
- `get_order_status`, `check_inventory`, etc.
- Direct operations

**Layer 2: Specialist agents**
- Use basic tools
- Domain-focused
- ReAct pattern

**Layer 3: Supervisor agent**
- Uses specialist tools (which are agents)
- Coordination focused
- ReAct pattern

Each layer abstracts complexity from the one above.

### No Special Magic

The supervisor pattern isn't a special multi-agent framework. It's:
- A ReAct agent
- With tools that happen to be agents
- Using standard tool calling

The "coordination" is just the supervisor deciding which tools to call - no different than any agent deciding which tools to use!

### Customization Opportunities

Because you control the wrappers, you can:
- Modify what information specialists receive
- Filter or format specialist responses
- Add error handling per specialist
- Inject context or history
- Log detailed interactions
- Implement custom retry logic

Full control means full flexibility.

## Testing

Try the same scenarios as Supervisor v1:

**Single specialist:**
- "What's the status of order #12345?"
- Supervisor → Order Operations only

**Multiple specialists:**
- "Check order #12345, do you have it in blue, show my account"
- Supervisor → All three specialists (parallel)

**Complex coordination:**
- "Order #12345 is late, want refund or expedite, have it in blue?"
- Supervisor → Order + Product specialists

The results should be identical to Supervisor v1!

## Advantages of Custom Implementation

### Full Transparency

**You can see:**
- Exactly when specialists are called
- What requests they receive
- What responses they return
- How supervisor processes results

**In Supervisor v1:**
- Most of this is hidden
- Harder to debug
- Can't easily trace flow

### Complete Customization

**You can modify:**
- How requests are formatted for specialists
- How responses are processed
- Error handling per specialist
- Information flow patterns
- Logging and monitoring

**In Supervisor v1:**
- Limited to configuration options
- Can't change core behavior
- Must accept standard patterns

### Better for Learning

**You learn:**
- How multi-agent coordination actually works
- Why specialists are just wrapped tools
- How to build custom coordination patterns
- The mechanics behind the abstraction

**In Supervisor v1:**
- Learn how to use the pattern
- Don't see how it's implemented
- Understanding is surface-level

## Limitations of Custom Implementation

### More Code to Maintain

**Supervisor v2:**
- More lines of code
- More potential for bugs
- Need to test thoroughly

**Supervisor v1:**
- Minimal code
- LangGraph team maintains it
- Already tested

### Reinventing the Wheel

**The trade-off:**
- Understanding comes from building it yourself
- But the built-in version already works well
- Custom implementation needs validation

**When it's worth it:**
- Learning and education
- Need specific customizations
- Building novel patterns

**When it's not:**
- Standard use cases
- Production systems
- Time constraints

## Comparing All Stages

| Aspect | Stage 2 | Stage 3 | Stage 4 Supervisor v1 | Stage 4 Supervisor v2 |
|--------|---------|---------|---------------------|---------------------|
| Agents | 1 | 1 | 4 (1+3) | 4 (1+3) |
| Pattern | ReAct | ReWOO | Built-in Supervisor | Custom Supervisor |
| Transparency | Full | Full | Limited | Full |
| Customization | Full | Full | Limited | Full |
| Complexity | Low | Medium | Low | Medium |
| Learning | Basic | Advanced | Quick start | Deep understanding |

## What This Implementation Teaches

### The Abstraction Principle

**Bottom layer:** Basic tools (database queries, API calls)
**Middle layer:** Specialist agents (use basic tools)
**Top layer:** Supervisor (uses specialist agents as tools)

Each layer abstracts the complexity below it. The supervisor doesn't need to know about database queries - it just asks specialists.

### Coordination is Tool Calling

The supervisor doesn't have special coordination logic. It just:
1. Decides which specialists to consult (tool selection)
2. Calls them (tool execution)
3. Processes responses (observation)
4. Synthesizes (response)

Same ReAct pattern as Stage 1!

### Agents All the Way Down

**Stage 1:** Agent uses tools
**Stage 4:** Supervisor (agent) uses specialists (agents) which use tools

It's agents calling agents calling tools. Clean and consistent.

### Power of Simplicity

You don't need complex frameworks to build multi-agent systems. You just need:
- Tool wrapping pattern
- Standard ReAct agents
- Clear prompts

The complexity is conceptual (coordination), not technical (code).

## Running and Comparing

### Side-by-Side Test

```bash
# Run Supervisor v1
python stage_4/supervisor_1/demo.py

# Run Supervisor v2
python stage_4/supervisor_2/demo.py
```

**Same inputs, same outputs.** Different implementations showing the same pattern.

### Adding Logging

To see the difference in action:

```python
# In specialist_wrappers.py, add logging
@tool
def specialist_order_operations(request: str) -> str:
    print(f"\n→ Supervisor calling Order Operations")
    print(f"  Request: {request}")
    
    result = order_agent.invoke(...)
    response = result["messages"][-1].content
    
    print(f"← Order Operations responding")
    print(f"  Response: {response[:100]}...")
    
    return response
```

Now you can see every interaction!

## What's Next

You've now seen both approaches to the supervisor pattern:
- Supervisor v1: Fast implementation with built-in function
- Supervisor v2: Educational implementation showing mechanics

**Choose based on your goal:**
- Production? Use Supervisor v1
- Learning? Use Supervisor v2
- Both? Study Supervisor v2, deploy Supervisor v1

**Future exploration:**
- Other multi-agent patterns (pipeline, collaborative)
- Hierarchical supervisors (supervisors of supervisors)
- Custom coordination strategies
- Production deployment and monitoring

The lesson: **Understanding the implementation gives you power to customize and innovate.**
