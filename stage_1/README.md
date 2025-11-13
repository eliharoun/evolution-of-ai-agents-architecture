# Stage 1: Simple ReAct Agent

## What We're Building

Stage 1 introduces the basic building blocks of an AI agent for customer support. This is a simple agent that can look up order information and answer common questions about policies like returns and shipping.

The agent uses the **ReAct pattern** (Reasoning and Acting), which means it thinks about what to do, takes an action (like using a tool), and then observes the results before responding to the customer.

## What This Stage Achieves

By the end of Stage 1, you'll have a working agent that can:
- Look up order status by order number
- Answer frequently asked questions using semantic search
- Follow a simple reasoning process before acting
- Handle errors when things go wrong
- Stay focused on customer support tasks (won't answer off-topic questions)

This stage establishes the foundation that later stages will build upon.

## Folder Structure

```
stage_1/
├── agents/                  # Core agent logic
│   ├── state.py            # Defines what data flows through the agent
│   ├── react_agent.py      # The agent that thinks and acts
│   └── workflow.py         # Orchestrates the agent's flow
├── prompts/                 # Instructions for the agent
│   └── prompts.py          # System prompt with guardrails
├── demo.py                  # Run this to see the agent in action
└── README.md               # This file
```

The agent also uses shared components in the `common/` directory:
- `common/tools/` - The actual tools the agent can use (order lookup, FAQ search)
- `common/data/` - Sample data (orders, FAQs)
- `common/config.py` - Configuration settings
- `common/model_factory.py` - Handles different AI model providers

## Component Breakdown

### 1. State (state.py)

This defines the data structure that flows through the agent as it works. Think of it as the agent's working memory.

**What it contains:**
- `messages`: The conversation history between user and agent
- `iterations`: A counter to prevent the agent from getting stuck in loops

The state is very simple in Stage 1. Later stages add more complexity.

### 2. ReAct Agent (react_agent.py)

This is the brain of the operation. The agent follows a three-step pattern:

**Thought**: The agent reasons about what it needs to do
- "The user is asking about order status, so I need the order lookup tool"

**Action**: The agent decides to use a tool or respond directly
- Uses `get_order_status` tool or `search_faq` tool

**Observation**: The agent processes the tool results
- "The order was delivered on November 4th"

**What it does:**
- Initializes the AI model (OpenAI, Anthropic, or local Ollama)
- Binds tools to the model so it knows what actions it can take
- Has a `call_model` method that processes each step of the conversation
- Handles errors gracefully if something goes wrong

### 3. Workflow (workflow.py)

This orchestrates how the agent moves through its reasoning process using LangGraph.

**The flow:**
```
START → Agent (thinks) → Tools (acts) → Agent (observes) → END
```

**What it does:**
- Creates a graph with two nodes: the agent node and the tools node
- The agent node calls the ReAct agent to think and decide
- The tools node executes any tools the agent wants to use
- Uses `tools_condition` to automatically decide: "Did the agent want to use tools or is it done?"
- Loops back to the agent after tools run so it can observe results
- Ends when the agent is satisfied and ready to respond

Stage 1 is **stateless**, meaning each conversation starts fresh. Later stages add memory.

### 4. System Prompt (prompts.py)

This is the instruction manual for the agent. It tells the agent:

**What to do:**
- Act as a customer support agent for a clothing store
- Always use the ReAct pattern (think, act, observe)
- Use tools to get information instead of making things up
- Be friendly and professional

**What NOT to do:**
- Don't answer questions outside of customer support (like weather or coding)
- Don't mention technical terms like "tools" or "database"
- Don't make up information
- Don't give vague responses without the actual data

**Guardrails:**
The prompt includes strict rules to keep the agent focused on customer support. If someone asks about the weather, the agent politely declines and redirects.

## How the Components Work Together

Here's what happens when a customer asks "What's the status of order #12345?":

1. **User Input** → Workflow receives the question
2. **Agent Node** → ReAct agent reads the question and thinks:
   - "This is about order status"
   - "I need to use the get_order_status tool"
3. **Tools Node** → Executes `get_order_status("12345")`
   - Returns: Order delivered on Nov 4, 2025
4. **Agent Node Again** → Agent observes the result and formulates response:
   - "Your order #12345 was delivered on November 4th!"
5. **End** → Response sent back to user

The workflow uses LangGraph's built-in utilities (`tools_condition` and `ToolNode`) to handle the routing automatically. This keeps the code clean and simple.

## Available Tools

### Order Lookup Tool
- **Name**: `get_order_status`
- **What it does**: Searches a mock database for order information
- **When to use**: Customer asks about their order status
- **Data source**: `common/data/orders.py`

### FAQ Retrieval Tool
- **Name**: `search_faq`
- **What it does**: Uses semantic search to find relevant answers in the FAQ database
- **When to use**: Customer asks about policies, shipping, returns, payments
- **Technology**: ChromaDB vector database with SentenceTransformers
- **Data source**: `common/data/faqs.py`

The FAQ tool is more sophisticated - it converts text into embeddings (numerical representations) and finds semantically similar content, even if the exact words don't match.

## Running Stage 1

### Quick Start

```bash
# From project root
python stage_1/demo.py
```

This runs several example scenarios showing the agent in action.

### Using the Web Interface

```bash
# Terminal 1: Start backend
uvicorn backend.api:app --reload

# Terminal 2: Open frontend/index.html in your browser
```

The web interface shows you the agent's thought process in real-time.

### Configuration

Edit `.env` to change settings:
- `MODEL_TYPE`: Choose between openai, anthropic, or ollama
- `DEFAULT_MODEL`: Specific model name
- `MAX_ITERATIONS`: Prevent infinite loops (default 10)

## Key Concepts

### ReAct Pattern
The agent explicitly reasons before acting. You can see this in the logs:
- "Agent reasoning - iteration 1"
- "Agent action: using tools ['get_order_status']"
- "Agent action: final response"

### State Management
LangGraph manages state automatically. The state flows through nodes and gets updated at each step. The `add_messages` reducer ensures messages are properly accumulated.

### Built-in Utilities
Stage 1 uses LangGraph's utilities to simplify code:
- `tools_condition`: Automatically checks if the agent called tools
- `ToolNode`: Automatically executes tools and formats results

This means we don't need custom routing logic.

### Semantic Search with RAG
The FAQ tool uses Retrieval Augmented Generation (RAG):
1. FAQs are split into chunks and converted to embeddings
2. Stored in ChromaDB (a vector database)
3. When the agent searches, it converts the query to an embedding
4. Finds the most similar FAQ chunks
5. Returns relevant information to the agent

This allows the agent to find answers even when the question is phrased differently than the FAQ.

## What's Next

Stage 1 is intentionally simple to establish the foundation. It works well for basic queries, but has limitations:
- Only two tools
- No memory between conversations
- Can struggle with complex multi-step requests
- No way to handle ambiguous tool selection

**Stage 2** addresses these by adding more tools and demonstrating where a single agent starts to struggle. This sets up the need for more sophisticated patterns in later stages.

## Example Interactions

**Order Status Check:**
- User: "What's the status of my order #12345?"
- Agent thinks: Need order information
- Agent acts: Uses get_order_status tool
- Agent observes: Order delivered Nov 4
- Agent responds: "Your order #12345 was delivered on November 4th!"

**FAQ Query:**
- User: "How do I return an item?"
- Agent thinks: Need policy information
- Agent acts: Uses search_faq tool
- Agent observes: Gets return policy from FAQ
- Agent responds: "You can return items within 30 days..."

## Testing

Available test order IDs: 12345, 12346, 12347, 12348, 12349

Try these queries:
- "What's the status of order #12345?"
- "How do I return an item?"
- "Do you offer free shipping?"
- "What's the weather?" (should decline)
- "Check order #12345 and tell me your return policy" (multi-tool)

## Resources
1. **LangGraph Documentation:** https://langchain-ai.github.io/langgraph/
2. **LangChain Academy:** Intro to LangGraph https://academy.langchain.com/courses/intro-to-langgraph (free course)
3. **Building a ReAct Agent with Langgraph: A Step-by-Step Guide:** https://medium.com/@umang91999/building-a-react-agent-with-langgraph-a-step-by-step-guide-812d02bafefa