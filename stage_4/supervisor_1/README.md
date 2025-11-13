# Stage 4 Supervisor v1: Multi-Agent System with Built-in Coordination

## What We're Building

Stage 4 takes a completely different approach to handling complexity. Instead of one agent with all 7 tools, we create three specialized agents that each focus on a specific area. A supervisor agent coordinates them, deciding which specialists to consult for each customer request.

This is like a customer service team where different people handle orders, products, and accounts - and a team lead coordinates who helps with what.

## What This Stage Achieves

By the end of Stage 4 Supervisor v1, you'll have:
- Three specialist agents, each with their own tools and expertise
- A supervisor that intelligently delegates work to specialists
- Ability to handle complex queries by coordinating multiple specialists
- Parallel execution when specialists can work independently
- A system that scales better than single agents

This stage shows how specialization solves the complexity problems from earlier stages.

## The Problem We're Solving

Stages 1-3 all used a single agent:
- Stage 1: One agent, 2 tools - worked fine
- Stage 2: One agent, 7 tools - struggled with complexity
- Stage 3: One agent, 7 tools with better planning - better but still limited

**The insight:** Instead of making one agent smarter, create a team of specialists.

**Benefits:**
- Each specialist masters a small domain
- Supervisor handles coordination
- Can work in parallel when appropriate
- Natural division of labor

## Folder Structure

```
stage_4/
├── supervisor_1/                    # Built-in supervisor implementation
│   ├── agents/
│   │   └── workflow.py             # Supervisor coordination using create_supervisor()
│   ├── demo.py                      # Run this to see multi-agent in action
│   └── README.md                   # This file
│
├── common/                          # Shared across supervisor patterns
│   ├── specialist_agents.py        # The three specialist agents
│   ├── specialist_prompts.py       # Prompts for each specialist
│   └── supervisor_prompts.py       # Prompt for supervisor coordination
│
└── supervisor_2/                    # Custom supervisor (alternative approach)
```

Why this organization:
- `supervisor_1/` - Uses LangGraph's built-in coordination
- `common/` - Specialist agents shared by both supervisor implementations
- `supervisor_2/` - Custom implementation for learning how it works internally

## Component Breakdown

### 1. Specialist Agents (common/specialist_agents.py)

Instead of one agent with 7 tools, we have three agents with 2-3 tools each.

**Order Operations Agent (3 tools)**
- Focus: Everything about orders
- Tools:
  - `get_order_status` - Check order status
  - `modify_shipping` - Change delivery
  - `process_refund` - Handle refunds
- When used: Customer asks about their order

**Product & Inventory Agent (2 tools)**
- Focus: Products and policies
- Tools:
  - `check_inventory` - Check product availability
  - `search_faq` - Search knowledge base
- When used: Customer asks about products or policies

**Customer Account Agent (2 tools)**
- Focus: Accounts and escalations
- Tools:
  - `get_customer_account` - Get account info
  - `create_ticket` - Escalate to humans
- When used: Customer asks about their account or has complex issues

**How they're created:**
Each specialist is a simple ReAct agent (like Stage 1), created using LangGraph's `create_react_agent()` function. They're just focused on a smaller domain.

### 2. Specialist Prompts (common/specialist_prompts.py)

Each specialist has a custom prompt that defines their role and expertise.

**Order Operations Prompt:**
- "You are an Order Operations Specialist"
- Lists responsibilities (tracking, shipping, refunds)
- Provides guidelines (check status before modifying)
- Sets empathetic tone for delayed orders

**Product & Inventory Prompt:**
- "You are a Product & Inventory Specialist"
- Lists responsibilities (availability, specs, policies)
- Provides guidelines (check stock, suggest alternatives)
- Focuses on helping customers find what they need

**Customer Account Prompt:**
- "You are a Customer Account Specialist"
- Lists responsibilities (account info, escalations)
- Provides guidelines (privacy, comprehensive tickets)
- Focuses on personalized support

**Why separate prompts?**
- Each specialist needs different instructions
- Different tone for different situations
- Clear scope keeps agents focused

### 3. Supervisor Prompt (common/supervisor_prompts.py)

The supervisor is the customer-facing agent. It coordinates everything behind the scenes.

**What it emphasizes:**
- Act like a human customer service rep
- Consult with specialists but present information naturally
- Don't mention "specialists" or "delegation" to customers
- Be warm, empathetic, and conversational
- Handle multiple concerns in one coherent response

**Examples from the prompt:**
- Bad: "I delegated to the order operations specialist"
- Good: "Let me check on that order for you"

**The key:** Customers interact with one helpful person, not a committee.

### 4. Supervisor Workflow (supervisor_1/agents/workflow.py)

This is where the magic happens. The workflow coordinates everything.

