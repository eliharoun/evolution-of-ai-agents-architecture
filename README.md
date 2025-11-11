<div align="center">

# 🤖 Evolution of AI Agents Architecture

**A comprehensive hands-on tutorial series showcasing the evolution from simple to sophisticated AI agent design patterns**

[![Python](https://img.shields.io/badge/Python-3.9+-blue?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Framework-green?style=for-the-badge)](https://python.langchain.com/docs/langgraph)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

</div>

## 🎯 What You'll Learn

Transform from a simple chatbot to production-ready multi-agent systems through **5 progressive stages**:

| Stage | Focus | Architecture | Features |
|-------|-------|--------------|--------------|
| **🏗️ Stage 1** | **ReAct Foundation** | Single Agent | 2 tools, streaming, RAG, AI assistant style UI |
| **🔧 Stage 2** | **Sophisticated Single** | Enhanced Agent | 7 tools, struggle detection, stateful ops |
| **🧠 Stage 3** | **Advanced Patterns** | Smart Agent | ReWOO, Reflection, Plan-and-Execute |
| **👥 Stage 4** | **Multi-Agent** | Agent Teams | Supervisor, Pipeline, Collaborative |
| **📊 Stage 5** | **Production Analysis** | Optimized System | Performance comparison, pattern selection |

## ✨ Features

### 🎬 **Simple Demo UI**
- **Chatting interface** - Chat with the agent to test different scenarios
- **Live thought process visualization** - Watch your agent think, act, and observe in real-time

### 🛠️ **Production-Ready Architecture**
- **Model Factory Pattern** - Switch between AI providers with zero code changes
- **Shared Resources** - Reusable components across stages
- **Configuration-Driven** - Environment-based model selection and behavior
- **Standard Logging** - Logging throughout the code

### 🧰 **Advanced RAG Implementation**
- **ChromaDB Integration** - Persistent vector storage for semantic search
- **Text Chunking** - Optimal document preprocessing for retrieval
- **Semantic Search** - Find relevant FAQs using sentence transformers

### 🔒 **Enterprise Features**
- **Guardrails** - Scope-limited responses with polite redirects
- **Error Handling** - Graceful fallbacks and recovery
- **Type Safety** - Full type hints and validation
- **API Documentation** - Auto-generated OpenAPI specs

## 🚀 Quick Start

```bash
# 1. Clone and setup
git clone <your-repo-url>
cd evolution-of-ai-agents-arch
pip install -r requirements.txt

# 2. Configure (choose one)
cp stage_1/.env.example .env
# Option A: Use local models (free)
echo "MODEL_TYPE=ollama" >> .env

# Option B: Use OpenAI
echo "MODEL_TYPE=openai" >> .env
echo "OPENAI_API_KEY=your-key-here" >> .env

# 3. Run instantly
python stage_1/demo.py
```

**🎉 That's it! Your AI agent is running with streaming responses!**

## 🎭 Example Interactions

<details>
<summary><b>📦 Order Status Check</b></summary>

```
👤 Customer: "What's the status of my order #12345?"

🤖 Agent: 
💭 Thought: User asking about order status, need to use get_order_status tool
🔧 Action: Using tool: get_order_status
🔍 Observation: Order #12345 Details: Status: Delivered, Items: 2...
💬 Response: Your order #12345 has been delivered! Here are the details...
```
</details>

<details>
<summary><b>❓ FAQ Query with RAG</b></summary>

```
👤 Customer: "How do I return an item?"

🤖 Agent:
💭 Thought: User asking about return policy, need to search FAQ
🔧 Action: Using tool: search_faq  
🔍 Observation: ChromaDB found relevant FAQs about returns...
💬 Response: Here are the most relevant FAQs:
   1. **Returns**: How do I return an item?
   To return an item: 1) Log into your account...
```
</details>

<details>
<summary><b>🛡️ Guardrails in Action</b></summary>

```
👤 Customer: "What's the weather today?"

🤖 Agent: I'm a customer support agent for our clothing store and can only help 
with order-related questions, shipping, returns, payments, and account issues. 
For other questions, please use a general-purpose assistant.
```
</details>

## 🎯 Tutorial Stages

### 🏗️ **Stage 1: Foundation**
> **Simple ReAct Agent** - Learn the fundamentals

**What you'll build:**
- Customer support agent with ReAct pattern
- Order lookup tool + FAQ retrieval with semantic search  
- Streaming web interface with thought process visualization
- Model factory supporting OpenAI, Anthropic, and Ollama

**Concepts:**
- `Thought → Action → Observation` loop
- LangGraph workflows with built-in utilities
- RAG implementation with ChromaDB
- Production-ready FastAPI backend

[📖 Stage 1 Documentation](stage_1/README.md)

---

### 🔧 **Stage 2: Sophisticated Single Agent**
> **Tool Complexity & Limitations** - Discover when single agents break



**Demonstrated struggles:**
- Missing information causing agent confusion
- Multi-step dependency chains (4-5 sequential tools)
- Complex conditional logic (if/then/else)
- Tool confusion and redundant calls

[📖 Stage 2 Documentation](stage_2/README.md)

---

### 🧠 **Stage 3: Advanced Single Agent Patterns** *Coming Soon*
> **Smart Architecture Patterns** - Solve complexity with intelligence

**What you'll build:**
- **ReWOO** - Plan all tools upfront, then execute
- **Reflection** - Self-evaluation and learning from mistakes  
- **Plan-and-Execute** - Dynamic planning with adaptation

**Concepts:**
- Advanced reasoning patterns
- Self-improvement mechanisms
- Adaptive planning strategies

---

### 👥 **Stage 4: Multi-Agent Architecture** *Coming Soon*
> **Agent Specialization** - Divide and conquer with agent teams

**What you'll build:**
- **Supervisor Pattern** - Central coordination with specialists
- **Pipeline Pattern** - Sequential processing chain
- **Collaborative Pattern** - Peer-to-peer agent negotiation

**Concepts:**
- Agent communication protocols
- Task decomposition strategies
- Coordination mechanisms

---

### 📊 **Stage 5: Performance & Pattern Analysis** *Coming Soon*
> **Production Optimization** - Choose the right pattern for the job

## 🏃‍♂️ Running the Web Interface

1. **Start the unified backend:**
   ```bash
   # Stage 1 (default - 2 tools)
   uvicorn common.backend.api:app --reload
   
   # Or Stage 2 (7 tools + struggles)
   STAGE=2 uvicorn common.backend.api:app --reload
   ```

2. **Open the frontend:**
   ```bash
   open frontend/index.html
   ```

3. **Try these queries:**
   - `"What's the status of order #12345?"`
   - `"How do I return an item?"`
   - `"Do you offer free shipping?"`

**✨ Watch the magic:**
- Real-time responses
- Click "🧠 Agent Thought Process" to see reasoning

## 🔧 Configuration Options

### 🏠 **Local Models (Free)**
```bash
MODEL_TYPE=ollama
OLLAMA_MODEL=llama3.1
```

### ☁️ **Cloud Models (Paid)**
```bash
# OpenAI
MODEL_TYPE=openai
OPENAI_API_KEY=sk-your-key

# Anthropic Claude  
MODEL_TYPE=anthropic
ANTHROPIC_API_KEY=sk-ant-your-key
```

**💡 Pro tip:** Start with Ollama for free experimentation!

## 🎓 Learning Path

This repo teaches you to build **production-ready AI agents** through hands-on coding:

### **📚 What You'll Learn**
- **LangGraph fundamentals** - State management, nodes, edges, conditional routing
- **ReAct pattern mastery** - Thought → Action → Observation loops
- **RAG implementation** - Vector databases, embeddings, semantic search
- **Multi-agent coordination** - Communication, task delegation, collaboration
- **Production deployment** - FastAPI, streaming, monitoring, optimization

### **🏭 Production-Focused**
- **Enterprise-grade code** - Type hints, logging, error handling, documentation
- **Scalable architecture** - Shared resources, modular design, configuration-driven
- **Multiple deployment options** - Local development → Cloud production (coming soon)

### **🎨 Modern Stack**
- **LangGraph** - Latest graph-based agent framework
- **FastAPI** - High-performance async web framework
- **ChromaDB** - Production vector database
- **Multiple LLM Support** - OpenAI, Anthropic, Ollama

## 📄 License

MIT License - Feel free to use this for learning, research, or commercial projects!

## ⭐ Support This Project

If this tutorial helped you, please:
- **⭐ Star this repository** on GitHub
- **🔗 Share it** with your network
- **👥 Follow me** for updates on new stages

---

<div align="center">

[🚀 **Start with Stage 1**](stage_1/) | [📖 **Read the Docs**](stage_1/README.md) | [💻 **See the Code**](stage_1/agents/)

</div>
