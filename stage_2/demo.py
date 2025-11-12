"""
Demonstration script for Stage 2: Sophisticated Single Agent.
Shows how agents struggle when given too many tools and complex scenarios.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from stage_2.agents.workflow import AgentWorkflow
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
    print(f"\n🤖 Agent: {response}")


def print_struggle_analysis(stats: dict, iterations: int):
    """Print struggle analysis."""
    print(f"\n📊 Performance Analysis:")
    print(f"   Iterations: {iterations}")
    print(f"   High Iterations: {stats.get('high_iterations', 0)}")
    print(f"   Tool Confusion Events: {stats.get('tool_confusion_events', 0)}")
    print(f"   Context Loss Events: {stats.get('context_loss_events', 0)}")
    
    # Analysis
    total_struggles = sum(stats.values())
    if total_struggles > 0:
        print(f"\n⚠️  STRUGGLES DETECTED: {total_struggles} total struggle indicators")
        print("   This demonstrates single-agent limitations with complex tool sets")
    else:
        print(f"\n✅ Clean execution - no struggles detected")


def run_demo_scenario(workflow: AgentWorkflow, scenario_num: int, description: str, message: str, expect_struggles: bool = False):
    """
    Run a single demo scenario with struggle analysis.
    
    Args:
        workflow: AgentWorkflow instance
        scenario_num: Scenario number
        description: Scenario description
        message: Customer message
        expect_struggles: Whether this scenario should demonstrate struggles
    """
    print_scenario(scenario_num, description)
    print_user_message(message)
    
    if expect_struggles:
        print("\n🔍 Expected: This scenario should demonstrate agent struggles")
    
    print("\n⚙️  Processing...")
    
    # Reset struggle stats for clean measurement
    workflow.reset_struggle_stats()
    
    try:
        result = workflow.invoke(message)
        
        # Extract final response
        messages = result.get("messages", [])
        final_response = "No response generated"
        
        for msg in reversed(messages):
            if hasattr(msg, "type") and msg.type == "ai" and msg.content:
                final_response = msg.content
                break
        
        print_agent_response(final_response)
        
        # Analyze struggles
        struggle_stats = result.get("struggle_stats", {})
        print_struggle_analysis(struggle_stats, result.get('iterations', 0))
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
    
    input("\nPress Enter to continue...")


def main():
    """Run all demo scenarios showing progression from simple to complex."""
    print("\n" + "="*80)
    print("  STAGE 2 DEMO: Sophisticated Single Agent - Tool Complexity Issues")
    print("  " + "-"*76)
    print("  This demo shows how single agents struggle with complex tool sets")
    print("="*80)
    
    print(f"\n🔧 Initializing Stage 2 agent...")
    print(f"   Using model: {config.DEFAULT_MODEL_TYPE}:{config.DEFAULT_MODEL_NAME}")
    
    try:
        workflow = AgentWorkflow()
        print(f"✅ Stage 2 Agent ready!")
        print(f"   Tools available: {len(workflow.agent.tools)} (vs 2 in Stage 1)")
        print("   Struggle monitoring: ENABLED\n")
    except Exception as e:
        print(f"❌ Failed to initialize agent: {str(e)}")
        print("\nMake sure you have:")
        print("  1. Created a .env file with your model provider API key")
        print("  2. Installed dependencies: pip install -r requirements.txt")
        return
    
    print("📋 Demo Structure:")
    print("   • Scenarios 1-3: Simple queries (should work fine)")
    print("   • Scenarios 4-6: Complex queries (should show struggles)")
    print("   • Struggle indicators tracked and displayed")
    
    # Scenario 1: Simple Order Status (Should work fine)
    run_demo_scenario(
        workflow,
        1,
        "Simple Order Status Check (Should work smoothly)",
        "What's the status of my order #12345?",
        expect_struggles=False
    )
    
    # Scenario 2: Simple FAQ (Should work fine)
    run_demo_scenario(
        workflow,
        2,
        "Simple FAQ Question (Should work smoothly)",
        "How do I return an item?",
        expect_struggles=False
    )
    
    # Scenario 3: Customer Account Lookup (New tool, should work)
    run_demo_scenario(
        workflow,
        3,
        "Customer Account Lookup (New tool test)",
        "Can you tell me about my account history for order #12345?",
        expect_struggles=False
    )
    
    # Scenario 4: Multi-Step Dependency Chain - Needs Many Sequential Calls
    run_demo_scenario(
        workflow,
        4,
        "Multi-Step Dependency Chain (Forces sequential bottleneck)",
        "I want to reorder the t-shirt from my previous order, but first check if it's still available in my size and preferred colors. If not available, find similar items in the same price range that ARE in stock, then tell me the fastest shipping option for whichever item you recommend.",
        expect_struggles=True
    )
    
    # Scenario 5: Missing Critical Info - Agent Must Make Multiple Guesses
    run_demo_scenario(
        workflow,
        5,
        "Missing Critical Information (Agent flounders without order ID)",
        "I'm really frustrated! I ordered something weeks ago and it's still not here. This is unacceptable and I want a refund immediately! I've been a loyal customer and spent hundreds of dollars with you. Fix this now!",
        expect_struggles=True
    )
    
    # Scenario 6: Conditional Logic Nightmare - If/Then/Else Beyond Agent Capability
    run_demo_scenario(
        workflow,
        6,
        "Complex Conditional Logic (Agent can't plan conditionally)",
        "Check if order #12346 has shipped yet. If it hasn't, cancel it and refund me. But if it HAS shipped, then expedite it to overnight instead. Also, regardless of what happens with that order, I want to check if you have the same item in a different color for my next purchase. Also do you have any item similar to my previous order but in a different color?",
        expect_struggles=True
    )
    
    # Final summary
    print_separator("=")
    print("  STAGE 2 DEMO COMPLETE!")
    print("  " + "-"*76)
    print("  Single Agent Limitations Demonstrated:")
    print("    ⚠️  Tool selection confusion with 7 tools available")
    print("    ⚠️  Sequential bottlenecks instead of parallel processing")
    print("    ⚠️  Context loss in complex multi-step requests")
    print("    ⚠️  Difficulty planning multiple actions efficiently")
    print("\n  Solution Preview:")
    print("    🧠 Stage 3: Advanced patterns (ReWOO, Reflection, Plan-and-Execute)")
    print("    👥 Stage 4: Multi-agent architectures with specialization")
    print("="*80)
    print("\n🚀 Try the interactive web UI:")
    print("   1. Start backend: STAGE=2 uvicorn backend.api:app --reload")
    print("   2. Or: uvicorn backend.api:app --reload then POST /stage/2")
    print("   3. Open: frontend/index.html in your browser") 
    print("   4. Try the complex scenario to see struggles in real-time\n")


if __name__ == "__main__":
    main()
