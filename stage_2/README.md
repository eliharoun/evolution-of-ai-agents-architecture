# Stage 2: Sophisticated Single Agent - Tool Complexity & Limitations

## Overview

Stage 2 shows what happens when you give a single ReAct agent **too many tools** to choose from. Using the **exact same architecture** as Stage 1, but with **7 tools instead of 2**, this stage reveals the inherent limitations of single-agent systems when faced with complexity.

## The Problem Stage 2 Solves

**Question:** *"What happens when we give a single agent too many options?"*

**Answer:** The agent starts to struggle with:
- **Tool Selection Confusion** - Which tool should I use for "returning" an item?
- **Sequential Bottlenecks** - Processing multiple requests one-by-one instead of in parallel
- **Context Loss** - Forgetting earlier parts of complex multi-step requests
- **Planning Difficulties** - Unable to create efficient execution strategies

## Tools Overview

### Stage 1 Tools (2) ✅
- `get_order_status` - Order lookup by ID
- `search_faq` - FAQ knowledge base search

### Stage 2 Additional Tools (5) 🆕
- `get_customer_account` - Customer history and preferences
- `process_refund` - Initiate refunds (stateful)
- `modify_shipping` - Change addresses, expedite delivery (stateful)
- `check_inventory` - Product availability and variants
- `create_ticket` - Escalate complex issues (stateful)

**Total: 7 tools** (vs 2 in Stage 1)

## Architecture

Same LangGraph workflow as Stage 1, with added **struggle monitoring**:

```
┌─────────────────────────────────────────────────────────────┐
│                Stage 2: Same ReAct Pattern                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  START → Agent → [tools_condition] → Tools → Agent         │
│            ↓                            ↑                   │
│           END ←─────────────────────────┘                   │
│                                                             │
│  📊 NEW: Struggle Monitoring Throughout                    │
│  - High iteration detection                                 │
│  - Tool confusion alerts                                    │
│  - Context loss identification                              │
│  - Sequential bottleneck tracking                          │
└─────────────────────────────────────────────────────────────┘
```

## Struggle Indicators

Stage 2 automatically detects and displays when the agent is struggling:

### 🚨 High Iterations
- **What**: Agent takes ≥4 iterations to complete tasks (threshold lowered from >4)
- **Why**: Tool selection confusion, uncertainty about next steps
- **UI Display**: Red badge + "Agent took 4 iterations to complete the task..."
- **Log**: `🚨 STRUGGLE DETECTED: High iteration count (4) - agent may be confused`

### 🚨 Tool Confusion
- **What**: Agent uses 2+ tools simultaneously or in rapid succession  
- **Example**: Parallel calls like `['get_order_status', 'check_inventory']`
- **UI Display**: "Agent used 3 different tools simultaneously..."
- **Log**: `🚨 STRUGGLE DETECTED: Parallel tool usage - agent may be confused about dependencies`

### 🚨 Context Loss
- **What**: Agent repeats same tool calls >2 times, forgetting previous results
- **Example**: Calling `check_inventory` 3 times in one response
- **UI Display**: "Agent repeatedly called the same tools: check_inventory (3x)..."
- **Log**: `🚨 STRUGGLE DETECTED: Context loss - tool 'check_inventory' used 3 times`

### 🎨 UI Struggle Display
**Option 1 + 2 Implementation:**
- **Red Badge**: Shows in response card header: `[⚠️ 2 Struggles]`
- **Detailed Summary**: Pale red card inside response with comprehensive analysis
- **Real-time Detection**: No intermediate alerts, just final summary

## Setup & Usage

### Quick Start

```bash
# Same setup as Stage 1
cd evolution-of-ai-agents-arch
pip install -r requirements.txt

# Run Stage 2 demo
python stage_2/demo.py
```

### Web Interface

```bash
# Start unified backend with Stage 2 
uvicorn common.backend.api:app --reload
# Reads STAGE=2 from .env automatically

# Open frontend/index.html
open frontend/index.html
```

## Demo Scenarios

### Simple Scenarios (Work Fine with OpenAI)
1. **Order Status Check** - `"What's the status of my order #12345?"`
2. **FAQ Question** - `"How do I return an item?"`  
3. **Account Lookup** - `"Can you tell me about my account history for order #12345?"`

### Complex Scenarios (Trigger Struggles)
4. **Multi-Step Dependency Chain** - `"I want to reorder the t-shirt from my previous order, but first check if it's still available in my size and preferred colors. If not available, find similar items in the same price range that ARE in stock, then tell me the fastest shipping option for whichever item you recommend."`

5. **Missing Critical Information** - `"I'm really frustrated! I ordered something weeks ago and it's still not here. This is unacceptable and I want a refund immediately! I've been a loyal customer and spent hundreds of dollars with you. Fix this now!"` *(No order ID provided)*