**What it does:**
- Creates the three specialist agents
- Uses `create_supervisor()` to build coordination logic
- Sets up parallel execution for independent tasks
- Handles checkpointing for conversation memory

**Key configuration:**
```python
create_supervisor(
    agents=specialist_agents,           # The three specialists
    model=model,                        # Supervisor's model
    prompt=SUPERVISOR_PROMPT,           # How supervisor should act
    parallel_tool_calls=True,           # Enable parallel delegation
    output_mode="last_message",         # Clean output
)
```

**The flow:**
```
Customer query
    ↓
Supervisor analyzes: "What specialists do I need?"
    ↓
Delegates to specialist(s) (can be parallel)
    ↓
Specialists execute their tools
    ↓
Specialists return results
    ↓
Supervisor synthesizes into natural response
    ↓
Customer gets answer
```

### 5. Built-in vs Custom Implementation

**Supervisor v1 (this implementation):**
- Uses LangGraph's `create_supervisor()` function
- Quick to set up
- Production-ready
- Coordination logic is hidden

**Supervisor 2 (alternative):**
- Custom implementation showing how supervisor works
- More code but more educational
- Full control over delegation logic
- Better for learning

**Both use the same specialists and prompts** - only the supervisor coordination differs.

## How the Components Work Together

Let's walk through a complex request: "Check my order #12345, and do you have it in blue?"

### Step 1: Customer Message Received

```
User: "Check my order #12345, and do you have it in blue?"
```

### Step 2: Supervisor Analyzes

The supervisor thinks:
- "Two separate concerns here"
- "Order status → need Order Operations specialist"
- "Product availability → need Product & Inventory specialist"
- "These can run in parallel!"

### Step 3: Parallel Delegation

**Supervisor delegates to both specialists simultaneously:**

**To Order Operations:**
- Task: "Check order #12345"
- Specialist uses: `get_order_status("12345")`
- Returns: "Order delivered Nov 4..."

**To Product & Inventory:**
- Task: "Check if available in blue"
- Specialist uses: `check_inventory(item_from_context, "blue")`
- Returns: "Blue variant available, 5 in stock"

Both specialists work at the same time!

### Step 4: Supervisor Synthesizes

Supervisor receives both results and combines them naturally:

"Your order #12345 was delivered on November 4th! And yes, we do have that same item available in blue with 5 units currently in stock. Would you like to order it?"

### Step 5: Customer Gets Complete Answer

One coherent response addressing both questions. Customer doesn't know multiple specialists were involved.

## Why This Approach Works

### Specialization

**Stage 2 problem:** One agent, 7 tools, confusion about which to use

**Stage 4 solution:** Three agents, 2-3 tools each, no confusion
- Order Operations: Only thinks about orders
- Product & Inventory: Only thinks about products
- Customer Account: Only thinks about accounts

Each specialist is an expert in their domain.

### Intelligent Coordination

The supervisor:
- Understands what each specialist can do
- Decides which specialists are needed
- Can delegate to multiple specialists
- Combines their work into one answer

Like a good team lead.

### Parallel Execution

When tasks are independent:
```
Supervisor → Order Operations
         → Product & Inventory  (at the same time!)
         → Customer Account
```

All three can work simultaneously if needed. Much faster than sequential.

### Natural Scaling

Need to handle new types of requests?
- Add a new specialist
- Give them relevant tools
- Supervisor automatically learns to use them

No need to retrain the whole system.

## Running Stage 4 Supervisor v1

### Quick Start

```bash
# From project root
python stage_4/supervisor_1/demo.py
```

This demonstrates the supervisor coordinating specialists on various scenarios.

### Using the Web Interface

```bash
# Terminal 1: Start backend with Stage 4.1
STAGE=4.1 uvicorn backend.api:app --reload

# Terminal 2: Open frontend/index.html in your browser
```

The interface shows:
- Which specialists were consulted
- What each specialist did
- The final coordinated response

### Configuration

Edit `.env`:
- `STAGE`: Set to 4.1 for Supervisor v1
- `MODEL_TYPE`: openai or anthropic
- `ENABLE_CHECKPOINTING`: Optional conversation memory

## Demo Scenarios

### Simple Single-Specialist Query

**Query:** "What's the status of order #12345?"

**Execution:**
1. Supervisor recognizes: Order question
2. Delegates to: Order Operations only
3. Order Operations: Checks order status
4. Supervisor: Presents result naturally

One specialist, straightforward.

### Complex Multi-Specialist Query

**Query:** "My order #12345 is late, do you have it in blue, and can you check my account history?"

**Execution:**
1. Supervisor recognizes: Three separate concerns
2. Delegates to: All three specialists (parallel)
   - Order Operations: Checks order status
   - Product & Inventory: Checks blue variant
   - Customer Account: Gets account history
