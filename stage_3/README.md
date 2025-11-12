# Stage 3: ReWOO Pattern - Reasoning Without Observation

## Overview

Stage 3 demonstrates how the ReWOO (Reasoning Without Observation) pattern solves the complexity issues shown in Stage 2. Using the **same 7 tools** and **same complex scenarios**, ReWOO handles multi-step requests efficiently by planning all tool calls upfront.

## The Problem Stage 3 Solves

**Question:** *"How can we make single agents handle complex scenarios without the struggles seen in Stage 2?"*

**Answer:** ReWOO separates planning from execution:
- **Plans** all tool calls upfront with placeholders (#E1, #E2, etc.)
- **Executes** tools sequentially with variable substitution
- **Integrates** all evidence into a final answer
- **Reduces** LLM calls from N+1 (ReAct) to just 2

## ReWOO Pattern Deep Dive

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    ReWOO Pattern Architecture                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  User Query → 🧠 Planner (LLM call 1)                        │
│                    ↓                                         │
│         Complete Plan with Placeholders                      │
│         (#E1, #E2, #E3, ...)                                │
│                    ↓                                         │
│  🔧 Worker → Execute Tool 1 → Store #E1                      │
│         ↓                                                    │
│  🔧 Worker → Execute Tool 2 (uses #E1) → Store #E2           │
│         ↓                                                    │
│  🔧 Worker → Execute Tool 3 (uses #E1, #E2) → Store #E3      │
│         ↓                                                    │
│  🧠 Solver (LLM call 2)                                      │
│         ↓                                                    │
│  Final Answer                                                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Three Core Components

1. **🧠 Planner (LLM Call 1)**
   - Receives the full user query
   - Plans ALL required tool calls upfront
   - Uses placeholders for tool results (#E1, #E2, etc.)
   - Example output:
     ```
     Plan: Check order status. #E1 = OrderStatus[12345]
     Plan: Determine if delayed. #E2 = LLM[Will #E1 arrive on time?]
     Plan: Check expedite options. #E3 = ModifyShipping[12345, expedite]
     ```

2. **🔧 Worker (No LLM Calls)**
   - Executes each tool in sequence
   - Substitutes placeholder variables with actual results
   - Stores each result for use in subsequent steps
   - No reasoning between steps (just execution)

3. **🧠 Solver (LLM Call 2)**
   - Receives complete plan + all evidence
   - Integrates information into coherent answer
   - Final synthesis of all tool results

### Key Advantages

**Efficiency:**
- Only 2 LLM calls regardless of tool count
- ReAct uses N+1 LLM calls (reason → act → observe loop)
- Significant token savings on complex queries

**Planning:**
- All tool calls determined upfront
- No tool selection confusion between steps
- Clear execution flow

**Context:**
- All evidence available at final synthesis
- No information loss between steps
- Better final answer quality

## Setup & Usage

### Quick Start

```bash
# Same setup as previous stages
cd evolution-of-ai-agents-arch
pip install -r requirements.txt

# Run ReWOO demo (standalone)
python stage_3/demo.py

# Run with web interface
STAGE=3.1 python -m common.backend.api
open frontend/index.html
```

### Configuration

```bash
MODEL_TYPE=openai              # Recommended: openai (best tool calling)
STAGE=3.1                      # ReWOO pattern (3.2, 3.3 coming soon)
ENABLE_CHECKPOINTING=false     # Optional (for fault-tolerance, not conversation memory)

OPENAI_API_KEY=your_key_here
```

### 💾 Checkpointing (Fault-Tolerance & Debugging)

Stage 3.1 supports **optional checkpointing** for fault-tolerance and debugging:

**ReWOO is Single-Turn by Design:**
- Each query is processed independently
- No conversation memory needed
- Checkpointing saves state at each step: plan → tool → tool → ... → solve

**When to Enable:**
```bash
ENABLE_CHECKPOINTING=true STAGE=3.1 python -m common.backend.api
```

**Fault-Tolerance Example:**
```python
workflow = ReWOOWorkflow(enable_checkpointing=True)

try:
    # Execute query
    result = workflow.invoke("Complex query...", thread_id="task-123")
except Exception as e:
    # If tool fails, inspect where it failed
    state = workflow.get_state("task-123")
    print(f"Failed at step: {len(state.values.get('results', {}))}")
    print(f"Completed evidence: {state.values.get('results', {})}")
    print(f"Remaining steps: {len(state.values.get('steps', []))}")
    
    # Resume from checkpoint after fixing issue
    # (Current implementation creates fresh state, but checkpoints are saved)
```

**Debugging Example:**
```python
workflow = ReWOOWorkflow(enable_checkpointing=True)
result = workflow.invoke("Multi-step query...", thread_id="debug-456")

# Inspect execution history
history = workflow.get_state_history("debug-456", limit=10)

print(f"Total checkpoints: {len(history)}")
for i, checkpoint in enumerate(history):
    step = checkpoint.metadata.get('step', 'unknown')
    next_nodes = checkpoint.next
    print(f"[{i}] Step {step}: Next={next_nodes}")
    
    # Inspect plan generation
    if 'plan_string' in checkpoint.values:
        print(f"    Plan: {checkpoint.values['plan_string'][:100]}...")
    
    # Inspect evidence gathered
    if 'results' in checkpoint.values:
        evidence_count = len(checkpoint.values['results'])
        print(f"    Evidence collected: {evidence_count} items")
```

**Use Cases:**
- **Production Monitoring**: Track which steps fail most often
- **Performance Analysis**: Identify slow tool executions
- **Debugging**: Inspect intermediate state when output is wrong
- **Testing**: Verify plan generation and tool execution separately

**Note**: For multi-turn conversations with memory, use Stage 2 (ReAct pattern) instead.

### Code Usage

```python
from stage_3.agents.workflow import ReWOOWorkflow

# Initialize ReWOO workflow
workflow = ReWOOWorkflow(model_type="openai")

# Run a query
result = workflow.invoke("My order #12345 hasn't arrived...")

# Access the results
print(f"Plan: {result['plan_string']}")
print(f"Evidence: {result['results']}")
print(f"Final Answer: {result['result']}")

# With checkpointing (optional)
workflow_with_cp = ReWOOWorkflow(
    model_type="openai",
    enable_checkpointing=True
)
result = workflow_with_cp.invoke("Query...", thread_id="my-thread")

# Access checkpoints (for debugging)
state = workflow_with_cp.get_state("my-thread")
history = workflow_with_cp.get_state_history("my-thread", limit=5)
```

## Demo Scenarios

### Scenario 1: Simple Order Status
**Query:** "What's the status of my order #12345?"

**Expected ReWOO Execution:**
1. Planner creates simple plan
2. Worker executes OrderStatus tool
3. Solver provides concise answer

**Efficiency:** 2 LLM calls total

### Scenario 2: Complex Birthday Gift (from Stage 2)
**Query:** "My order #12345 hasn't arrived, it was supposed to be a birthday gift for tomorrow. Can you check where it is, and if it won't arrive on time, I want to either expedite shipping or get a refund and buy locally. Also, do you have the same item in blue instead of red for future reference?"

**Expected ReWOO Execution:**
1. **Planner** creates complete plan:
   - Check order status
   - Determine if will arrive on time  
   - Check expedite options
   - Check refund eligibility
   - Search for blue variant

2. **Worker** executes all 5 steps sequentially with variable substitution

3. **Solver** integrates all evidence into comprehensive answer

**Efficiency:** 2 LLM calls (vs 6+ in Stage 2's ReAct)

## Performance Comparison

| Metric | Stage 2 (ReAct) | Stage 3 (ReWOO) | Improvement |
|--------|------------------|-----------------|-------------|
| **LLM Calls** | N+1 per query | Always 2 | ~70% reduction |
| **Iterations** | 4-6 typical | 1 pass | ~80% reduction |
| **Tool Confusion** | Common | Rare | Significant |
| **Context Loss** | Frequent | None | Complete |
| **Token Usage** | High | Low | ~60% savings |

## What Stage 3 (ReWOO) Teaches

### 🧠 **Efficient Planning**
- Planning upfront eliminates redundant reasoning
- Variable substitution allows dependencies without re-planning
- Single synthesis step produces better final answers

### 🔧 **Batch Execution**
- All tool calls determined before any execution
- Sequential execution with full context available
- No wasted iterations from poor tool selection

### 📊 **Token Efficiency**
- Constant 2 LLM calls regardless of complexity
- Dramatic savings on multi-step queries
- More cost-effective at scale

### 🎯 **Predictable Behavior**
- Clear execution flow: Plan → Execute → Solve
- No confusion from interleaved reasoning/action
- Easier to debug and optimize

## Limitations (from ReWOO Paper)

1. **Static Planning**: If little context available, planner may be ineffective
   - *Mitigation*: Few-shot prompting with examples in our implementation

2. **Sequential Execution**: Tasks run in order, not in parallel
   - *Note*: True parallel execution would require more complex orchestration
   - Our implementation prioritizes clarity over parallelism

3. **No Mid-Course Correction**: Can't adapt plan based on tool results
   - *Note*: Plan-and-Execute pattern (Stage 3, Part 3) addresses this

## Web UI Features

### Thought Process Display

The frontend displays ReWOO's complete thought process:

**📋 REWOO PLAN Card:**
- Shows all planned steps with numbered badges
- Evidence variables (#E1, #E2) highlighted in blue
- Formatted for readability with step descriptions and tool calls on separate lines
- Example:
  ```
  [Step 1] Check the current status of order #12345
           #E1 = OrderStatus[12345]
  
  [Step 2] Analyze if order will arrive on time
           #E2 = LLM[Will #E1 arrive by tomorrow?]
  ```

**🔍 EVIDENCE GATHERED Cards:**
- One card per tool execution
- Shows evidence variable and tool result
- Color-coded green for observations
- Updates tool call counter in real-time

**💬 Final Response:**
- Short, conversational chat format (2-4 sentences)
- Streams word-by-word with typing effect
- Natural customer service tone

### Stage Selection

The UI automatically displays stage information:
- **Stage 3.1**: "ReWOO: Plan → Execute → Solve"
- **Stage 3.2**: "Reflection: Generate → Critique → Refine" (coming soon)
- **Stage 3.3**: "Plan-Execute: Plan → Execute → Replan" (coming soon)

## Implementation Details

### Files Structure
```
stage_3/
├── demo.py                    # Interactive ReWOO demonstration
├── README.md                  # This file
├── agents/
│   ├── __init__.py
│   ├── state.py              # BaseAgentState + ReWOOState with checkpointing support
│   ├── rewoo_agent.py        # Core ReWOO: Planner, Worker, Solver
│   └── workflow.py           # LangGraph workflow with optional checkpointing
├── prompts/
│   ├── __init__.py
│   └── rewoo_prompts.py      # Planner and Solver prompts
└── utils/
    ├── __init__.py
    └── fallbacks.py          # Shared fallback utilities

common/
├── base_workflow.py           # Abstract base class with checkpointing support
├── tool_invocation.py         # Reusable tool parameter mapping utility
├── checkpointing.py           # LangGraph persistence utilities
└── backend/
    ├── api.py                 # FastAPI with stage routing (1, 2, 3.1, 3.2, 3.3)
    ├── models.py              # Request/response schemas
    ├── workflow_loader.py     # Dynamic stage loading
    ├── streaming.py           # Stage-specific event handlers
    ├── session_manager.py     # Session → thread_id tracking
    └── response_handler.py    # Response extraction
```

### Key Implementations

**Reusable Tool Invocation** (`common/tool_invocation.py`):
- Uses Python introspection to map parameters automatically
- Handles single and multi-parameter tools
- Type conversion (int, float, bool)
- Works across all stages

**Backend Architecture** (Refactored):
- Modular design: 6 separate backend files
- Clean separation of concerns
- Stage routing via combined notation (3.1, 3.2, 3.3)
- Session management for checkpointing

### Tools Available (same as Stage 2)
1. `OrderStatus` - Check order status by ID
2. `SearchFAQ` - Search knowledge base
3. `CustomerAccount` - Get customer history
4. `ProcessRefund` - Initiate refunds
5. `ModifyShipping` - Expedite or change address
6. `CheckInventory` - Check product availability
7. `CreateTicket` - Escalate to human support

## Example Execution

**Input:** "My order #12345 hasn't arrived, supposed to be a birthday gift for tomorrow. Check status, if delayed expedite or refund, and do you have it in blue?"

**Planner Output:**
```
Plan: Check order status and delivery date
#E1 = OrderStatus[12345]

Plan: Determine if delayed
#E2 = LLM[Will order from #E1 arrive by tomorrow?]

Plan: Check expedite options if delayed
#E3 = ModifyShipping[12345, expedite]

Plan: Check refund eligibility
#E4 = ProcessRefund[12345]

Plan: Find blue variant
#E5 = CheckInventory[item from #E1 in blue color]
```

**Worker:** Executes E1 → E2 → E3 → E4 → E5 sequentially

**Solver:** Integrates all evidence into comprehensive customer response

## Learning Exercises

1. **Compare with Stage 2** - Run same query in both stages, compare:
   - Number of LLM calls
   - Execution time
   - Context preservation
   - Answer quality

2. **Plan Analysis** - Examine generated plans for:
   - Tool selection accuracy
   - Dependency ordering
   - Information flow

3. **Edge Cases** - Test scenarios where ReWOO struggles:
   - Insufficient initial context
   - Mid-execution plan changes needed
   - Dynamic environment requiring adaptation

## What's Next?

**Reflection Pattern (Stage 3, Part 2):**
- Self-evaluation loops
- Answer quality improvement
- Error detection and correction

**Plan-and-Execute (Stage 3, Part 3):**
- Dynamic replanning based on results
- Adaptive execution strategies
- Handling unknown dependencies

**Stage 4: Multi-Agent Systems:**
- Specialized agents for different domains
- Agent coordination patterns
- Supervisor and collaborative architectures

## Resources

- [Stage 2 Documentation](../stage_2/README.md) - Problems ReWOO solves
- [LangGraph ReWOO Tutorial](https://langchain-ai.github.io/langgraph/tutorials/rewoo/rewoo/)
- [ReWOO Paper](https://arxiv.org/abs/2305.18323) - Original research
- [Pattern Comparison Tool](tools/pattern_comparison.py) - Coming soon

Ready for self-improving agents? → **Reflection Pattern (Coming Soon)**
