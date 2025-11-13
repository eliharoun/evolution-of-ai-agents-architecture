# Building Stage 3: The ReWOO Pattern

Welcome to Stage 3! In this tutorial, you'll learn a completely different approach to building agents. Instead of thinking and acting one step at a time, you'll build an agent that plans everything upfront, then executes efficiently.

## What You'll Learn

- How the ReWOO pattern differs from ReAct
- How to build a Planner that creates complete plans
- How to build a Worker that executes without thinking
- How to build a Solver that synthesizes results
- How variable substitution enables dependencies
- Why this approach is more efficient

## Prerequisites

Before starting, you should have:
- Completed Stage 1 and Stage 2 tutorials
- Understanding of ReAct pattern limitations
- Familiarity with LangGraph basics
- The 7 tools from Stage 2 available

## Tutorial Overview

We'll build ReWOO in 5 steps:
1. Understand the ReWOO mental model
2. Create the ReWOO state
3. Build the three agent components (Planner, Worker, Solver)
4. Create the workflow
5. Test with complex scenarios

The key insight: **Plan first, execute second, synthesize third.**

Let's begin!

---

## Step 1: Understanding ReWOO

Before writing code, let's understand why ReWOO exists and how it works.

### The Problem with ReAct

In Stages 1 and 2, the agent followed this pattern:
```
1. User asks question
2. Agent thinks: "What should I do?"     [LLM Call]
3. Agent acts: Uses a tool
4. Agent observes result
5. Agent thinks: "What next?"            [LLM Call]
6. Agent acts: Uses another tool
7. Agent observes result
8. Agent thinks: "Done?"                 [LLM Call]
9. Agent responds
```

**Problems:**
- Many LLM calls (expensive, slow)
- Thinks after each tool (can get confused)
- No overall plan (reactive, not strategic)

### The ReWOO Solution

ReWOO separates thinking from doing:
```
1. User asks question
2. Planner thinks: "Here's my complete plan"  [LLM Call 1]
   Creates: Step 1, Step 2, Step 3, Step 4...
3. Worker: Execute Step 1 (no thinking)
4. Worker: Execute Step 2 (no thinking)
5. Worker: Execute Step 3 (no thinking)
6. Worker: Execute Step 4 (no thinking)
7. Solver: "Here's the answer"               [LLM Call 2]
```

**Benefits:**
- Only 2 LLM calls (regardless of complexity!)
- Complete plan before execution (strategic)
- No confusion between steps (just follow plan)

### The Magic: Placeholders

ReWOO uses placeholders like #E1, #E2, #E3 to reference results:

```
Plan: Check order status
#E1 = OrderStatus[12345]

Plan: Check if the item in #E1 is available in blue
#E2 = CheckInventory[item from #E1, blue]
```

When executing Step 2:
- Worker sees "#E1" in the parameters
- Replaces #E1 with actual result from Step 1
- Calls tool with complete information

This is how steps can depend on previous steps without replanning!

---

## Step 2: Create the ReWOO State

The state is more sophisticated than Stages 1 and 2 because we need to track a plan.

Create `stage_3/agents/rewoo/state.py`:

```python
"""State for ReWOO workflow."""

from typing import List
from common.base_state import BaseAgentState


class ReWOOState(BaseAgentState):
    """
    State for ReWOO agent.
    
    Unlike Stage 1/2 which just track messages and iterations,
    ReWOO needs to track an execution plan and results.
    """
    task: str           # Original user question
    plan_string: str    # The complete plan as text
    steps: List         # Parsed steps: [(desc, #E, tool, params), ...]
    results: dict       # Tool results: {"#E1": result, "#E2": result, ...}
    result: str         # Final answer
```

**Understanding the fields:**

1. **task**: The original user question
   - Example: "Check order #12345 and find it in blue"

2. **plan_string**: The raw plan from the planner
   - Example: 
     ```
     Plan: Check order status #E1 = OrderStatus[12345]
     Plan: Find blue variant #E2 = CheckInventory[item from #E1, blue]
     ```

3. **steps**: Parsed into structured format
   - Example: `[("Check order", "#E1", "OrderStatus", "12345"), ...]`

4. **results**: Stores tool execution results
   - Example: `{"#E1": "Order details...", "#E2": "Blue available"}`

5. **result**: The final synthesized answer
   - Example: "Your order was delivered. We have it in blue!"

