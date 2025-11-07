# Stage 1: Foundation - Simple ReAct Agent

## Overview

Stage 1 introduces the foundational **ReAct (Reasoning and Acting)** pattern for building AI agents. We'll build basic customer support agent for an online clothing retailer that can:

- Look up order status and details
- Answer frequently asked questions using semantic search
- Follow a simple linear flow with explicit reasoning steps
- Handle errors gracefully with appropriate fallbacks

**Learning Goals:**
- Understanding the ReAct pattern (Thought → Action → Observation)
- Building tools and integrating them with LangChain
- Creating LangGraph workflows with proper state management
- Implementing RAG (Retrieval Augmented Generation) with ChromaDB
- Using built-in LangGraph utilities like `tools_condition` and `ToolNode`

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    LangGraph Workflow                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  START → Agent → [tools_condition] → Tools → Agent          │
│            ↓                            ↑                   │
│           END ←─────────────────────────┘                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘

Components:
- Agent Node: LLM with tools (reasoning + action selection)
- Tools Node: Executes selected tools (observation)
- tools_condition: Built-in routing logic
```

### ReAct Pattern Flow

1. **Thought**: Agent receives user query and reasons about what information is needed
2. **Action**: Agent decides to either use a tool or respond directly
3. **Observation**: If tools were used, agent processes results and formulates response

### Tools

**1. Order Lookup Tool (`get_order_status`)**
- Queries mock order database
- Returns complete order details including items, status, tracking
- Data source: `common/data/orders.py`

**2. FAQ Retrieval Tool (`search_faq`)**
- Semantic search using ChromaDB + SentenceTransformers
- Implements RAG pattern with text chunking
- Persistent vector storage in `common/data/chroma_db/`
- Data source: `common/data/faqs.py`

## Project Structure

```
evolution-of-ai-agents-arch/
├── common/                          # Shared across all stages
│   ├── config.py                   # Configuration management
│   ├── logging_config.py           # Structured logging
│   ├── model_factory.py            # Model provider abstraction
│   ├── tools/                      # Shared tools
│   │   ├── order_lookup.py        # Order database and lookup tool
│   │   └── faq_retrieval.py       # ChromaDB RAG implementation
│   └── data/                       # Shared data
│       ├── orders.py              # Sample order data
│       ├── faqs.py                # FAQ knowledge base
│       └── chroma_db/             # ChromaDB storage (auto-generated)
│
├── frontend/                        # Shared web UI
│   └── index.html                  # Chat interface with thought process
│
├── stage_1/                         # Stage 1 specific
│   ├── agents/
│   │   ├── state.py               # AgentState definition
│   │   ├── react_agent.py         # ReAct agent implementation
│   │   └── workflow.py            # LangGraph workflow orchestration
│   ├── prompts/
│   │   └── prompts.py             # System prompt with guardrails
│   ├── backend/
│   │   └── api.py                 # FastAPI backend with streaming
│   ├── .env.example               # Environment variables template
│   ├── demo.py                    # Demonstration script
│   └── README.md                  # This file
│
└── requirements.txt                 # Python dependencies (project-wide)
```

## Setup Instructions

### 1. Prerequisites

- Python 3.9 or higher
- OpenAI API key (or Ollama for local models)
- pip or conda for package management

### 2. Install Dependencies

From the **project root** directory:

```bash
# Create and activate virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies (shared across all stages)
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
# Create .env file from template
cp stage_1/.env.example .env

# Edit .env and add your API keys or set MODEL_TYPE
# Options: MODEL_TYPE=openai|anthropic|ollama
```

### 4. Initialize FAQ Vector Store

The FAQ vector store will be automatically created on first run. To manually initialize:

```python
from common.tools.faq_retrieval import get_faq_retriever

