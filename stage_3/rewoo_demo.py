"""
Demonstration script for Stage 3: ReWOO Pattern.

Shows how ReWOO (Reasoning Without Observation) improves upon Stage 2's limitations:
- Plans all tool calls upfront before execution
- Batches operations efficiently
- Reduces redundant LLM calls (2 LLM calls vs N+1 in ReAct)
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from stage_3.agents.rewoo import ReWOOWorkflow
from common.logging_config import setup_logging
from common.config import config

# Setup logging
setup_logging(log_level="INFO")


def print_separator(char="=", length=80):
    """Print a separator line."""
    print("\n" + char * length)


def print_scenario(number: int, description: str):
    """Print scenario header."""
    print_separator("=")
    print(f"  SCENARIO {number}: {description}")
    print_separator("=")


def print_user_message(message: str):
    """Print user message."""
    print(f"\n👤 Customer: {message}")


def print_agent_response(response: str):
    """Print agent response."""
    print(f"\n🤖 ReWOO Agent: {response}")


def print_plan(plan: str):
    """Print the generated plan."""
    print(f"\n📋 Generated Plan:")
    print("-" * 80)
    print(plan)
    print("-" * 80)


def main():
    """Run ReWOO pattern demonstration scenarios."""
    print_separator("=")
    print("  STAGE 3 DEMO: ReWOO Pattern - Reasoning Without Observation")
    print("  " + "-" * 76)
    print("  Shows how ReWOO improves upon Stage 2 by planning all tool calls upfront")
    print_separator("=")
    
    print(f"\n🔧 Initializing ReWOO Agent...")
    print(f"   Using model type: {config.MODEL_TYPE}")
    
    try:
        workflow = ReWOOWorkflow()
        print(f"✅ ReWOO Agent ready!")
        print(f"   Pattern: Reasoning Without Observation")
        print(f"   Components: Planner → Worker → Solver")
        print(f"   LLM Calls: Only 2 (vs N+1 in ReAct)\n")
    except Exception as e:
        print(f"❌ Failed to initialize agent: {str(e)}")
        print("\nMake sure you have:")
        print("  1. Created a .env file with your model provider API key")
        print("  2. Installed dependencies: pip install -r requirements.txt")
        return
    
    # Scenario 1: Simple order status check (should work efficiently)
    print_scenario(
        1,
        "Simple Order Status - Efficient Execution"
    )
    message = "What's the status of my order #12345?"
    print_user_message(message)
    print("\n⚙️  Processing with ReWOO pattern...")
    
    try:
        result = workflow.invoke(message)
        
        # Print the plan
        if "plan_string" in result:
            print_plan(result["plan_string"])
        
        # Print final response
        if "result" in result:
            print_agent_response(result["result"])
        
        # Show efficiency metrics
        steps = len(result.get("steps", []))
        print(f"\n📊 Efficiency Metrics:")
        print(f"   Steps planned: {steps}")
        print(f"   LLM calls: 2 (Planner + Solver)")
        print(f"   Tool executions: {steps}")
        print(f"   Total operations: {steps + 2}")
        print(f"\n💡 Note: ReAct would require {steps + 1} LLM calls for comparison")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
    
    input("\nPress Enter to continue to the complex scenario...")
    
    # Scenario 2: The complex birthday gift scenario from Stage 2
    print_scenario(
        2,
        "Complex Multi-Step Query - ReWOO Advantage"
    )
    message = """My order #12345 hasn't arrived, it was supposed to be a birthday gift for tomorrow. \
Can you check where it is, and if it won't arrive on time, I want to either expedite shipping or \
get a refund and buy locally. Also, do you have the same item in blue instead of red for future reference?"""
    
    print_user_message(message)
    print("\n⚙️  Processing with ReWOO pattern...")
    print("   Key Advantage: All tool calls planned upfront, then executed in sequence")
    
    try:
        # Use streaming to show step-by-step execution
        for step in workflow.stream(message):
            node_name = list(step.keys())[0]
            print(f"\n🔄 Step: {node_name}")
            
            if node_name == "plan":
                # Show the complete plan
                plan_string = step[node_name].get("plan_string", "")
                if plan_string:
                    print_plan(plan_string)
            
            elif node_name == "tool":
                # Show tool execution
                results = step[node_name].get("results", {})
                if results:
                    latest_key = list(results.keys())[-1]
                    print(f"   Executed: {latest_key}")
                    print(f"   Result preview: {results[latest_key][:100]}...")
            
            elif node_name == "solve":
                # Show final answer
                print_agent_response(step[node_name].get("result", ""))
        
        print("\n" + "=" * 80)
        print("  COMPARISON: ReWOO vs Stage 2 (ReAct)")
        print("  " + "-" * 76)
        print("  ReWOO:")
        print("    ✓ Plans all tool calls upfront")
        print("    ✓ Executes tools sequentially with variable substitution")
        print("    ✓ Only 2 LLM calls (Planner + Solver)")
        print("    ✓ No redundant planning between tool calls")
        print()
        print("  Stage 2 (ReAct):")
        print("    ✗ Plans one step at a time")
        print("    ✗ LLM call after each tool execution")
        print("    ✗ N+1 LLM calls (reason → act → observe loop)")
        print("    ✗ Higher token usage")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
    
    # Summary
    print_separator("=")
    print("  STAGE 3 DEMO COMPLETE!")
    print("  " + "-" * 76)
    print("  ReWOO Pattern Demonstrated:")
    print("    🧠 Planner: Creates complete plan with placeholders")
    print("    🔧 Worker: Executes tools with variable substitution")
    print("    🧠 Solver: Integrates all evidence into final answer")
    print()
    print("  Key Benefits:")
    print("    ✓ More efficient token usage (2 LLM calls vs N+1)")
    print("    ✓ Better handling of complex multi-step queries")
    print("    ✓ Clearer execution flow")
    print("    ✓ Reduced tool confusion")
    print("=" * 80)
    print("\n🚀 Next Steps:")
    print("   - Compare with Stage 2 performance")
    print("   - Explore Reflection pattern (coming soon)")
    print("   - Explore Plan-and-Execute pattern (coming soon)\n")


if __name__ == "__main__":
    main()