**Why this structure?**
- Need to track the plan (not just messages)
- Need to store intermediate results for substitution
- Need structured steps for the worker to execute

---

## Step 3: Build the Three Agent Components

ReWOO has three distinct components. Let's build each one.

### Component 1: The Planner

The planner's job: Create a complete plan before doing anything.

Create `stage_3/agents/rewoo/rewoo_agent.py` and start with the planner:

```python
"""ReWOO Agent with Planner, Worker, and Solver."""

import re
from typing import Dict
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from stage_3.agents.rewoo.state import ReWOOState
from common.tools import STAGE_2_TOOLS  # Same 7 tools


class ReWOOAgent:
    """
    ReWOO agent with three components:
    1. Planner: Creates complete plan
    2. Worker: Executes tools
    3. Solver: Synthesizes answer
    """
    
    # Regex to parse plan format
    REGEX_PATTERN = r"Plan:\s*(.+)\s*(#E\d+)\s*=\s*(\w+)\s*\[([^\]]+)\]"
    
    def __init__(self, model_name: str = "gpt-4o-mini"):
        """Initialize with planner and solver models."""
        # Create models
        self.planner_model = ChatOpenAI(model=model_name, temperature=0)
        self.solver_model = ChatOpenAI(model=model_name, temperature=0)
        
        # Set up tools
        self.tools = {
            'OrderStatus': get_order_status,
            'SearchFAQ': search_faq,
            'CustomerAccount': get_customer_account,
            'ProcessRefund': process_refund,
            'ModifyShipping': modify_shipping,
            'CheckInventory': check_inventory,
            'CreateTicket': create_ticket,
        }
    
    def get_plan(self, state: ReWOOState) -> Dict:
        """
        PLANNER: Create complete plan with placeholders.
        
        This is the first LLM call in ReWOO.
        """
        task = state["task"]
        
        # Create planner prompt (we'll define this next)
        planner_prompt = ChatPromptTemplate.from_messages([
            ("user", PLANNER_PROMPT)
        ])
        
        # Create planner chain
        planner = planner_prompt | self.planner_model
        
        # Get the plan
        result = planner.invoke({"task": task})
        
        # Parse the plan using regex
        # Extracts: (description, #E1, ToolName, parameters)
        matches = re.findall(self.REGEX_PATTERN, result.content)
        
        print(f"\n📋 PLAN CREATED:")
        for desc, var, tool, params in matches:
            print(f"  {var} = {tool}[{params}]")
        
        return {
            "steps": matches,
            "plan_string": result.content
        }
```

**What's happening:**
1. Takes the user's task
2. Creates a prompt asking for a complete plan
3. Calls the planner model (first LLM call)
4. Parses the output to extract structured steps
5. Stores both the raw plan and parsed steps

**The regex pattern:**
- Looks for: `Plan: description #E1 = ToolName[params]`
- Extracts all four parts
- Creates list of tuples

### Component 2: The Worker

The worker's job: Execute tools in order without thinking.

Add to the same file:

```python
    def _get_current_task(self, state: ReWOOState) -> Optional[int]:
        """
        Determine which step to execute next.
        
        Returns:
            Step number (1-indexed) or None if all done
        """
        if "results" not in state or state["results"] is None:
            return 1  # Start with step 1
        
        completed = len(state["results"])
        total = len(state["steps"])
        
        if completed == total:
            return None  # All done
        else:
            return completed + 1  # Next step
    
    def tool_execution(self, state: ReWOOState) -> Dict:
        """
        WORKER: Execute one tool with variable substitution.
        
        No LLM calls here - just execute the plan.
        """
        # Figure out which step to execute
        step_num = self._get_current_task(state)
        
        if step_num is None:
            return {}  # All steps complete
        
        # Get step details
        desc, step_name, tool, tool_input = state["steps"][step_num - 1]
        
        # Get previous results
        results = state.get("results", {}) or {}
        
        # Variable substitution - this is the magic!
        # Replace #E1, #E2, etc. with actual results
        for var, value in results.items():
            tool_input = tool_input.replace(var, value)
        
        print(f"\n🔧 EXECUTING: {step_name} = {tool}[{tool_input}]")
        
        # Execute the tool
        if tool == "LLM":
            # Special case: LLM reasoning step
            result = self.planner_model.invoke(tool_input)
            result_str = result.content
        elif tool in self.tools:
            # Execute actual tool
            result = invoke_tool_with_params(
                self.tools[tool], 
                tool_input
            )
            result_str = str(result)
        else:
            raise ValueError(f"Unknown tool: {tool}")
        
        # Store result
        results[step_name] = result_str
        
        print(f"  ✓ Result: {result_str[:100]}...")
        
        return {"results": results}
```