# This will create the ChromaDB collection and generate embeddings
retriever = get_faq_retriever()
print(f"Initialized with {retriever.collection.count()} FAQ chunks")
```

**Note:** ChromaDB data is stored in `common/data/chroma_db/` (shared across all stages)

## Usage

### Option 1: Demo Script (Recommended for First Run)

Run the interactive demo that shows 6 different scenarios:

```bash
python stage_1/demo.py
```

This will demonstrate:
- Order status lookups
- FAQ queries (returns, shipping)
- Guardrail enforcement (out-of-scope queries)
- Multi-tool coordination

### Option 2: Web Interface

**Step 1: Start the FastAPI backend**

```bash
uvicorn common.backend.api:app --reload
```

The backend will start on `http://localhost:8000`

**Step 2: Open the frontend**

Open `frontend/index.html` in your web browser (from the project root).

**Features:**
- 💬 Real-time chat interface
- 🧠 Thought process panel (click to collapse to the right)
- 🔄 Streaming responses
- 📊 Visibility into tool calls and observations

### Option 3: Programmatic Usage

```python
from stage_1.agents.workflow import AgentWorkflow

# Initialize workflow (uses config MODEL_TYPE)
workflow = AgentWorkflow()

# Single query
result = workflow.invoke("What's the status of order #12345?")

# Extract response
messages = result["messages"]
final_response = messages[-1].content
print(final_response)

# Streaming
for chunk in workflow.stream("How do I return an item?"):
    for node_name, node_output in chunk.items():
        print(f"Node: {node_name}")
        print(f"Output: {node_output}")
```

## Example Interactions

### Example 1: Order Status Check

**User:** "What's the status of my order #12345?"

**Agent Process:**
1. 💭 Thought: "User asking about order status, need to use get_order_status tool"
2. 🔍 Action: Calls `get_order_status("12345")`
3. 👁️ Observation: Receives order details (Delivered, items, tracking, etc.)
4. 💬 Response: Formats and presents order information to user

### Example 2: FAQ Query

**User:** "How do I return an item?"

**Agent Process:**
1. 💭 Thought: "User asking about return policy, need to search FAQ"
2. 🔍 Action: Calls `search_faq("How do I return an item?")`
3. 👁️ Observation: ChromaDB returns relevant FAQ chunks
4. 💬 Response: Presents return policy information

### Example 3: Guardrails in Action

**User:** "What's the weather today?"

**Agent Response:**
"I'm a customer support agent for our clothing store and can only help with order-related questions, shipping, returns, payments, and account issues. For other questions, please use a general-purpose assistant."

## Key Concepts Demonstrated

### 1. ReAct Pattern

The agent explicitly follows Reasoning → Acting → Observation:

```python
# From agents/react_agent.py
def call_model(self, state: AgentState) -> dict:
    """
    Thought + Action: Agent reasons and decides on tools
    """
    response = self.model_with_tools.invoke(messages)
    return {"messages": [response], "iterations": iterations + 1}

# Tools Node handles Observation automatically
# Then loops back to agent for next thought
```

### 2. LangGraph State Management

```python
# From agents/state.py
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    iterations: int
```

- `messages`: Conversation history with proper reducer (`add_messages`)
- `iterations`: Counter to prevent infinite loops

### 3. Built-in Utilities

Stage 1 uses LangGraph's built-in utilities for cleaner code:

- `tools_condition`: Automatic routing based on tool calls
- `ToolNode`: Automatic tool execution and response formatting

```python
# From agents/workflow.py
workflow.add_conditional_edges(
    "agent",
    tools_condition,  # No custom logic needed!
    {"tools": "tools", END: END}
)
```

### 4. RAG with ChromaDB

```python
# From common/tools/faq_retrieval.py
class FAQRetriever:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection = self._get_or_create_collection()
    
    def search(self, query: str, top_k: int = 2):
        query_embedding = self.model.encode([query])
        results = self.collection.query(query_embeddings=query_embedding, n_results=top_k)
        return formatted_results
```

**Benefits:**
- Persistent storage (vector DB persists across runs)
- Fast semantic search
- Text chunking for optimal retrieval
- Metadata tracking

