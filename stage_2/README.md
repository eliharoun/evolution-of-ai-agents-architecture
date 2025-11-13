# Stage 2: When One Agent Has Too Many Choices

## What We're Building

Stage 2 takes the same agent from Stage 1 and gives it five more tools to work with - going from 2 tools to 7 tools. The architecture stays exactly the same, but now we can see what happens when a single agent has too many options to choose from.

This stage demonstrates the limitations of the simple ReAct pattern when dealing with complexity.

## What This Stage Achieves

By the end of Stage 2, you'll see:
- The same ReAct agent struggling with more tools
- Automatic detection of when the agent is confused
- Why more tools doesn't mean better performance
- The limitations that will motivate more sophisticated patterns in later stages

This stage shows us where simple agents break down, setting up the need for better solutions.

## The Problem We're Exploring

**Question:** What happens when we give a single agent more tools to choose from?

**Answer:** The agent starts having problems:
- **Tool Selection Confusion**: With 7 tools available, which one should I use?
- **Sequential Bottlenecks**: Processing one thing at a time when parallel would be better
- **Context Loss**: Forgetting what was done earlier in complex requests
- **Planning Difficulties**: No strategy for handling multi-step problems

## Folder Structure

```
stage_2/
├── agents/                  # Core agent logic
│   ├── state.py            # Same simple state as Stage 1
│   ├── react_agent.py      # Same ReAct agent, but with 7 tools
│   └── workflow.py         # Same workflow + struggle monitoring
├── prompts/                 # Instructions for the agent
│   └── prompts.py          # Enhanced prompt for 7 tools
├── demo.py                  # Run this to see the agent struggle
└── README.md               # This file
```

The agent uses shared components:
- `common/tools/` - Now has 7 tools instead of 2
- `common/monitoring/struggle_analyzer.py` - Detects when agent struggles
- `common/data/` - Sample data for all tools

## What Changed from Stage 1

### Same Architecture
- State structure: Identical
- ReAct pattern: Identical  
- Workflow graph: Identical
- Everything else: Identical

### What's Different
- **Number of tools**: 2 → 7
- **Struggle monitoring**: Added
- **Checkpointing**: Optional conversation memory

That's it. The only real change is more tools, but that's enough to cause problems.

## The Seven Tools

### From Stage 1 (2 tools)
1. **get_order_status** - Look up order information
2. **search_faq** - Search FAQ knowledge base

### New in Stage 2 (5 tools)
3. **get_customer_account** - Look up customer history and preferences
4. **process_refund** - Initiate refunds for orders
5. **modify_shipping** - Change delivery address or expedite shipping
6. **check_inventory** - Check product availability and variants
7. **create_ticket** - Escalate complex issues to human support

More tools means more choices, which means more opportunities for confusion.

## Component Breakdown

### 1. State (state.py)

Exactly the same as Stage 1. No changes needed.

**Why?**
- The state structure isn't the problem
- The complexity comes from tools, not state management
- This proves the architecture can handle more - the agent just struggles with choices

### 2. ReAct Agent (react_agent.py)

Same ReAct pattern as Stage 1, but now with 7 tools bound to the model.

**What's new:**
- Imports all 7 tools from `STAGE_2_TOOLS`
- Logs warnings when it detects potential struggles
- Same `call_model` method - no architectural changes

**The problem:**
When the model has to choose from 7 tools instead of 2, it:
- Takes longer to decide
- Sometimes picks the wrong tool
- Gets confused about which tools to use together
- May call tools in inefficient orders

### 3. Workflow (workflow.py)

Same graph structure as Stage 1, plus struggle monitoring.

**The flow is identical:**
```
START → Agent (thinks) → Tools (acts) → Agent (observes) → END
```

**What's new:**
- Wraps the agent node with `_agent_with_monitoring`
- Uses `StruggleAnalyzer` to detect problems
- Optional checkpointing for conversation memory
- Includes struggle stats in results

**The monitoring catches:**
- When iterations get too high (≥4)
- When agent uses multiple tools at once (confusion)
- When agent repeats the same tool (context loss)

### 4. System Prompt (prompts.py)

Enhanced version of Stage 1's prompt with guidance for 7 tools.