**What's happening:**
1. Determines which step to execute (1, 2, 3, ...)
2. Gets step details from parsed plan
3. Replaces #E variables with actual results
4. Executes the tool
5. Stores result for next step to use

**The key:** No LLM calls! Just mechanical execution.

### Component 3: The Solver

The solver's job: Combine all evidence into a natural answer.

Add to the same file:

```python
    def solve(self, state: ReWOOState) -> Dict:
        """
        SOLVER: Integrate all evidence into final answer.
        
        This is the second (and final) LLM call in ReWOO.
        """
        # Reconstruct plan with actual results
        plan = ""
        for desc, step_name, tool, tool_input in state["steps"]:
            results = state.get("results", {})
            
            # Show substituted values
            for var, value in results.items():
                tool_input = tool_input.replace(var, value)
            
            plan += f"Plan: {desc}\n{step_name} = {tool}[{tool_input}]\n"
        
        # Add all evidence
        plan += "\nEvidence:\n"
        for step_name, result in state.get("results", {}).items():
            plan += f"{step_name} = {result}\n"
        
        print(f"\n💬 SOLVING with {len(state.get('results', {}))} pieces of evidence")
        
        # Create solver prompt (we'll define this next)
        prompt = SOLVER_PROMPT.format(
            plan=plan,
            task=state["task"]
        )
        
        # Call solver model (second LLM call)
        result = self.solver_model.invoke(prompt)
        
        return {"result": result.content}
```

**What's happening:**
1. Gathers the complete plan
2. Gathers all evidence (tool results)
3. Creates a prompt with everything
4. Calls the solver model (second LLM call)
5. Returns the final answer

**The key:** Solver sees EVERYTHING. All steps, all results, full context.

---

## Step 4: Create the Prompts

ReWOO needs two specialized prompts: one for planning, one for solving.

Create `stage_3/agents/rewoo/utils/rewoo_prompts.py`:

```python
"""Prompts for ReWOO pattern."""

# Planner Prompt - teaches model how to create plans
PLANNER_PROMPT = """For the following task, make plans that can solve the problem step by step. 
For each plan, indicate which external tool together with tool input to retrieve evidence. 
You can store the evidence into a variable #E that can be called by later tools.

Available tools:
(1) OrderStatus[order_id]: Check order status
(2) SearchFAQ[query]: Search FAQ knowledge base
(3) CustomerAccount[order_id]: Get customer account info
(4) ProcessRefund[order_id, reason]: Initiate refund
(5) ModifyShipping[order_id, modification_type, details]: Modify shipping
(6) CheckInventory[product_name, color, size]: Check product availability
(7) CreateTicket[issue_description, customer_email, priority]: Create support ticket
(8) LLM[input]: Use when you need reasoning or general knowledge

IMPORTANT: Follow this exact format:
Plan: <description> #E<number> = <ToolName>[<parameters>]

Example:
Task: My order #12345 is late, I want refund or expedite, do you have it in blue?

Plan: Check order status #E1 = OrderStatus[12345]
Plan: Analyze if delayed #E2 = LLM[Is #E1 delayed?]
Plan: Check expedite options #E3 = ModifyShipping[12345, expedite]
Plan: Check refund eligibility #E4 = ProcessRefund[12345, delayed order]
Plan: Find blue variant #E5 = CheckInventory[item from #E1, blue]

Begin! Create a plan for:
Task: {task}"""


# Solver Prompt - teaches model how to synthesize
SOLVER_PROMPT = """You are a friendly customer service agent. Based on the investigation below, 
provide a brief, conversational response.

{plan}

IMPORTANT - Keep it conversational:
- SHORT responses (2-4 sentences max)
- NO email formatting
- NO bullet points
- Write naturally as if chatting
- Get straight to the point

Task: {task}
Response:"""
```

**Understanding the prompts:**

