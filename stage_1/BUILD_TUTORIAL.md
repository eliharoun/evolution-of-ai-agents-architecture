# Building Your First AI Agent: A Step-by-Step Tutorial

Welcome! In this tutorial, you'll build a working AI agent from the ground up. By the end, you'll have an agent that can help customers check their orders and answer common questions.

## What You'll Learn

- How to structure an AI agent project
- How to create tools that your agent can use
- How to build the ReAct pattern (Reasoning and Acting)
- How to orchestrate everything with LangGraph
- How to test and run your agent

## Prerequisites

Before we start, make sure you have:
- Python 3.9 or higher installed
- Basic understanding of Python (functions, classes, dictionaries)
- A text editor (VS Code recommended)
- An OpenAI API key OR Ollama installed locally

Don't worry if you're not an expert - we'll explain everything as we go!

## Tutorial Overview

We'll build our agent in 5 steps:
1. Set up the project structure
2. Create tools for the agent
3. Define the agent's state
4. Build the ReAct agent
5. Create the workflow that orchestrates everything

Let's get started!

---

## Step 1: Set Up Your Project Structure

First, let's understand what we're building. An AI agent needs:
- **Tools**: Actions the agent can take (like looking up an order)
- **State**: The agent's working memory
- **Brain**: The logic that decides what to do
- **Workflow**: The orchestrator that connects everything

### Create the Folders

```bash
# Start from your project root
mkdir -p stage_1/agents
mkdir -p stage_1/prompts
mkdir -p common/tools
mkdir -p common/data
```

Your structure should look like:
```
project/
├── common/
│   ├── tools/
│   └── data/
└── stage_1/
    ├── agents/
    └── prompts/
```

**Why this structure?**
- `common/` holds code shared across all stages (tools, data)
- `stage_1/` holds code specific to this stage
- Separating concerns makes code easier to understand and maintain

---

## Step 2: Create Your First Tool - Order Lookup

An agent without tools is just a chatbot. Tools give the agent real capabilities. Let's create a tool that looks up order information.

### Create Sample Data

First, we need some orders to look up. Create `common/data/orders.py`:

```python
"""Sample order data for our demo."""

ORDERS = {
    "12345": {
        "order_id": "12345",
        "customer_name": "John Smith",
        "status": "Delivered",
        "items": [
            {"name": "Blue Jeans", "quantity": 1, "price": 59.99},
            {"name": "White T-Shirt", "quantity": 2, "price": 19.99}
        ],
        "total": 99.97,
        "order_date": "2025-10-15",
        "delivery_date": "2025-11-04",
        "tracking_number": "1Z999AA10123456784"
    },
    "12346": {
        "order_id": "12346",
        "customer_name": "Jane Doe",
        "status": "Shipped",
        "items": [
            {"name": "Red Sweater", "quantity": 1, "price": 79.99}
        ],
        "total": 79.99,
        "order_date": "2025-11-01",
        "estimated_delivery": "2025-11-15",
        "tracking_number": "1Z999AA10123456785"
    }
}
```

**What's happening here?**
- We're creating a dictionary that maps order IDs to order details
- In a real app, this would be a database query
- For learning, a dictionary is simpler and faster

### Create the Tool

Now create `common/tools/order_lookup.py`:

```python
"""Tool for looking up order information."""

from langchain_core.tools import tool
from common.data.orders import ORDERS


@tool
def get_order_status(order_id: str) -> str:
    """
    Look up the status and details of an order.
    
    Args:
        order_id: The order ID to look up (e.g., "12345")
    
    Returns:
        A formatted string with order details, or an error message
    """
    # Clean up the order ID (remove # if present)
    order_id = order_id.replace("#", "").strip()
    
    # Look up the order
    order = ORDERS.get(order_id)
    
    if not order:
        return f"Order {order_id} not found. Please check the order number."
    
    # Format the response
    result = f"Order #{order['order_id']}\n"
    result += f"Customer: {order['customer_name']}\n"
    result += f"Status: {order['status']}\n"
    
    # Add items
    result += "\nItems:\n"
    for item in order['items']:
        result += f"  - {item['name']} (x{item['quantity']}) - ${item['price']}\n"
    
    result += f"\nTotal: ${order['total']}\n"
    
    # Add tracking if available
    if 'tracking_number' in order:
        result += f"Tracking: {order['tracking_number']}\n"
    
    # Add dates
    if 'delivery_date' in order:
        result += f"Delivered: {order['delivery_date']}\n"
    elif 'estimated_delivery' in order:
        result += f"Estimated Delivery: {order['estimated_delivery']}\n"
    
    return result
```