3. All specialists work simultaneously
4. Supervisor: Synthesizes all three results into one answer

Three specialists, coordinated response.

### Parallel vs Sequential

**Parallel execution (when possible):**
- Checking order AND checking inventory - independent tasks
- Both can run at the same time
- Faster completion

**Sequential execution (when needed):**
- Need order details before checking refund eligibility
- Must wait for first specialist to finish
- Supervisor handles dependencies automatically

## Comparing Stage 4 to Previous Stages

| Aspect | Stage 2 | Stage 3 | Stage 4 |
|--------|---------|---------|---------|
| Agents | 1 | 1 | 4 (1 supervisor + 3 specialists) |
| Tools per agent | 7 | 7 | 2-3 each |
| Tool selection | Confusing | Better | Clear (domain-focused) |
| Complex queries | Struggles | Better | Handles well |
| Parallel execution | No | No | Yes |
| Scalability | Limited | Better | Excellent |

## What Makes Supervisor v1 Special

### Uses Built-in LangGraph Function

This implementation uses `create_supervisor()` from LangGraph:

**Advantages:**
- Quick to set up (minimal code)
- Production-ready immediately
- Handles edge cases automatically
- Maintained by LangGraph team

**Trade-offs:**
- Coordination logic is hidden
- Harder to customize delegation strategy
- Less transparent for learning

**When to use:**
- Building production systems quickly
- Standard multi-agent patterns work for your use case
- Don't need custom coordination logic

### Comparison with Supervisor v2

**Supervisor v1 (this implementation):**
- Uses `create_supervisor()` built-in
- ~150 lines of code
- Fast to implement
- Less customizable

**Supervisor v2 (alternative):**
- Custom implementation
- ~400+ lines of code
- Fully transparent
- Completely customizable

**Both use the same specialists** - only coordination differs.

## Key Concepts

### Specialization Pattern

Instead of:
```
One agent knows everything → Gets confused with 7 tools
```

We have:
```
Order specialist knows orders → 3 tools, focused
Product specialist knows products → 2 tools, focused
Account specialist knows accounts → 2 tools, focused
Supervisor coordinates → Knows which specialist to call
```

Division of labor creates clarity.

### Delegation

The supervisor doesn't have tools. It has specialists.

**Supervisor's job:**
1. Understand customer request
2. Identify which specialists can help
3. Delegate appropriately
4. Synthesize results

**Specialists' job:**
1. Receive focused task
2. Use their tools to handle it
3. Return results

Clear separation of concerns.

### Parallel Coordination

The supervisor can delegate to multiple specialists at once:

```python
parallel_tool_calls=True
```

This means:
- Independent tasks run simultaneously
- Faster response times
- Better resource utilization

Example: Checking order status and inventory can happen at the same time.

## What Stage 4 Teaches

### Specialization > Generalization

One generalist with 7 tools → confusion
Three specialists with 2-3 tools each → clarity

**Why it works:**
- Smaller problem space per agent
- Domain expertise
- Focused prompts and tools
- Less cognitive load

### Coordination as a Skill

The supervisor doesn't need to know how to do everything. It needs to know:
- Who can do what
- When to delegate
- How to combine results

This is a different type of intelligence.

### The Power of Abstraction

Using `create_supervisor()` abstracts away complexity:
- You don't need to implement coordination logic
- You don't need to handle parallel execution
- You don't need to manage specialist state

Just define specialists and let LangGraph handle the rest.

### When Multi-Agent Makes Sense

**Use multi-agent when:**
- Domain naturally divides into areas
- Different areas need different tools
- Want to scale by adding specialists
- Complex requests span multiple domains

**Stick with single agent when:**
- Simple, focused domain
- Few tools (2-3)
- Don't need parallelism
- Overhead not worth it

## Testing

Try these scenarios:

**Single specialist queries:**
- "What's the status of order #12345?" → Order Operations
- "Do you have red shirts in size M?" → Product & Inventory
- "Show me my account history" → Customer Account

**Multi-specialist queries:**
- "Check order #12345 and find it in blue" → Order + Product
- "My order is late, I want a refund, check my account" → All three
- "What's your return policy for order #12346?" → Order + Product

Watch how the supervisor delegates efficiently!

## What's Next

Stage 4 Supervisor v1 shows the built-in approach. But how does it actually work under the hood?

**Stage 4 Supervisor v2** provides:
- Custom implementation of supervisor logic
- Full transparency into delegation decisions
- Complete control over coordination strategy
- Deep understanding of multi-agent systems

Same specialists, different supervisor implementation.

**Future Patterns:**
- Pipeline: Sequential specialist chain
- Collaborative: Specialists talk directly to each other
- Hierarchical: Supervisors of supervisors