### 5. Guardrails

The system prompt includes guardrails to keep the agent focused:

```python
# From prompts/prompts.py
SYSTEM_PROMPT = """
IMPORTANT GUARDRAILS:
- You must ONLY answer questions related to our clothing retail business
- If asked about topics outside retail customer service, politely decline
...
"""
```

## Testing the Agent

### Test Order IDs

Available in the mock database:
- `12345`: Delivered order (2 items)
- `12346`: Shipped order (1 item)
- `12347`: Processing order (2 items)
- `12348`: Shipped order (shoes)
- `12349`: Delivered order (sweater)

### Test Queries

**Order-related:**
- "What's the status of order #12345?"
- "Can you check order #12346?"
- "Track my order #12347"

**FAQ-related:**
- "How do I return an item?"
- "Do you offer free shipping?"
- "What payment methods do you accept?"
- "How long does shipping take?"

**Guardrails testing:**
- "What's the weather today?" (should decline)
- "Write me some Python code" (should decline)
- "Tell me a joke" (should decline)

**Multi-tool:**
- "Check order #12345 and tell me your return policy"

## API Endpoints

When running the backend (`uvicorn common.backend.api:app --reload`):

### GET /
Health check endpoint
```json
{
  "status": "online",
  "service": "Customer Support Agent",
  "stage": "1"
}
```

### GET /health
Detailed health status
```json
{
  "status": "healthy",
  "workflow_initialized": true,
  "model_type": "ollama"
}
```

### POST /chat
Chat with the agent

**Request:**
```json
{
  "message": "What's the status of order #12345?",
  "stream": true
}
```

**Response (streaming):**
Server-Sent Events with:
- `type: "thought"` - Agent reasoning and tool selection
- `type: "observation"` - Tool execution results
- `type: "response"` - Final agent response
- `type: "done"` - Stream complete

### GET /tools
List available tools
```json
{
  "tools": [
    {"name": "get_order_status", "description": "..."},
    {"name": "search_faq", "description": "..."}
  ]
}
```

## Configuration Options

Edit `.env` to customize:

```bash
# Model Selection
MODEL_TYPE=ollama                # openai, anthropic, or ollama
DEFAULT_MODEL=llama3.1
DEFAULT_TEMPERATURE=0

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1

# Agent Behavior
MAX_ITERATIONS=10                # Prevent infinite loops

# Backend
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
```

To use different model providers:

```python
# Uses config.MODEL_TYPE by default
workflow = AgentWorkflow()

# Or override explicitly
workflow = AgentWorkflow(model_type="openai")
workflow = AgentWorkflow(model_type="anthropic")
workflow = AgentWorkflow(model_type="ollama")
```

**Model Factory Pattern:**
The agent uses a factory pattern (in `common/model_factory.py`) to abstract model initialization. This makes it easy to:
- Switch between providers without changing agent code
- Add new providers in one place
- Reuse model creation logic across all stages

## Troubleshooting

### ChromaDB Permission Issues

If you encounter permission errors:
```bash
chmod -R 755 common/data/chroma_db/
```

### Port Already in Use

Change the port in `.env`:
```bash
BACKEND_PORT=8001
```

### Import Errors

Make sure you're running from the project root and have installed dependencies:
```bash
cd /path/to/evolution-of-ai-agents-arch
pip install -r requirements.txt
```

### Model Configuration Issues

Verify your `.env` file has the right MODEL_TYPE and corresponding API key:
```bash
cat .env | grep MODEL_TYPE
```

## What's Next?

**Stage 2** will build upon this foundation by:
- Adding more sophisticated tools (refunds, shipping modifications, inventory)
- Demonstrating limitations of single-agent architectures
- Showing tool selection confusion and context loss problems


## Resources

- [LangGraph Documentation](https://python.langchain.com/docs/langgraph)
- [LangChain Tools](https://python.langchain.com/docs/modules/agents/tools/)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [ReAct Paper](https://arxiv.org/abs/2210.03629)