6. **Complex Conditional Logic** - `"Check if order #12346 has shipped yet. If it hasn't, cancel it and refund me. But if it HAS shipped, then expedite it to overnight instead. Also, regardless of what happens with that order, I want to check if you have the same item in a different color for my next purchase."`

**Note**: These scenarios are designed to demonstrate when single agents break down with complex, multi-step requests.

### The Complex Birthday Gift Scenario

**Input:**
*"My order #12345 hasn't arrived, it was supposed to be a birthday gift for tomorrow. Can you check where it is, and if it won't arrive on time, I want to either expedite shipping or get a refund and buy locally. Also, do you have the same item in blue instead of red for future reference?"*

**What Should Happen:**
- Agent struggles to plan multiple steps
- Tool selection confusion (expedite vs refund?)
- Context loss across the long request
- Sequential processing instead of efficient planning

**Expected Struggles:**
- High iteration count
- Tool confusion events
- Difficulty maintaining context across multiple sub-questions

## Configuration

Uses same `.env` configuration as Stage 1, plus stage selection and checkpointing:

```bash
MODEL_TYPE=openai              # Recommended: openai (best tool calling)
STAGE=2                        # Set to 2 for this stage
ENABLE_CHECKPOINTING=true      # Enable conversation memory (optional)

# Add corresponding API keys:
OPENAI_API_KEY=your_key_here
# or ANTHROPIC_API_KEY=your_key_here
```

### 💾 Checkpointing (Conversation Memory)

Stage 2 now supports **optional checkpointing** for maintaining conversation history:

**When Enabled:**
- Agent remembers previous messages in the conversation
- Follow-up questions work naturally: "What order did I ask about?"
- Session-based memory (60-minute timeout)
- Uses LangGraph's InMemorySaver

**To Enable:**
```bash
ENABLE_CHECKPOINTING=true STAGE=2 python -m common.backend.api
```

**Test Queries:**
1. "What's the status of order #12345?"
2. "What order did I just ask about?" ← Agent remembers #12345!

**Note**: ReAct (Stage 2) is designed for multi-turn conversations, so checkpointing works naturally. ReWOO (Stage 3.1) is single-turn by design.

**Important**: Ollama/llama3.1 has poor tool-calling capabilities and may output tool descriptions instead of making actual tool calls. OpenAI and Anthropic models work much better.

## Comparing Stages

| Aspect | Stage 1 | Stage 2 |
|--------|---------|---------|
| **Tools** | 2 | 7 |
| **Architecture** | Simple ReAct | Same ReAct |
| **Scenarios** | Basic | Complex |
| **Monitoring** | Basic logging | Struggle detection |
| **Performance** | Smooth | Shows limitations |
| **Purpose** | Learn fundamentals | Discover problems |

## What Stage 2 Teaches

### 🔍 **Single Agent Limitations**
- Tool selection becomes harder with more options (7 vs 2)
- Sequential processing creates bottlenecks when parallel execution would be better
- Context management challenges at scale - forgetting previous tool results
- No built-in planning or coordination between tool calls

### 📊 **Complexity Challenges**  
- More tools ≠ better performance (actually makes it worse)
- Choice paralysis - with 7 tools, which one to use?
- Difficulty prioritizing actions in multi-step requests
- Context loss when handling complex, long requests

### 🎯 **When Single Agents Break**
- Complex multi-part requests with dependencies
- Requests requiring multiple tools in sequence or parallel
- Time-sensitive scenarios with trade-offs (expedite vs refund)
- Situations needing parallel information gathering
- Conditional logic: "If X, then Y, otherwise Z"

## Learning Exercises

1. **Run the Complex Scenario** - See the agent struggle in real-time
2. **Monitor Struggle Stats** - Watch `/struggles` endpoint during complex queries  
3. **Compare with Stage 1** - Run same query in both stages
4. **Create New Complex Scenarios** - Design requests that trigger struggles
5. **Analyze Tool Confusion** - Look for conflicting tool usage in logs

## What's Next?

**Stage 3** will solve these problems using advanced single-agent patterns:
- **ReWOO** - Plan all tool calls upfront, then execute efficiently
- **Reflection** - Self-evaluate and improve responses
- **Plan-and-Execute** - Create dynamic plans that adapt to findings

The same complex scenarios that break Stage 2 will work smoothly in Stage 3.

## Resources

- [Stage 1 Documentation](../stage_1/README.md) - Compare the differences
- [LangGraph Documentation](https://python.langchain.com/docs/langgraph) - Understanding the framework

Ready to see how advanced patterns solve these problems? → **Stage 3**
