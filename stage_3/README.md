# Stage 3: ReWOO (Reasoning without Observation) - Planning Before Acting

## What We're Building

Stage 3 introduces a smarter approach to handling complex requests. Instead of thinking and acting one step at a time like in Stages 1 and 2, the ReWOO pattern (Reasoning Without Observation) plans all the steps upfront, then executes them efficiently.

We use the same 7 tools from Stage 2, but with a completely different workflow that eliminates the struggles we saw earlier.

## What This Stage Achieves

By the end of Stage 3, you'll have an agent that:
- Plans all tool calls before executing any of them
- Executes tools in the right order with dependencies handled automatically
- Uses only 2 LLM calls regardless of complexity (vs many in Stage 2)
- Handles complex multi-step requests without confusion
- Never loses context or repeats tools unnecessarily

This stage shows how better planning solves the problems from Stage 2.

## The Problem We're Solving

In Stage 2, the agent struggled with complex requests because it:
- Decided which tool to use after each step
- Had no overall plan
- Could get confused choosing from 7 tools
- Sometimes forgot what it already learned

**ReWOO solves this by planning everything upfront.**

## How ReWOO is Different

### Stage 2 (ReAct Pattern)
```
User asks question
  → Agent thinks: "What should I do?"
  → Agent acts: Uses tool
  → Agent observes: Sees result
  → Agent thinks: "What should I do next?"
  → Agent acts: Uses another tool
  → Agent observes: Sees result
  → ... (repeats until done)
```

Many back-and-forth cycles. Each "think" step uses the LLM.

### Stage 3 (ReWOO Pattern)
```
User asks question
  → Planner thinks: "What's my complete plan?"
  → Worker: Executes all tools in order
  → Solver: Combines everything into answer
```

Just two LLM calls - one to plan, one to answer.

## Folder Structure

```
stage_3/
├── agents/
│   └── rewoo/                      # ReWOO-specific implementation
│       ├── state.py               # ReWOO state (different from Stage 1/2)
│       ├── rewoo_agent.py         # Planner, Worker, Solver
│       ├── workflow.py            # ReWOO orchestration
│       └── utils/
│           ├── rewoo_prompts.py   # Planner and Solver prompts
│           └── tool_invocation.py # Tool execution helper
├── rewoo_demo.py                   # Run this to see ReWOO in action
└── README.md                       # This file
```

Shared components:
- `common/tools/` - Same 7 tools as Stage 2
- `common/base_workflow.py` - Base workflow class
- `common/model_factory.py` - Model initialization

## Component Breakdown

### 1. State (state.py)

The ReWOO state is more complex than Stages 1 and 2 because it needs to track the plan and execution.