**Planner:**
- Lists all available tools
- Shows the format with #E placeholders
- Provides an example
- Teaches the model the pattern

**Solver:**
- Emphasizes conversational tone
- Asks for brevity
- Gets the full context (plan + evidence)

---

## Step 5: Create the Tool Invocation Helper

The planner outputs parameters as strings. Tools need typed parameters. We need a bridge.

Create `stage_3/agents/rewoo/utils/tool_invocation.py`:

```python
"""Helper for invoking tools with string parameters."""

import inspect
from typing import Any, Callable


def invoke_tool_with_params(tool: Callable, params_str: str) -> Any:
    """
    Invoke a tool with parameters parsed from a string.
    
    The planner outputs: "12345, expedite"
    The tool needs: modify_shipping(order_id="12345", modification_type="expedite")
    
    This function bridges the gap.
    
    Args:
        tool: The tool function to call
        params_str: Parameters as a string
        
    Returns:
        Tool execution result
    """
    # Get tool's parameter names using introspection
    sig = inspect.signature(tool.func)  # .func for @tool decorated
    param_names = list(sig.parameters.keys())
    
    # Parse the parameter string
    # Simple parsing: split by comma
    param_values = [p.strip() for p in params_str.split(',')]
    
    # Create parameter dictionary
    params = {}
    for i, param_name in enumerate(param_names):
        if i < len(param_values):
            params[param_name] = param_values[i]
    
    # Call the tool
    return tool.invoke(params)
```

**What this does:**
1. Uses Python introspection to find parameter names
2. Splits the string by commas
3. Maps values to parameter names
4. Calls the tool with proper parameters

**Example:**
```python
tool = modify_shipping
params_str = "12345, expedite"

# Inspects modify_shipping:
#   Parameters: order_id, modification_type, details
# Parses: ["12345", "expedite"]
# Calls: modify_shipping(order_id="12345", modification_type="expedite", details="")
```

---

## Step 6: Build the Workflow

Now we connect everything with a workflow.

Create `stage_3/agents/rewoo/workflow.py`:

```python
"""ReWOO Workflow - orchestrates Plan → Execute → Solve."""

from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage

from stage_3.agents.rewoo.state import ReWOOState
from stage_3.agents.rewoo.rewoo_agent import ReWOOAgent


class ReWOOWorkflow:
    """
    ReWOO workflow with three stages:
    - Plan: Create complete plan
    - Tool: Execute tools (loops)
    - Solve: Synthesize final answer
    """
    
    def __init__(self):
        """Initialize the workflow."""
        self.agent = ReWOOAgent()
        self.workflow = self._build_graph()
    
    def _build_graph(self):
        """
        Build the workflow graph.
        
        Structure:
        START → plan → tool → [more tools?] → solve → END
                         ↑         |
                         └─────────┘ (loop)
        """
        # Create state graph
        graph = StateGraph(ReWOOState)
        
        # Add the three nodes
        graph.add_node("plan", self.agent.get_plan)
        graph.add_node("tool", self.agent.tool_execution)
        graph.add_node("solve", self.agent.solve)
        
        # Define the flow
        graph.add_edge(START, "plan")      # Start with planning
        graph.add_edge("plan", "tool")     # Plan → first tool
        graph.add_edge("solve", END)       # Solve → done
        
        # Conditional edge: more tools OR solve?
        graph.add_conditional_edges(
            "tool",
            self._route,
            {
                "tool": "tool",    # Loop back for next tool
                "solve": "solve"   # All done, go to solver
            }
        )
        
        return graph.compile()
    
    def _route(self, state: ReWOOState) -> str:
        """
        Decide: Execute more tools OR move to solver?
        
        Returns:
            "tool" if more steps to do, "solve" if complete
        """
        # Check how many steps are done
        completed = len(state.get("results", {}))
        total = len(state.get("steps", []))
        
        if completed < total:
            return "tool"  # More tools to execute
        else:
            return "solve"  # All done, synthesize
    
    def run(self, user_input: str) -> str:
        """Run the workflow."""
        print(f"\n{'='*60}")
        print(f"User: {user_input}")
        print(f"{'='*60}")
        
        # Create initial state
        initial_state = {
            "task": user_input,
            "messages": [HumanMessage(content=user_input)],
            "iterations": 0,
            "results": {}
        }
        
        # Execute workflow
        result = self.workflow.invoke(initial_state)
        
        # Extract final answer
        final_answer = result["result"]
        
        print(f"\n💬 Agent: {final_answer}")
        print(f"{'='*60}\n")
        
        return final_answer
```