**What's different:**
- Lists all 7 tools with descriptions
- Adds "Tool Selection Tips" section
- Warns about conflicting tools (refund AND shipping modification)
- Encourages careful thinking before choosing tools

**The challenge:**
Even with detailed instructions, the agent struggles because choosing between 7 options is harder than choosing between 2.

### 5. Struggle Analyzer (common/monitoring/struggle_analyzer.py)

New component that watches for signs the agent is struggling.

**What it detects:**

**High Iterations:**
- Trigger: Agent takes 4 or more iterations
- Means: Can't decide what to do, keeps going back and forth
- Example: User asks about order, agent calls 4 different tools trying to figure it out

**Tool Confusion:**
- Trigger: Agent uses 2+ tools simultaneously
- Means: Unsure about dependencies, trying multiple approaches
- Example: Calls both `process_refund` AND `modify_shipping` at once

**Context Loss:**
- Trigger: Repeats same tool more than 2 times
- Means: Forgetting what it already learned
- Example: Calls `check_inventory` three times in one conversation

**How it works:**
1. Watches each iteration as agent works
2. Tracks which tools are called
3. Detects patterns that indicate confusion
4. Logs warnings when struggles detected
5. Returns statistics for the frontend to display

## How the Components Work Together

Here's what happens with a complex request like: "My order #12345 hasn't arrived, I want a refund or expedited shipping, and do you have it in blue?"

### Without Struggles (Ideal - Rarely Happens)
1. **Agent thinks**: "Three sub-tasks: check order, handle refund/shipping, check inventory"
2. **Iteration 1**: Calls `get_order_status` for order #12345
3. **Iteration 2**: Based on status, calls `modify_shipping` to expedite
4. **Iteration 3**: Calls `check_inventory` for blue variant
5. **End**: Provides complete answer

### With Struggles (What Actually Happens)
1. **Agent thinks**: "Order issue... but which tool first?"
2. **Iteration 1**: Calls `get_order_status`
3. **Iteration 2**: Confused - calls both `process_refund` AND `modify_shipping` (tool confusion detected)
4. **Iteration 3**: Realizes it forgot the blue variant question, calls `check_inventory`
5. **Iteration 4**: Still unsure if refund or shipping, calls `get_customer_account` (high iterations detected)
6. **End**: Finally responds, but struggle analyzer has flagged multiple issues

The struggle analyzer catches these patterns and reports them.

## Running Stage 2

### Quick Start

```bash
# From project root
python stage_2/demo.py
```

This runs several scenarios, including complex ones that trigger struggles.

### Using the Web Interface

```bash
# Terminal 1: Start backend
uvicorn backend.api:app --reload

# Terminal 2: Open frontend/index.html in your browser
```

The web interface shows:
- The agent's thought process
- Which tools it uses
- Struggle indicators when detected (red badges and summary)

### Configuration

Edit `.env`:
- `MODEL_TYPE`: openai, anthropic, or ollama (openai recommended for tool calling)
- `STAGE`: Set to 2 for this stage
- `ENABLE_CHECKPOINTING`: true to enable conversation memory

## Conversation Memory (Checkpointing)

Stage 2 can optionally remember previous messages in a conversation.

**Without checkpointing:**
- Each request starts fresh
- Agent has no memory of previous questions

**With checkpointing:**
- Agent remembers earlier messages
- Follow-up questions work naturally
- Example: "What order did I just ask about?" works

**To enable:**
```bash
ENABLE_CHECKPOINTING=true
```

**How it works:**
- Uses session IDs to track conversations
- Sessions timeout after 60 minutes of inactivity
- Memory stored in RAM (cleared when server restarts)

## Demo Scenarios

### Simple Scenarios (Work Fine)
These work well even with 7 tools:

1. **Order Status**: "What's the status of order #12345?"
   - Uses: `get_order_status`
   - No struggles

2. **FAQ Question**: "How do I return an item?"
   - Uses: `search_faq`
   - No struggles

3. **Account Info**: "Tell me about my account history"
   - Uses: `get_customer_account`
   - No struggles

### Complex Scenarios (Trigger Struggles)
These reveal the agent's limitations:

4. **Multi-Step Request**: "My order #12345 hasn't arrived, I want a refund or expedited shipping, and do you have the same item in blue?"
   - Multiple sub-questions
   - Requires planning
   - Often triggers high iterations and tool confusion