**What it contains:**
- `task`: The original user question
- `plan_string`: The complete plan as readable text
- `steps`: List of (description, variable, tool, parameters) tuples
- `results`: Dictionary mapping variables to results (like #E1 → result)
- `result`: The final answer

**Why different from Stage 2?**
- Stage 2 just tracks messages and iterations
- ReWOO tracks an entire execution plan
- Needs to store intermediate results for variable substitution

### 2. ReWOO Agent (rewoo_agent.py)

The agent has three distinct parts instead of one unified "call_model" method.

**Part 1: Planner**
- Method: `get_plan(state)`
- What it does: Creates complete plan with placeholders
- Example output:
  ```
  Plan: Check order status #E1 = OrderStatus[12345]
  Plan: Determine if delayed #E2 = LLM[Will #E1 arrive on time?]
  Plan: Check inventory #E3 = CheckInventory[item from #E1, blue]
  ```
- This is the first LLM call

**Part 2: Worker**
- Method: `tool_execution(state)`
- What it does: Executes one tool at a time
- Special feature: Variable substitution
  - Replaces #E1 with actual result from step 1
  - Replaces #E2 with actual result from step 2
  - And so on...
- No LLM calls - just execution

**Part 3: Solver**
- Method: `solve(state)`
- What it does: Takes all the evidence and creates final answer
- Sees: The complete plan + all tool results
- Returns: Natural language response to the user
- This is the second (and final) LLM call

**The key innovation:**
The Worker executes tools without calling the LLM. It just follows the plan that was already created.

### 3. Workflow (workflow.py)

The workflow structure is different from Stages 1 and 2.

**The flow:**
```
START → Planner → Worker → Worker → Worker → ... → Solver → END
```

More specifically:
```
START
  ↓
plan (creates full plan)
  ↓
tool (executes one tool)
  ↓
[Decision: More tools?]
  ↓ Yes         ↓ No
tool (loops)    solve (final answer)
  ↓
END
```

**What makes it work:**
- The `_route` method decides: "Are there more tools to execute?"
- If yes: Loop back to tool node
- If no: Go to solver
- Solver combines everything and ends

**Compared to Stage 2:**
- Stage 2: Agent → Tools → Agent → Tools → ... (many cycles)
- Stage 3: Planner → Tool → Tool → Tool → Solver (one pass)

### 4. Prompts (rewoo_prompts.py)

Two specialized prompts for the two LLM calls.

**Planner Prompt:**
- Lists all 7 available tools
- Shows example of how to format plans
- Teaches the model to use #E1, #E2, #E3 placeholders
- Emphasizes following the exact format

**Format example:**
```
Plan: <description> #E1 = ToolName[parameters]
Plan: <description> #E2 = ToolName[parameters using #E1]
```

**Solver Prompt:**
- Receives the plan + all evidence
- Asks for short, conversational response (2-4 sentences)
- No email formatting or bullet points
- Chat-style answer

**Why two prompts?**
- Planner needs to think strategically
- Solver needs to communicate naturally
- Different modes require different instructions

### 5. Tool Invocation (utils/tool_invocation.py)

Helper function that automatically calls tools with the right parameters.

**What it does:**
- Takes a tool and a string of parameters
- Figures out which parameters the tool needs
- Parses the input string
- Calls the tool correctly

**Example:**
```python
# Input: "12345, expedite"
# Tool: modify_shipping (needs order_id, modification_type, details)
# Output: Correctly calls modify_shipping("12345", "expedite", "")
```

**Why this is needed:**
- The planner outputs parameters as strings
- Tools expect proper typed parameters
- This bridges the gap automatically

## How the Components Work Together

Let's walk through a complex request: "My order #12345 hasn't arrived, I want expedited shipping or a refund, and do you have it in blue?"

### Step 1: Planner (First LLM Call)

**Input:** User's complex question

**Planner thinks:**
"This needs multiple pieces of information. Let me plan all the steps:"

**Output:**
```
Plan: Check order status #E1 = OrderStatus[12345]
Plan: Check if delayed #E2 = LLM[Is #E1 delayed?]
Plan: Check expedite options #E3 = ModifyShipping[12345, expedite]
Plan: Check refund eligibility #E4 = ProcessRefund[12345, Customer request]
Plan: Find blue variant #E5 = CheckInventory[item from #E1, blue]
```

**What happened:** Complete plan created with 5 steps. No tools executed yet.

### Step 2: Worker (No LLM Calls)

The worker executes each step in order:

**Iteration 1:**
- Execute: `OrderStatus["12345"]`
- Store: `#E1 = "Order delivered Nov 4..."`

**Iteration 2:**
- Input: "Is #E1 delayed?"
- Replace #E1: "Is Order delivered Nov 4... delayed?"
- Execute: LLM call to analyze
- Store: `#E2 = "No, delivered on time"`

**Iteration 3:**
- Execute: `ModifyShipping["12345", "expedite"]`
- Store: `#E3 = "Cannot expedite - already delivered"`

**Iteration 4:**
- Execute: `ProcessRefund["12345", "Customer request"]`
- Store: `#E4 = "Cannot refund - delivered over 30 days ago"`

**Iteration 5:**
- Input: "item from #E1, blue"
- Replace #E1: "item from Order delivered Nov 4... blue"
- Execute: `CheckInventory` with parsed item and color
- Store: `#E5 = "Blue variant available, 3 in stock"`

**What happened:** All 5 steps executed sequentially. Each step can use results from previous steps.

### Step 3: Solver (Second LLM Call)

**Input:** The complete plan + all evidence

**Solver sees:**
```
Plan with all #E variables
Evidence:
  #E1 = Order details (delivered Nov 4)
  #E2 = No, delivered on time
  #E3 = Cannot expedite
  #E4 = Cannot refund
  #E5 = Blue variant available
```

**Solver thinks:** "I need to explain this naturally to the customer"

**Output:** "Your order #12345 was delivered on November 4th, so it's no longer eligible for expedited shipping or refunds. However, we do have the same item available in blue with 3 units in stock!"

**What happened:** All evidence combined into one coherent, helpful answer.

## Why ReWOO is Better

### Fewer LLM Calls

**Stage 2 (ReAct):**
- Call 1: Think about what to do
- Call 2: Check order (observation)
- Call 3: Think about next step
- Call 4: Check inventory (observation)
- Call 5: Think about final answer
- Total: 5+ LLM calls

**Stage 3 (ReWOO):**
- Call 1: Create complete plan
- Call 2: Generate final answer
- Total: 2 LLM calls

**Savings:** Reduction in LLM calls

### No Tool Confusion

**Stage 2:** Agent might call both refund AND shipping tools simultaneously

**Stage 3:** Planner decides upfront: "First check order, then try expedite, then try refund"

Clear sequence, no confusion.

### No Context Loss

**Stage 2:** Agent might forget earlier tool results in later iterations

**Stage 3:** All results stored in `results` dictionary, available throughout

Nothing gets forgotten.

### Better Planning

**Stage 2:** Reactive - decides each step based only on immediate context

**Stage 3:** Proactive - sees the full picture and creates optimal plan

More strategic approach.

## Running Stage 3

### Quick Start

```bash
# From project root
python stage_3/rewoo_demo.py
```

This demonstrates ReWOO with the same complex scenarios that broke Stage 2.

### Using the Web Interface

```bash
# Terminal 1: Start backend with Stage 3
STAGE=3.1 uvicorn backend.api:app --reload

# Terminal 2: Open frontend/index.html in your browser
```

The interface shows:
- The complete plan (before execution)
- Each tool execution with its result
- The final synthesized answer

### Configuration

Edit `.env`:
- `STAGE`: Set to 3.1 for ReWOO pattern
- `MODEL_TYPE`: openai or anthropic (recommended for planning)
- `ENABLE_CHECKPOINTING`: Optional fault tolerance

## Demo Scenarios

### Simple Scenario

**Query:** "What's the status of order #12345?"

**ReWOO execution:**
1. Planner: "Plan: Check order #E1 = OrderStatus[12345]"
2. Worker: Executes OrderStatus
3. Solver: "Your order was delivered on November 4th!"

Even simple queries benefit from the structured approach.

### Complex Scenario (The Birthday Gift)

**Query:** "My order #12345 hasn't arrived, supposed to be a birthday gift for tomorrow. Check status, if delayed expedite or refund, and do you have it in blue?"

**ReWOO execution:**
1. **Planner:** Creates 5-step plan covering all parts
2. **Worker:** Executes all 5 steps with variable substitution
3. **Solver:** Provides comprehensive answer addressing everything

**Stage 2 comparison:**
- Stage 2: 6+ iterations, tool confusion, struggles detected
- Stage 3: 1 pass through workflow, no struggles, complete answer

## Comparing the Stages

| Aspect | Stage 1 | Stage 2 | Stage 3 (ReWOO) |
|--------|---------|---------|-----------------|
| Tools | 2 | 7 | 7 |
| Pattern | ReAct | ReAct | ReWOO |
| LLM Calls | 2-3 | 4-8 | Always 2 |
| Planning | None | None | Complete upfront |
| Tool Order | Reactive | Reactive | Planned |
| Struggles | Rare | Common | None |
| Complex Queries | Limited | Struggles | Handles well |

## Key Concepts

### Planning vs Reacting

**Reactive (Stage 2):**
- See situation
- Take action
- See new situation
- Take another action
- Repeat...

**Planned (Stage 3):**
- See full situation
- Plan all actions
- Execute plan
- Done

Planning is more efficient for complex tasks.

### Variable Substitution

The magic of ReWOO is in the placeholders:

```
Plan: Get order info #E1 = OrderStatus[12345]
Plan: Check if item exists #E2 = CheckInventory[item from #E1]
```

When executing step 2:
- Worker sees "item from #E1"
- Looks up #E1: "Blue jeans, size 32"
- Replaces: "item from Blue jeans, size 32"
- Calls: CheckInventory["Blue jeans, size 32"]

This allows dependencies without replanning.

### Two LLM Calls

**Call 1 - Planner:**
- Input: User question
- Output: Complete plan
- Purpose: Strategic thinking

**Call 2 - Solver:**
- Input: Plan + all evidence
- Output: Natural language answer
- Purpose: Synthesis and communication

Worker executions in between use no LLM calls.

### Single-Turn Design

ReWOO is designed for complete, single-turn responses:
- Plan everything at once
- Execute everything at once
- Answer everything at once

Not designed for ongoing conversations with memory. For that, use Stage 2 with checkpointing.

## Limitations of ReWOO

### Can't Adapt Mid-Execution

**Problem:** If a tool returns unexpected results, plan can't change

**Example:**
- Plan assumes order is in "Shipped" status
- Tool returns "Delivered" status
- Plan continues with original assumptions
- May execute unnecessary steps

**Solution:** Plan-and-Execute pattern (future stage) adds replanning

### Assumes Complete Information

**Problem:** Works best when all information is in the initial query

**Example:**
- Query: "I want to return something"
- Planner: "What order? Can't plan without it"
- Gets stuck

**Solution:** Better prompt engineering or hybrid patterns

### Sequential Execution

**Problem:** Executes tools one at a time, even if they could run in parallel

**Example:**
- Could check inventory and order status simultaneously
- ReWOO does them sequentially

**Trade-off:** Simplicity vs maximum speed

## What Stage 3 Teaches

### Planning Eliminates Struggles

The same complex queries that cause 4+ iterations in Stage 2 complete in one pass with ReWOO.

**Why?**
- All decisions made upfront
- No tool selection confusion
- Clear execution path

### Efficiency Through Structure

**2 LLM calls regardless of complexity:**
- Simple query: 2 calls
- Complex query: Still 2 calls

**Stage 2 comparison:**
- Simple query: 2-3 calls
- Complex query: 6-8 calls

The structure creates efficiency.

### The Power of Placeholders

Variable substitution (#E1, #E2, etc.) allows:
- Dependencies between tools
- Information flow through steps
- No need to replan after each tool

Simple but powerful mechanism.

### When to Use Each Pattern

**Use Stage 2 (ReAct) when:**
- Simple, straightforward queries
- Need conversation memory
- Uncertain about required steps
- Interactive back-and-forth needed

**Use Stage 3 (ReWOO) when:**
- Complex, multi-step requests
- All information available upfront
- Efficiency is important
- Single-turn complete responses

Different patterns for different situations.

## Testing

Try the same queries from Stage 2 and compare:

**Simple query (both work well):**
- "What's the status of order #12345?"

**Complex query (Stage 2 struggles, Stage 3 handles smoothly):**
- "Order #12345 is late, I want refund or expedite, and do you have it in blue?"

Watch how Stage 3:
- Plans all 5 steps immediately
- Executes them in order
- Provides complete answer
- No struggles detected

## What's Next

Stage 3 shows one advanced pattern. But there are more:

**Coming Soon:**
- **Reflection**: Agent evaluates its own answers and improves them
- **Plan-and-Execute**: Creates plans that adapt based on tool results

Each pattern solves different types of complexity.

**Stage 4: Multi-Agent Systems**
- Multiple specialized agents
- Coordination between agents
- Supervisor patterns
- Even more powerful than single-agent patterns


## Resources
1. [Stage 2 Documentation](../stage_2/README.md) - Compare the differences
2. **LangGraph ReWOO tutorial:** https://langchain-ai.github.io/langgraph/tutorials/rewoo/rewoo/
3. **REWOO Agent Pattern:** https://agent-patterns.readthedocs.io/en/stable/patterns/rewoo.html