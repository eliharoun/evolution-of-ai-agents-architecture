# Stage 4 Supervisor 1: Usage Examples

## Quick Start

```python
from stage_4.supervisor_1.agents.workflow import SupervisorWorkflow

# Initialize workflow
workflow = SupervisorWorkflow(
    model_type="openai",
    enable_checkpointing=False
)

# Run a query
result = workflow.invoke("What's the status of my order #12345?")
print(result['messages'][-1].content)
```

## Example 1: Simple Order Status

**Query:**
```
"What's the status of my order #12345?"
```

**Expected Flow:**
1. Supervisor analyzes → identifies order query
2. Delegates to Order Operations agent
3. Order Operations uses `get_order_status` tool
4. Supervisor aggregates and responds

**Response:**
Order details with status, tracking, and delivery information.

---

## Example 2: Complex Multi-Domain Query

**Query:**
```
"My order #12345 hasn't arrived, it was supposed to be a birthday gift for tomorrow. 
Can you check where it is, and if it won't arrive on time, I want to either expedite 
shipping or get a refund and buy locally. Also, do you have the same item in blue 
instead of red for future reference?"
```

**Expected Flow:**
1. Supervisor analyzes → identifies 3 sub-tasks:
   - Order tracking and shipping options
   - Product availability in blue
   - Refund options if needed

2. Delegates to specialists:
   - **Order Operations**: Check status, evaluate expedite/refund
   - **Product & Inventory**: Find blue variant
   
3. Specialists work (can be parallel for reads)

4. Supervisor synthesizes comprehensive response

**Response:**
Complete solution addressing all concerns with specific options.

---

## Example 3: Multi-Specialist Parallel Query

**Query:**
```
"I want to check my order #12345 status, also what's your return policy, 
and can you look up my account history?"
```

**Expected Flow:**
1. Supervisor identifies 3 independent queries
2. Delegates to all 3 specialists (parallel-safe reads):
   - **Order Operations**: Order status
   - **Product & Inventory**: Return policy from FAQ
   - **Customer Account**: Account history
   
3. All specialists execute in parallel
4. Supervisor aggregates results

**Response:**
Comprehensive answer covering all three domains.

---

## Example 4: Sequential Write Operations

**Query:**
```
"Please process a refund for order #12345 and then check the updated status"
```

**Expected Flow:**
1. Supervisor identifies dependent operations
2. Sequential delegation (NOT parallel):
   - First: Order Operations processes refund
   - Then: Order Operations checks updated status
   
3. Ensures correct ordering for write operations

**Response:**
Refund confirmation with updated order status.

---

## Testing Specialist Isolation

```python
# Test each specialist independently
from stage_4.supervisor_1.agents.specialist_agents import (
    create_order_operations_agent,
    create_product_inventory_agent,
    create_customer_account_agent,
)
from common.model_factory import ModelFactory

model = ModelFactory.create_model("openai", "gpt-4o-mini")

# Test Order Operations
order_agent = create_order_operations_agent(model)
result = order_agent.invoke({"messages": [{"role": "user", "content": "Check order #12345"}]})

# Test Product & Inventory  
product_agent = create_product_inventory_agent(model)
result = product_agent.invoke({"messages": [{"role": "user", "content": "Do you have blue t-shirts?"}]})

# Test Customer Account
account_agent = create_customer_account_agent(model)
result = account_agent.invoke({"messages": [{"role": "user", "content": "Show my account info for order #12345"}]})
```

---

## With Checkpointing (Conversation Memory)

```python
workflow = SupervisorWorkflow(
    model_type="openai",
    enable_checkpointing=True
)

# First query
result1 = workflow.invoke("What's the status of order #12345?", thread_id="user-123")

# Follow-up query (remembers context)
result2 = workflow.invoke("Can you expedite it?", thread_id="user-123")
# Supervisor remembers order #12345 from previous query

# Another follow-up
result3 = workflow.invoke("Do you have it in blue?", thread_id="user-123")
# Supervisor remembers the item from order #12345
```

---

## Debugging Delegation

```python
workflow = SupervisorWorkflow(enable_checkpointing=False)

result = workflow.invoke("Complex query here...")

# Examine delegation flow
for msg in result['messages']:
    if hasattr(msg, 'tool_calls') and msg.tool_calls:
        for tc in msg.tool_calls:
            if 'transfer_to' in tc['name']:
                print(f"Delegated to: {tc['name']}")
    
    if hasattr(msg, 'name'):
        print(f"Response from: {msg.name}")
```

---

## Performance Monitoring

```python
import time

workflow = SupervisorWorkflow(enable_checkpointing=False)

# Time execution
start = time.time()
result = workflow.invoke("Your query here")
elapsed = time.time() - start

print(f"Execution time: {elapsed:.2f}s")
print(f"Total messages: {len(result['messages'])}")
print(f"Specialist calls: {sum(1 for m in result['messages'] if hasattr(m, 'name'))}")
```

---

## Common Patterns

### Pattern 1: Order + Product Query
```python
query = "Check order #12345 and see if you have more in stock"
# Delegates to: Order Operations + Product & Inventory (parallel)
```

### Pattern 2: Account + Order Query
```python
query = "Show my account history and current order status"
# Delegates to: Customer Account + Order Operations (parallel)
```

### Pattern 3: Complex Resolution
```python
query = "Order delayed, need expedite or refund, and create ticket if issues"
# Delegates to: Order Operations (sequential) + Customer Account
```

### Pattern 4: Information Gathering
```python
query = "What's your return policy and do you have [item] in blue?"
# Delegates to: Product & Inventory (parallel for FAQ + inventory)
```

---

## Error Handling

The supervisor gracefully handles:
- **Missing information**: Asks specialists to gather what's needed
- **Tool failures**: Specialists retry or escalate
- **Ambiguous queries**: Supervisor clarifies before delegating
- **No applicable specialist**: Supervisor attempts direct response or escalates

---

## Tips for Best Results

1. **Clear Queries**: More specific queries → better delegation
2. **Order IDs**: Include order IDs when asking about orders
3. **Multiple Questions**: Separate concerns are handled efficiently
4. **Follow-ups**: Use checkpointing for multi-turn conversations

---

## Comparing with Stage 2

**Same Query in Stage 2 vs Stage 4:**

| Aspect | Stage 2 (Single Agent) | Stage 4 (Supervisor) |
|--------|------------------------|----------------------|
| **Delegation** | N/A (single agent) | Intelligent routing |
| **Tool Selection** | Confused (7 choices) | Clear (2-3 per specialist) |
| **Parallel Execution** | No | Yes (for reads) |
| **Iterations** | 4-6 typical | 1-2 typical |
| **Context Management** | Struggles | Maintained |

**Run both to compare:**
```bash
# Stage 2
STAGE=2 python stage_2/demo.py

# Stage 4
python stage_4/supervisor_1/demo.py
