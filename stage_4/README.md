# Stage 4: Multi-Agent Architecture - Supervisor Pattern

## Overview

Stage 4 demonstrates how **specialization through multi-agent coordination** solves the complexity issues shown in Stage 2. Instead of one overwhelmed agent with 7 tools, we have **3 specialized agents** coordinated by a **Supervisor**, each focused on their domain expertise.

## The Problem Stage 4 Solves

**Question:** *"How can we solve complexity through specialization?"*

**Answer:** Multi-agent systems with specialized roles:
- **Focused Expertise** - Each agent masters a specific domain
- **Parallel Execution** - Independent tasks run simultaneously
- **Better Tool Selection** - Specialists have fewer tools, clearer choices
- **Scalability** - Easy to add new specialists without overwhelming existing agents

## Architecture

### Supervisor Pattern (Tool Calling)

The supervisor treats specialist agents as "tools" to be invoked:

```
┌─────────────────────────────────────────────────────────────┐
│              Stage 4: Supervisor Pattern                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Customer Query                                             │
│       ↓                                                     │
│  🎯 Supervisor Agent                                        │
│       ├─→ Analyzes request                                 │
│       ├─→ Identifies required specialists                  │
│       ├─→ Delegates to specialists (parallel if safe)      │
│       ├─→ Aggregates results                               │
│       └─→ Responds to customer                             │
│                                                             │
│  Specialist Agents (ReAct):                                │
│  ┌────────────────────────────────────────┐               │
│  │ 📦 Order Operations Agent               │               │
│  │    • get_order_status                   │               │
│  │    • modify_shipping                    │               │
│  │    • process_refund                     │               │
│  └────────────────────────────────────────┘               │
│                                                             │
│  ┌────────────────────────────────────────┐               │
│  │ 🛍️ Product & Inventory Agent           │               │
│  │    • check_inventory                    │               │
│  │    • search_faq                         │               │
│  └────────────────────────────────────────┘               │
│                                                             │
│  ┌────────────────────────────────────────┐               │
│  │ 👤 Customer Account Agent               │               │
│  │    • get_customer_account               │               │
│  │    • create_ticket                      │               │
│  └────────────────────────────────────────┘               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Two Implementations

### Supervisor 1: Built-in `create_supervisor()`
- Uses LangGraph's `create_supervisor()` function
- Quick setup, production-ready
- Located in `supervisor_1/`

### Supervisor 2: Custom Educational Implementation
- Fully transparent supervisor logic
- Educational: see how delegation works
- Located in `supervisor_2/`

## Specialist Agent Design

### 📦 Order Operations Agent
**Domain**: Complete order lifecycle management  
**Tools**:
- `get_order_status` - Track orders
- `modify_shipping` - Change delivery
- `process_refund` - Handle returns

**Why Together?** Natural workflow - checking orders often leads to shipping changes or refunds.

### 🛍️ Product & Inventory Agent
**Domain**: Pre-purchase decisions and product information  
**Tools**:
- `check_inventory` - Product availability
- `search_faq` - Knowledge base (specs, policies)

**Why Together?** Customers researching products need both availability and information.

### 👤 Customer Account Agent
**Domain**: Account management and escalations  
**Tools**:
- `get_customer_account` - Account details
- `create_ticket` - Escalate complex issues

**Why Together?** Account problems requiring escalation often need account context.

## Parallel Execution Rules

The supervisor intelligently parallelizes work:

### ✅ Safe to Run in Parallel
- **Read-only operations**: `get_order_status`, `check_inventory`, `search_faq`, `get_customer_account`
- **Independent domains**: Order + Product queries, Product + Account queries

### 🚫 Must Be Sequential
- **Write operations**: `modify_shipping`, `process_refund`, `create_ticket`
- **Dependent operations**: Must complete refund before checking updated order status

**Implementation**: Only pure read operations are parallelized automatically.

## Setup & Usage

### Quick Start

```bash
# Install dependencies (if not already done)
cd evolution-of-ai-agents-arch
pip install -r requirements.txt

# Run Supervisor 1 demo
python stage_4/supervisor_1/demo.py

# Run Supervisor 2 demo (after implementation)
python stage_4/supervisor_2/demo.py
```

### Configuration

```bash
MODEL_TYPE=openai              # Recommended: openai
STAGE=4.1                      # Supervisor 1 (4.2 for Supervisor 2)
ENABLE_CHECKPOINTING=true      # Optional conversation memory