**Let's break this down:**

1. **`@tool` decorator**: This tells LangChain "this function is a tool the agent can use"
2. **Docstring**: The agent reads this to understand what the tool does. Be clear!
3. **Input validation**: We clean up the input (remove #, strip whitespace)
4. **Error handling**: If order not found, we return a helpful message
5. **Formatting**: We format the output nicely so the agent can read it

**Test it yourself:**
```python
# Try this in a Python shell
from common.tools.order_lookup import get_order_status

result = get_order_status("12345")
print(result)
```

You should see the order details printed nicely!

---

## Step 3: Create Your Second Tool - FAQ Search

The second tool will search through frequently asked questions. This is more sophisticated - it uses semantic search to find relevant answers even if the question is worded differently.

### Create FAQ Data

Create `common/data/faqs.py`:

```python
"""Frequently asked questions about our clothing store."""

FAQS = [
    {
        "category": "Returns",
        "question": "What is your return policy?",
        "answer": "You can return any item within 30 days of delivery for a full refund. Items must be unworn with tags attached."
    },
    {
        "category": "Shipping",
        "question": "How long does shipping take?",
        "answer": "Standard shipping takes 5-7 business days. Express shipping takes 2-3 business days."
    },
    {
        "category": "Shipping",
        "question": "Do you offer free shipping?",
        "answer": "Yes! We offer free standard shipping on orders over $50."
    },
    {
        "category": "Payment",
        "question": "What payment methods do you accept?",
        "answer": "We accept all major credit cards (Visa, MasterCard, Amex), PayPal, and Apple Pay."
    }
]
```

### Create the FAQ Search Tool

Create `common/tools/faq_retrieval.py`:

```python
"""Tool for searching FAQs using semantic search."""

import chromadb
from sentence_transformers import SentenceTransformer
from langchain_core.tools import tool
from common.data.faqs import FAQS


class FAQRetriever:
    """Handles FAQ storage and retrieval using ChromaDB."""
    
    def __init__(self):
        # Initialize the embedding model
        # This converts text into numbers that capture meaning
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize ChromaDB (vector database)
        self.client = chromadb.PersistentClient(path="common/data/chroma_db")
        
        # Get or create the FAQ collection
        self.collection = self._get_or_create_collection()
    
    def _get_or_create_collection(self):
        """Create the FAQ collection if it doesn't exist."""
        collection_name = "faqs"
        
        # Try to get existing collection
        try:
            collection = self.client.get_collection(collection_name)
            return collection
        except:
            pass
        
        # Create new collection
        collection = self.client.create_collection(collection_name)
        
        # Add FAQs to the collection
        for i, faq in enumerate(FAQS):
            # Combine question and answer for better search
            text = f"Q: {faq['question']}\nA: {faq['answer']}"
            
            # Convert text to embedding
            embedding = self.model.encode([text])[0]
            
            # Store in ChromaDB
            collection.add(
                ids=[str(i)],
                embeddings=[embedding.tolist()],
                documents=[text],
                metadatas=[{"category": faq["category"]}]
            )
        
        return collection
    
    def search(self, query: str, top_k: int = 2):
        """Search for relevant FAQs."""
        # Convert query to embedding
        query_embedding = self.model.encode([query])[0]
        
        # Search in ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=top_k
        )
        
        # Format results
        if not results['documents'][0]:
            return "No relevant FAQs found."
        
        formatted = "Relevant FAQs:\n\n"
        for doc in results['documents'][0]:
            formatted += doc + "\n\n"
        
        return formatted.strip()


# Create a global retriever instance
_retriever = None

def get_faq_retriever():
    """Get or create the FAQ retriever."""
    global _retriever
    if _retriever is None:
        _retriever = FAQRetriever()
    return _retriever


@tool
def search_faq(query: str) -> str:
    """
    Search the FAQ knowledge base for relevant information.
    
    Use this for questions about policies, shipping, returns, or general info.
    
    Args:
        query: The question to search for
        
    Returns:
        Relevant FAQ entries that answer the question
    """
    retriever = get_faq_retriever()
    return retriever.search(query)
```

**What's happening here?**

1. **SentenceTransformer**: Converts text into embeddings (numbers that capture meaning)
2. **ChromaDB**: A vector database that stores and searches embeddings
3. **Semantic Search**: Finds FAQs based on meaning, not exact words
4. **Singleton Pattern**: We create one retriever and reuse it (the `_retriever` global)

**Why semantic search?**
- Customer asks: "Can I send stuff back?"
- FAQ says: "What is your return policy?"
- Semantic search knows these are related!

---

## Step 4: Define the Agent's State

The state is the agent's working memory. It tracks the conversation and progress.

Create `stage_1/agents/state.py`:

```python
"""State management for the customer support agent."""

from typing import Annotated, Sequence
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """
    The state represents data flowing through the agent.
    
    Think of this as the agent's working memory - it remembers
    the conversation and how many times it has thought/acted.
    """
    # The conversation history
    # add_messages is a special function that properly combines messages
    messages: Annotated[Sequence[BaseMessage], add_messages]
    
    # Counter to prevent infinite loops
    iterations: int
```

**Breaking it down:**

1. **TypedDict**: Defines the structure of our state
2. **messages**: The conversation history
   - `Annotated[..., add_messages]`: Special reducer that properly merges messages
   - Handles tool calls and responses correctly
3. **iterations**: Counts how many times the agent has looped
   - Prevents the agent from getting stuck forever

**Why do we need state?**
- The agent needs to remember what the user said
- It needs to track tool calls and their results
- It needs to know when to stop (via iterations)

---

## Step 5: Build the ReAct Agent

Now for the exciting part - the agent's brain! This is where the thinking happens.

### Create the System Prompt

First, create `stage_1/prompts/prompts.py`:

```python
"""System prompts for the agent."""

SYSTEM_PROMPT = """You are a helpful customer support agent for an online clothing retailer.

Your job is to help customers with:
- Order status and tracking
- Returns and refunds
- Shipping information
- General questions about policies

IMPORTANT RULES:

1. Think before you act:
   - What information do you need?
   - Which tool should you use?
   - Or can you answer directly?

2. Use your tools:
   - get_order_status: Check order details
   - search_faq: Search policies and information

3. Always include the actual information in your response:
   - Don't say "I found your order" - tell them the status!
   - Don't say "Let me know if you need help" - give the full answer!

4. Be professional and friendly:
   - Use natural language
   - Don't mention "tools" or "database"
   - Act like a human customer service rep

5. Stay in scope:
   - ONLY answer questions about the clothing store
   - If asked about other topics, politely decline

Remember: Think → Act → Observe → Respond
"""
```

**Why is the prompt so detailed?**
- The prompt is the agent's instruction manual
- Clear instructions = better agent behavior
- We set guardrails to keep it focused

### Build the Agent

Create `stage_1/agents/react_agent.py`:

```python
"""ReAct Agent - the brain of the operation."""

from langchain_core.messages import SystemMessage, AIMessage
from langchain_openai import ChatOpenAI  # Or your preferred model

from stage_1.agents.state import AgentState
from common.tools.order_lookup import get_order_status
from common.tools.faq_retrieval import search_faq
from stage_1.prompts.prompts import SYSTEM_PROMPT


class ReactAgent:
    """
    The ReAct Agent follows a simple pattern:
    1. THINK: What do I need to do?
    2. ACT: Use a tool or respond
    3. OBSERVE: What happened?
    """
    
    def __init__(self, model_name: str = "gpt-4o-mini", temperature: float = 0):
        """
        Initialize the agent.
        
        Args:
            model_name: Which AI model to use
            temperature: 0 = consistent, higher = more creative
        """
        # Create the base model
        self.model = ChatOpenAI(
            model=model_name,
            temperature=temperature
        )
        
        # Define available tools
        self.tools = [get_order_status, search_faq]
        
        # Bind tools to the model
        # This teaches the model what tools it can use
        self.model_with_tools = self.model.bind_tools(self.tools)
        
        # Store the system prompt
        self.system_prompt = SYSTEM_PROMPT
        
        print(f"Agent initialized with {len(self.tools)} tools")
    
    def call_model(self, state: AgentState) -> dict:
        """
        The main thinking function.
        
        This is called at each step of the workflow.
        The agent thinks about what to do next.
        """
        # Get current messages and iteration count
        messages = state["messages"]
        iterations = state.get("iterations", 0)
        
        print(f"\n--- Agent Thinking (Iteration {iterations + 1}) ---")
        
        # Add system prompt if not already there
        if not any(isinstance(m, SystemMessage) for m in messages):
            messages = [SystemMessage(content=self.system_prompt)] + list(messages)
        
        try:
            # Call the model - this is where thinking happens!
            response = self.model_with_tools.invoke(messages)
            
            # Log what the agent decided to do
            if hasattr(response, "tool_calls") and response.tool_calls:
                tool_names = [tc["name"] for tc in response.tool_calls]
                print(f"Agent decided to use tools: {tool_names}")
            else:
                print("Agent decided to respond directly")
            
            # Return updated state
            return {
                "messages": [response],
                "iterations": iterations + 1
            }
            
        except Exception as e:
            print(f"Error: {e}")
            # Return a graceful error message
            error_msg = AIMessage(
                content="I apologize, but I encountered an error. Please try again."
            )
            return {
                "messages": [error_msg],
                "iterations": iterations + 1
            }
```

**Understanding the code:**

1. **`__init__`**: Sets up the agent
   - Creates the AI model
   - Defines available tools
   - Binds tools to model (model learns what tools exist)

2. **`call_model`**: The thinking function
   - Gets current conversation state
   - Adds system prompt if needed
   - Calls the model to decide what to do
   - Returns updated state

3. **Error handling**: If something breaks, return a friendly error

**The magic of `bind_tools`:**
When you bind tools to a model, the model learns:
- What tools are available
- What each tool does (from the docstring)
- What parameters each tool needs

---

## Step 6: Create the Workflow

The workflow orchestrates everything. It's like a flowchart that determines the order of operations.

Create `stage_1/agents/workflow.py`:

```python
"""LangGraph workflow - the orchestrator."""

from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import HumanMessage

from stage_1.agents.state import AgentState
from stage_1.agents.react_agent import ReactAgent


class AgentWorkflow:
    """
    Orchestrates the agent's flow:
    START → Agent → Tools? → Agent → END
    """
    
    def __init__(self):
        """Set up the workflow."""
        # Create the agent
        self.agent = ReactAgent()
        
        # Build the workflow graph
        self.workflow = self._build_graph()
    
    def _build_graph(self):
        """
        Build the workflow graph.
        
        The graph has two nodes:
        1. Agent: Thinks and decides
        2. Tools: Executes tool calls
        
        Flow:
        START → agent → [does it need tools?] → tools → agent → END
        """
        # Create the graph
        graph = StateGraph(AgentState)
        
        # Add the agent node
        graph.add_node("agent", self.agent.call_model)
        
        # Add the tools node
        # ToolNode automatically executes tool calls
        graph.add_node("tools", ToolNode(self.agent.tools))
        
        # Define the flow
        # Start with the agent
        graph.add_edge(START, "agent")
        
        # After agent, decide: tools or end?
        # tools_condition is a built-in function that checks
        # if the agent called any tools
        graph.add_conditional_edges(
            "agent",
            tools_condition,  # The decision function
            {
                "tools": "tools",  # If tools were called, go to tools
                END: END           # Otherwise, we're done
            }
        )
        
        # After tools execute, go back to agent
        # This creates the loop: Agent → Tools → Agent → ...
        graph.add_edge("tools", "agent")
        
        # Compile the graph
        return graph.compile()
    
    def run(self, user_input: str) -> str:
        """
        Run the agent with a user input.
        
        Args:
            user_input: What the user is asking
            
        Returns:
            The agent's final response
        """
        print(f"\n{'='*60}")
        print(f"User: {user_input}")
        print(f"{'='*60}")
        
        # Create initial state
        initial_state = {
            "messages": [HumanMessage(content=user_input)],
            "iterations": 0
        }
        
        # Run the workflow
        result = self.workflow.invoke(initial_state)
        
        # Extract the final response
        final_message = result["messages"][-1]
        response = final_message.content
        
        print(f"\nAgent: {response}")
        print(f"{'='*60}\n")
        
        return response
```

**Understanding the workflow:**

1. **StateGraph**: Creates a graph where each node can modify the state
2. **Nodes**: 
   - `agent`: Calls the agent's thinking function
   - `tools`: Automatically executes any tool calls
3. **Edges**:
   - `START → agent`: Begin with agent thinking
   - `agent → [condition] → tools or END`: Decide based on tool calls
   - `tools → agent`: After tools, agent observes and thinks again

**The flow in action:**
```
User asks question
    ↓
[Agent Node] "I need to use get_order_status"
    ↓
[Tools Node] Executes get_order_status("12345")
    ↓
[Agent Node] "Order was delivered Nov 4. I'll tell the user."
    ↓
END
```

---

## Step 7: Test Your Agent!

Create `stage_1/demo.py` to test everything:

```python
"""Demo script to test the agent."""

from stage_1.agents.workflow import AgentWorkflow


def main():
    """Run demo scenarios."""
    print("\n🤖 Customer Support Agent Demo\n")
    
    # Create the workflow
    workflow = AgentWorkflow()
    
    # Test scenarios
    scenarios = [
        "What's the status of order #12345?",
        "How do I return an item?",
        "Do you offer free shipping?",
        "What's the weather today?",  # Should decline (out of scope)
    ]
    
    for scenario in scenarios:
        workflow.run(scenario)
        input("Press Enter for next scenario...")


if __name__ == "__main__":
    main()
```

**Run it:**
```bash
python stage_1/demo.py
```

**What you should see:**
1. Agent thinks about what to do
2. Logs show tool calls
3. Final response to user

---

## Step 8: Understanding What's Happening

Let's trace through a real example step by step.

### Example: "What's the status of order #12345?"

**Step 1: User Input**
```
User: What's the status of order #12345?
```

**Step 2: Agent Thinks (First Iteration)**
```python
# Agent receives message
# System prompt is added
# Model thinks: "User wants order status, I need get_order_status tool"
# Returns: AIMessage with tool_call
```

**Step 3: Tools Condition**
```python
# Checks: Did agent call any tools?
# Yes! tool_calls = [{"name": "get_order_status", "args": {"order_id": "12345"}}]
# Decision: Route to tools node
```

**Step 4: Tools Execute**
```python
# ToolNode calls: get_order_status("12345")
# Returns: "Order #12345\nCustomer: John Smith\nStatus: Delivered\n..."
# Adds ToolMessage to state with results
```

**Step 5: Agent Observes (Second Iteration)**
```python
# Agent sees the tool results
# Model thinks: "Order was delivered on Nov 4. I'll format a response."
# Returns: AIMessage with final response (no tool calls)
```

**Step 6: Tools Condition Again**
```python
# Checks: Did agent call any tools?
# No! tool_calls = []
# Decision: Route to END
```

**Step 7: Done!**
```
Agent: Your order #12345 was delivered on November 4th! 📦
```

---

## Common Issues and Solutions

### Issue 1: "Module not found"
**Problem**: Python can't find your modules
**Solution**: Run from the project root:
```bash
# From project root
python stage_1/demo.py
# NOT from inside stage_1/
```

### Issue 2: "ChromaDB permission error"
**Problem**: Can't write to database directory
**Solution**: Fix permissions:
```bash
chmod -R 755 common/data/chroma_db/
```

### Issue 3: Agent gives generic responses
**Problem**: Agent says "I'm glad I could help!" without actual info
**Solution**: Check the system prompt emphasizes including actual data

### Issue 4: Agent loops forever
**Problem**: Agent keeps calling tools repeatedly
**Solution**: Add max iterations check or improve prompt clarity

---

## What You've Accomplished

Congratulations! You've built a complete AI agent from scratch. You now understand:

✅ How to create tools with the `@tool` decorator
✅ How to structure agent state
✅ How the ReAct pattern works (Think → Act → Observe)
✅ How to build a workflow with LangGraph
✅ How semantic search works with embeddings
✅ How to test and debug agents

## Next Steps

Now that you have a working agent, try:

1. **Add a new tool**: Create a tool to check inventory
2. **Improve the prompt**: Make the agent more helpful
3. **Add more FAQs**: Expand the knowledge base
4. **Add logging**: Track what the agent is doing
5. **Try different models**: Test with different AI models

## Key Takeaways

**Tools are simple functions:**
```python
@tool
def my_tool(input: str) -> str:
    """What the tool does."""
    return "result"
```

**State is a dictionary:**
```python
state = {
    "messages": [...],
    "iterations": 0
}
```

**Agent is a class with call_model:**
```python
class Agent:
    def call_model(self, state):
        # Think and decide
        return updated_state
```

**Workflow connects everything:**
```python
graph.add_node("agent", agent.call_model)
graph.add_node("tools", ToolNode(tools))
graph.add_edge("tools", "agent")
```

🏆 Congratulations on building your first AI agent 🏆