**Understanding the workflow:**

1. **Three nodes**: plan, tool, solve
2. **Linear flow**: START → plan → tool
3. **Loop**: tool can go back to itself
4. **Conditional**: _route decides when to stop looping
5. **End**: solve → END

**The routing logic:**
```python
if (steps_completed < total_steps):
    return "tool"   # Keep executing
else:
    return "solve"  # Time to synthesize
```

Simple but effective!

---

## Step 7: Test Your ReWOO Agent

Create `stage_3/rewoo_demo.py`:

```python
"""Demo showing ReWOO handling complex scenarios."""

from stage_3.agents.rewoo.workflow import ReWOOWorkflow


def main():
    """Run demo scenarios."""
    print("\n" + "="*60)
    print("STAGE 3: ReWOO PATTERN")
    print("="*60)
    
    workflow = ReWOOWorkflow()
    
    # Simple scenario
    print("\n--- SIMPLE SCENARIO ---")
    workflow.run("What's the status of order #12345?")
    
    input("Press Enter for complex scenario...")
    
    # Complex scenario (broke Stage 2)
    print("\n--- COMPLEX SCENARIO ---")
    workflow.run(
        "My order #12345 hasn't arrived, I want expedited shipping "
        "or a refund, and do you have it in blue?"
    )
    
    print("\nNotice:")
    print("- Complete plan created upfront")
    print("- All tools executed in order")
    print("- Only 2 LLM calls total")
    print("- No struggles!")


if __name__ == "__main__":
    main()
```

**Run it:**
```bash
python stage_3/rewoo_demo.py
```

**What you'll see:**
1. The complete plan printed out
2. Each tool execution with results
3. The final synthesized answer
4. Count of LLM calls (should be exactly 2)

---

## Step 8: Understanding Execution Flow

Let's trace through a complete example.

### Example Query
"Check order #12345. If delayed, expedite it. Also check if you have it in blue."

### Execution Trace

