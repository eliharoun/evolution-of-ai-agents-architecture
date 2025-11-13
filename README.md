# Evolution of AI Agent Architecture

A hands-on learning repository that teaches you how to build AI agents from the ground up. You'll start with a simple agent and progressively build more sophisticated systems, understanding exactly why and when each pattern is useful.

## What This Is

This isn't just another AI tutorial with code snippets. It's a complete learning path where you build real, working agents that solve actual problems. Each stage builds on the previous one, showing you not just how to implement patterns, but when and why to use them.

Think of it as a guided journey from "Hello World" to production-ready multi-agent systems.

## Who This Is For

- **Beginners** who want to understand AI agents from first principles
- **Software engineers** looking to add AI agent development to their skillset
- **AI practitioners** who want to understand different architectural patterns
- **Anyone** curious about how AI agents actually work under the hood

No prior AI experience needed. If you know Python basics, you can follow along.

## The Learning Path

### Stage 1: Foundation - Simple ReAct Agent
Build your first agent that can look up orders and answer customer questions. Learn the fundamental ReAct pattern (Reasoning and Acting) that underlies all agent systems.

**What you'll learn:** Tool creation, state management, LangGraph basics, semantic search with vector databases

[Read the README](stage_1/README.md) | [Follow the Tutorial](stage_1/BUILD_TUTORIAL.md)

### Stage 2: When One Agent Has Too Many Choices
Take the same agent architecture and give it more tools (7 instead of 2). Watch it struggle with complexity and understand why more capabilities don't automatically mean better performance.

**What you'll learn:** Single-agent limitations, struggle detection, when simple patterns break down

[Read the README](stage_2/README.md) | [Follow the Tutorial](stage_2/BUILD_TUTORIAL.md)

### Stage 3: ReWOO - Planning Before Acting
Solve Stage 2's problems with a smarter approach. Instead of thinking and acting one step at a time, learn to plan all steps upfront and execute efficiently.

**What you'll learn:** Upfront planning, variable substitution, dramatically reducing LLM calls

[Read the README](stage_3/README.md) | [Follow the Tutorial](stage_3/BUILD_TUTORIAL.md)

### Stage 4 Supervisor 1: Multi-Agent Teams (Quick Setup)
Move from one agent to a team of specialists. Build a supervisor that coordinates three focused agents, each expert in their domain. Use LangGraph's built-in functions for quick implementation.

**What you'll learn:** Specialization, parallel execution, rapid multi-agent setup

[Read the README](stage_4/supervisor_1/README.md) | [Follow the Tutorial](stage_4/supervisor_1/BUILD_TUTORIAL.md)

### Stage 4 Supervisor 2: Understanding Coordination (Custom Implementation)
Build the same multi-agent system from scratch to see exactly how the supervisor pattern works. Understand what the built-in functions hide.

**What you'll learn:** Agent composition, custom coordination logic, when to build vs buy

[Read the README](stage_4/supervisor_2/README.md) | [Follow the Tutorial](stage_4/supervisor_2/BUILD_TUTORIAL.md)

## Getting Started

### Prerequisites
- Python 3.9 or higher
- Basic Python knowledge (functions, classes, dictionaries)
- Either an OpenAI API key OR Ollama installed locally

### Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd evolution-of-ai-agents-arch

# Install dependencies
pip install -r requirements.txt

# Set up configuration
cp .env.example .env
# Edit .env with your settings
```

### Choose Your Path

**Quick Demo (Recommended First):**
```bash
python stage_1/demo.py
```
Runs the Stage 1 agent with example scenarios in your terminal.

**Web Interface:**
```bash
# Terminal 1: Start the backend
uvicorn backend.api:app --reload

# Terminal 2: Serve the frontend
cd frontend && python3 -m http.server 8080

# Open http://localhost:8080 in your browser
```

For detailed frontend setup, see [Frontend Quick Start Guide](frontend/QUICKSTART.md).

## Repository Structure

```
evolution-of-ai-agents-arch/
├── stage_1/              # Simple ReAct agent (2 tools)
├── stage_2/              # Same agent with 7 tools (shows struggles)
├── stage_3/              # ReWOO pattern (plans first)
├── stage_4/
│   ├── supervisor_1/     # Multi-agent with built-in coordination
│   └── supervisor_2/     # Multi-agent with custom coordination
├── common/               # Shared tools, data, and utilities
├── frontend/             # Web interface for all stages
└── backend/              # Unified FastAPI backend
```

Each stage has:
- `README.md` - Explains what the stage does and why
- `BUILD_TUTORIAL.md` - Step-by-step guide to building it yourself
- `demo.py` - Quick demonstration script

## What Makes This Different

**Progressive Complexity:** Start simple, add complexity only when needed. Each stage solves real problems from the previous stage.

**Build It Yourself:** Not just reading about patterns - you'll implement them. The tutorials guide you through every line of code.

**Understand the Why:** Learn when to use each pattern, not just how. See the problems each pattern solves through concrete examples.

**Production-Ready Code:** Not toy examples. The code includes proper error handling, logging, type hints, and follows best practices.

**Compare Patterns:** Run the same query through different stages and see the differences. Understand trade-offs through experience.

## Configuration

The system supports multiple AI providers through a simple configuration:

```bash
# .env file
MODEL_TYPE=openai        # openai, anthropic, or ollama
DEFAULT_MODEL=gpt-4o-mini
STAGE=1                  # Which stage to run (1, 2, 3.1, 4.1, 4.2)
```

Switch between providers without changing any code.

## What You'll Build

By the end of this tutorial series, you'll understand:

- How to build agents from scratch
- When different patterns are appropriate
- How to handle complex multi-step requests
- How to coordinate multiple specialized agents
- How to deploy agents to production
- How to evaluate and monitor agent performance

More importantly, you'll understand the **why** behind architectural decisions, not just the how.

## Contributing

Found a bug? Have a suggestion? Contributions are welcome! This is a learning resource for the community.

## License

MIT License - Use this for learning, teaching, or building your own projects.

## Acknowledgments

Built with LangGraph and LangChain. Inspired by research papers on ReAct, ReWOO, and multi-agent systems.

---

Ready to build your first AI agent? Start with [Stage 1](stage_1/README.md) or jump straight to the [tutorial](stage_1/BUILD_TUTORIAL.md).