5. **Missing Information**: "I'm frustrated! I ordered something weeks ago and it's not here! I want a refund!"
   - No order ID provided
   - Agent struggles to figure out what to do
   - May call wrong tools trying to help

6. **Conditional Logic**: "Check if order #12346 has shipped. If not, cancel and refund. If yes, expedite to overnight. Also check if you have it in a different color."
   - Multiple conditions
   - Complex decision tree
   - Agent has trouble planning the sequence

## When the Agent Struggles

### Signs of Struggle

**High Iterations (4+)**
- Agent keeps going in circles
- Can't decide which tool to use
- Takes multiple attempts to get it right

**Tool Confusion**
- Uses multiple tools at once when it should use one
- Uses conflicting tools (refund AND shipping modification)
- Unclear about dependencies between tools

**Context Loss**
- Repeats the same tool multiple times
- Forgets what it learned from previous tool calls
- Has to re-fetch information it already has

### Why This Happens

**Too Many Choices**
- 7 tools is a lot for the agent to consider
- Each tool has its own use cases and parameters
- Agent has to reason about which combination to use

**No Planning Capability**
- Agent thinks one step at a time
- Can't create an efficient multi-step plan
- Processes requests sequentially, not in parallel

**Context Window Limitations**
- Long conversations with many tool calls
- Earlier context gets pushed out
- Agent forgets what it already did

## Comparing Stage 1 and Stage 2

| Aspect | Stage 1 | Stage 2 |
|--------|---------|---------|
| Tools | 2 | 7 |
| Architecture | Simple ReAct | Same ReAct |
| State | Simple | Same |
| Scenarios | Basic queries | Complex requests |
| Performance | Smooth | Shows struggles |
| Monitoring | Basic logs | Struggle detection |
| Purpose | Learn pattern | See limitations |

The key lesson: **Same architecture + more complexity = struggles**

## What Stage 2 Teaches

### More Tools ≠ Better Performance

You might think giving the agent more tools would make it better. Actually, it makes things harder:
- More choices to evaluate
- More potential for wrong choices
- More opportunities for confusion

### Single Agents Have Limits

The ReAct pattern works great for simple tasks, but struggles with:
- Complex multi-step requests
- Parallel information gathering
- Conditional logic (if this, then that)
- Coordinating multiple tools

### The Need for Better Patterns

Stage 2 proves we need something more sophisticated than just giving an agent more tools. We need:
- Better planning capabilities
- Ability to work in parallel
- Coordination strategies
- Specialized expertise

This motivates the advanced patterns in Stage 3 and the multi-agent architectures in Stage 4.

## Testing

Try these yourself to see the struggles:

**Simple (should work fine):**
- "What's the status of order #12345?"
- "How do I return an item?"
- "Show me my account history"

**Complex (will trigger struggles):**
- "My order #12345 is late, I want a refund or expedited shipping, and check if you have it in blue"
- "I ordered something weeks ago and it's not here! Refund me now!" (no order ID)
- "If order #12346 shipped, expedite it. If not, refund it. Also check blue variants"

Watch the struggle indicators appear!

## What's Next

Stage 2 shows the problems. Stage 3 shows the solutions.

**Stage 3 introduces advanced single-agent patterns:**
- **ReWOO**: Plan all tool calls upfront, then execute efficiently
- **Reflection**: Self-evaluate and improve responses
- **Plan-and-Execute**: Create and adapt plans dynamically

These patterns handle the same complex scenarios that break Stage 2, but do so smoothly without struggles.

The architectural shift isn't about changing the ReAct pattern - it's about adding planning and reflection capabilities on top of it.

## Resources

1. [Stage 1 Documentation](../stage_1/README.md) - Compare the differences
2. **LangGraph Documentation:** https://python.langchain.com/docs/langgraph (Understanding the framework)
3. **LangChain Academy:** Intro to LangGraph https://academy.langchain.com/courses/intro-to-langgraph (free course)
4. **Building a ReAct Agent with Langgraph: A Step-by-Step Guide:** https://medium.com/@umang91999/building-a-react-agent-with-langgraph-a-step-by-step-guide-812d02bafefa