**Phase 1: Planner (LLM Call #1)**
```
Input: User query

Planner thinks:
"I need to:
1. Check order status
2. Determine if delayed
3. Prepare expedite option
4. Find blue variant"

Output:
Plan: Check order status #E1 = OrderStatus[12345]
Plan: Check if delayed #E2 = LLM[Is #E1 delayed?]
Plan: Expedite if needed #E3 = ModifyShipping[12345, expedite]
Plan: Find blue variant #E4 = CheckInventory[item from #E1, blue]
```

**Phase 2: Worker (No LLM Calls)**
```
Step 1:
- Execute: OrderStatus[12345]
- Store: #E1 = "Order #12345, Shipped, Est delivery Nov 15"

Step 2:
- Input: "Is #E1 delayed?"
- Substitute: "Is Order #12345, Shipped, Est delivery Nov 15 delayed?"
- Execute: LLM reasoning
- Store: #E2 = "Delivery is on schedule for Nov 15"

Step 3:
- Execute: ModifyShipping[12345, expedite]
- Store: #E3 = "Upgraded to overnight, arrives tomorrow"

Step 4:
- Input: "item from #E1, blue"
- Substitute: "Blue variant of items from Order #12345"
- Execute: CheckInventory[parsed items, blue]
- Store: #E4 = "Blue variant available, 5 in stock"
```

**Phase 3: Solver (LLM Call #2)**
```
Input:
Plan: [complete plan with descriptions]
Evidence:
  #E1 = Order details
  #E2 = Not delayed
  #E3 = Upgraded to overnight
  #E4 = Blue available

Solver synthesizes:
"Your order #12345 is on track for Nov 15, but I've upgraded 
it to overnight shipping for faster delivery! We also have the 
blue variant in stock if you'd like to order that."

Output: Natural, conversational answer
```

**Total LLM calls: 2**

---

## Comparing with Stage 2

Let's run the same complex query through both patterns:

### Stage 2 (ReAct) Execution
```
User: "Order #12345 is late, refund or expedite, have it in blue?"

Iteration 1: Think → OrderStatus[12345]              [LLM Call 1]
Iteration 2: Observe → Think → ModifyShipping[...]   [LLM Call 2]
Iteration 3: Observe → Think → ProcessRefund[...]    [LLM Call 3]
Iteration 4: Observe → Think → CheckInventory[...]   [LLM Call 4]
Iteration 5: Observe → Think → "Wait, what did I already do?" [LLM Call 5]
Iteration 6: Observe → Respond                       [LLM Call 6]

Total: 6 LLM calls, 6 iterations
Struggles: High iterations, tool confusion likely
```

### Stage 3 (ReWOO) Execution
```
User: "Order #12345 is late, refund or expedite, have it in blue?"

Planner: Create complete 4-step plan                 [LLM Call 1]
Worker: Execute step 1 (no LLM)
Worker: Execute step 2 (no LLM)
Worker: Execute step 3 (no LLM)
Worker: Execute step 4 (no LLM)
Solver: Synthesize complete answer                   [LLM Call 2]

Total: 2 LLM calls, 1 pass
Struggles: None
```

The difference is dramatic!

---

## Advanced Concepts

### The LLM Tool

Notice in the prompts there's an "LLM" tool:

```
Plan: Analyze if order is delayed #E2 = LLM[Is #E1 delayed?]
```

**What is this?**
- A tool that calls the LLM for reasoning
- Used when you need judgment, not just data lookup
- Example uses:
  - "Is this order delayed based on #E1?"
  - "What's the best option given #E1 and #E2?"
  - "Summarize the key points from #E1"

**Why it's useful:**
- Some steps need reasoning, not just tool execution
- Allows hybrid plans: data gathering + reasoning
- More flexible than pure tool execution

### Variable Substitution in Detail

The worker replaces variables in a simple way:

```python
tool_input = "item from #E1, blue"
results = {"#E1": "Blue Jeans, Size 32"}

# String replacement
tool_input = tool_input.replace("#E1", "Blue Jeans, Size 32")
# Result: "item from Blue Jeans, Size 32, blue"
```

**Limitations:**
- Simple string replacement (no parsing)
- Works for simple cases
- Complex substitutions need smarter parsing

**For production:**
- Consider more sophisticated variable extraction
- Handle nested references
- Parse structured data better

---

## Common Issues

### Issue 1: Plan format not parsed correctly
**Problem**: Regex doesn't match plan output
**Solution**: Ensure planner follows exact format: `Plan: desc #E1 = Tool[params]`

### Issue 2: Variable substitution fails
**Problem**: #E1 not replaced in tool input
**Solution**: Check that variable names match exactly (#E1 vs #e1 vs E1)

### Issue 3: Too many/few LLM calls
**Problem**: Not exactly 2 LLM calls
**Solution**: Check if LLM tool is being used (counts as planner call in worker)

### Issue 4: Tools not found
**Problem**: "Unknown tool" error
**Solution**: Verify tool names in planner match self.tools dictionary keys

---

## What You've Accomplished

You've built ReWOO and learned:

✅ How to separate planning from execution
✅ How to use placeholders for dependencies
✅ How to build a multi-phase agent (Planner/Worker/Solver)
✅ How to drastically reduce LLM calls
✅ Why planning solves the problems from Stage 2

## Key Takeaways

**ReWOO in a nutshell:**
```python
# Phase 1: Plan (LLM Call 1)
plan = planner.create_plan(task)

# Phase 2: Execute (No LLM Calls)
for step in plan:
    result = execute_tool(step)
    store_result(result)

# Phase 3: Solve (LLM Call 2)
answer = solver.synthesize(plan, results)
```

**When to use ReWOO:**
- Complex multi-step requests
- Efficiency is important
- All info available upfront
- Single-turn responses

**When NOT to use ReWOO:**
- Need to adapt plan mid-execution
- Interactive conversations
- Uncertain requirements
- Need parallel execution

## Next Steps

Now that you understand ReWOO, explore:

1. **Optimize the planner prompt**: Better examples, clearer instructions
2. **Improve tool invocation**: Handle more parameter types
3. **Add error handling**: What if a tool fails mid-execution?
4. **Compare patterns**: Run same queries through Stage 2 and Stage 3

**Future patterns to learn:**
- Reflection: Self-evaluation and improvement
- Plan-and-Execute: Adaptive replanning
- Multi-agent: Multiple specialized agents working together

The lesson: **Different patterns for different problems. Choose wisely!**