OPENAI_API_KEY=your_key_here
```

## Demo Scenarios

### The Complex Birthday Gift Scenario (from Stage 2)

**Input:**
*"My order #12345 hasn't arrived, it was supposed to be a birthday gift for tomorrow. Can you check where it is, and if it won't arrive on time, I want to either expedite shipping or get a refund and buy locally. Also, do you have the same item in blue instead of red for future reference?"*

**Stage 2 Behavior (Single Agent):**
- High iterations (4-6 loops)
- Tool selection confusion
- Sequential processing (slow)
- Context loss

**Stage 4 Behavior (Supervisor):**
- Supervisor immediately identifies 3 sub-tasks
- Delegates to specialists:
  1. **Order Operations**: Check order #12345 status and shipping options
  2. **Product & Inventory**: Find blue variant
  3. **Resolution consideration**: Prepared by Order Operations based on delay
- Parallel execution where safe
- Clean aggregated response

### Expected Output Flow

```
🎯 Supervisor: Analyzing request...
   └─ Identified needs: Order tracking, inventory check, refund options

📦 Order Operations Agent: Checking order #12345...
   └─ Tool: get_order_status(12345)
   └─ Status: Delayed, arriving in 3 days

🛍️ Product & Inventory Agent: Searching for blue variant...
   └─ Tool: check_inventory(item_from_order, color=blue)
   └─ Result: In stock

📦 Order Operations Agent: Evaluating options...
   └─ Tool: modify_shipping(12345, expedite=overnight)
   └─ Alternative: process_refund(12345)

🎯 Supervisor: Aggregating results...
   └─ Final Response: Comprehensive solution with options
```

## Performance Comparison

| Metric | Stage 2 (Single) | Stage 4 (Supervisor) |
|--------|------------------|----------------------|
| **Tool Selection** | Confused (7 tools) | Clear (2-3 tools/agent) |
| **Execution** | Sequential | Parallel where safe |
| **Context** | Loss issues | Maintained per domain |
| **Iterations** | 4-6 typical | 1-2 typical |
| **Scalability** | Poor | Excellent |

## What Stage 4 Teaches

### 🎯 **Specialization Benefits**
- Focused expertise beats generalization
- Each agent masters its domain
- Clearer decision-making with fewer options

### 🔄 **Coordination Patterns**
- Supervisor delegates intelligently
- Parallel execution when possible
- Aggregation produces coherent responses

### 📊 **Scalability**
- Adding specialists doesn't overwhelm existing agents
- Independent development and testing
- Clear boundaries and responsibilities

### 🛠️ **Design Trade-offs**
- More complexity in coordination
- Latency from coordination overhead
- But: better quality and maintainability

## Key Differences from Earlier Stages

| Aspect | Stage 2 | Stage 3 (ReWOO) | Stage 4 (Supervisor) |
|--------|---------|-----------------|----------------------|
| **Agents** | 1 | 1 | 4 (1 supervisor + 3 specialists) |
| **Planning** | Per-step | Upfront | Supervisor decides |
| **Execution** | Sequential | Sequential | Parallel-capable |
| **Tool Access** | All 7 | All 7 | Partitioned (2-3 each) |
| **Specialization** | None | None | Domain-focused |

## Learning Exercises

1. **Run the Complex Scenario** - Compare with Stage 2's struggle
2. **Add a New Specialist** - Try adding a "Promotion Agent"
3. **Modify Parallel Rules** - Experiment with delegation patterns
4. **Custom Supervisor** - Compare supervisor_1 vs supervisor_2 implementations
5. **Trace Delegation Flow** - Use logging to see supervisor decisions

## Implementation Details

### Files Structure (Supervisor 1)
```
stage_4/supervisor_1/
├── demo.py                        # Interactive demonstration
├── agents/
│   ├── specialist_agents.py       # 3 specialist ReAct agents
│   ├── supervisor.py              # Supervisor using create_supervisor()
│   ├── state.py                   # State schema
│   └── workflow.py                # Complete workflow
└── prompts/
    └── specialist_prompts.py      # Domain-specific prompts
```

### Specialist Agents
Each specialist is created using LangGraph's `create_react_agent`:
```python
order_agent = create_react_agent(
    model="openai:gpt-4o",
    tools=[get_order_status, modify_shipping, process_refund],
    name="order_operations"
)
```

### Supervisor Creation
Using LangGraph's built-in supervisor:
```python
supervisor = create_supervisor(
    agents=[order_agent, product_agent, account_agent],
    model=ChatOpenAI(model="gpt-4o"),
    parallel_tool_calls=True  # Enable parallel delegation
)
```

## What's Next?

**Tutorial 2** will cover:
- Production deployment of multi-agent systems
- Evaluation and monitoring
- Performance optimization
- Cost management for multiple agents

## Resources

- [Stage 2 Documentation](../stage_2/README.md) - Problems this solves
- [Stage 3 Documentation](../stage_3/README.md) - Comparison with ReWOO
- [LangGraph Multi-Agent Guide](https://python.langchain.com/docs/langgraph/how-tos/multi-agent)
- [Supervisor Pattern Tutorial](https://docs.langchain.com/oss/python/langchain/supervisor)

Ready to see how to customize supervisor behavior? → **Supervisor 2 (Custom Implementation)**
