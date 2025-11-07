"""
Demonstration script for Stage 1: Simple ReAct Agent.
Shows the agent handling various customer support scenarios.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from stage_1.agents.workflow import AgentWorkflow
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


def run_demo_scenario(workflow: AgentWorkflow, scenario_num: int, description: str, message: str):
    """
    Run a single demo scenario.
    
    Args:
        workflow: AgentWorkflow instance
        scenario_num: Scenario number
        description: Scenario description
        message: Customer message
    """
    print_scenario(scenario_num, description)
    print_user_message(message)
    
    print("\n⚙️  Processing...")
    
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
        
        # Show some stats
        print(f"\n📊 Stats: {result.get('iterations', 0)} iterations, {len(messages)} messages")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
    
    input("\nPress Enter to continue...")


def main():
    """Run all demo scenarios."""
    print("\n" + "="*80)
    print("  STAGE 1 DEMO: Simple ReAct Agent for Customer Support")
    print("  " + "-"*76)
    print("  This demo showcases the agent handling various customer scenarios")
    print("="*80)
    
    print("\n🔧 Initializing agent...")
    print(f"   Using model type: {config.MODEL_TYPE}")
    
    try:
        # Uses MODEL_TYPE from config (set in .env)
        workflow = AgentWorkflow()
        print("✅ Agent ready!\n")
    except Exception as e:
        print(f"❌ Failed to initialize agent: {str(e)}")
        print("\nMake sure you have:")
        print("  1. Created a .env file with your model provider API key")
        print("  2. Installed dependencies: pip install -r requirements.txt")
        return
    
    # Scenario 1: Order Status Check
    run_demo_scenario(
        workflow,
        1,
        "Order Status Check (Tool: get_order_status)",
        "What's the status of my order #12345?"
    )
    
    # Scenario 2: FAQ Question - Returns
    run_demo_scenario(
        workflow,
        2,
        "FAQ Question - Returns (Tool: search_faq)",
        "How do I return an item I bought?"
    )
    
    # Scenario 3: FAQ Question - Shipping
    run_demo_scenario(
        workflow,
        3,
        "FAQ Question - Shipping (Tool: search_faq)",
        "Do you offer free shipping?"
    )
    
    # Scenario 4: Another Order Check
    run_demo_scenario(
        workflow,
        4,
        "Order Status Check - Shipped (Tool: get_order_status)",
        "Can you check order #12346 for me?"
    )
    
    # Scenario 5: Testing Guardrails
    run_demo_scenario(
        workflow,
        5,
        "Testing Guardrails - Out of Scope Question",
        "What's the weather like today?"
    )
    
    # Scenario 6: Complex Multi-part Question
    run_demo_scenario(
        workflow,
        6,
        "Multi-part Question (Multiple Tool Uses)",
        "I need to check order #12347 and also want to know about your return policy"
    )
    
    print_separator("=")
    print("  DEMO COMPLETE!")
    print("  " + "-"*76)
    print("  The agent successfully demonstrated:")
    print("    ✅ Order lookup tool usage")
    print("    ✅ FAQ retrieval with semantic search")
    print("    ✅ Guardrails for out-of-scope queries")
    print("    ✅ Multi-tool coordination")
    print("="*80)
    print("\n🚀 Try the interactive web UI:")
    print("   1. Start backend: uvicorn stage_1.backend.api:app --reload")
    print("   2. Open: frontend/index.html in your browser\n")


if __name__ == "__main__":
    main()
