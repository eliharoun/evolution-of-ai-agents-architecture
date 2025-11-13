"""
Interactive demo for Stage 4 Supervisor v1 implementation.

This demo shows the Supervisor pattern in action, coordinating specialist agents
to handle complex customer support queries efficiently.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from stage_4.supervisor_1.agents.workflow import SupervisorWorkflow
from common.logging_config import get_logger
from common.config import config
from common.model_factory import ModelType
from typing import cast

logger = get_logger(__name__)


def print_separator():
    """Print a visual separator."""
    print("\n" + "=" * 80 + "\n")


def display_messages(result: dict):
    """
    Display conversation messages in a readable format.
    
    Args:
        result: Workflow result containing messages
    """
    messages = result.get("messages", [])
    
    print("\n📝 Conversation Flow:")
    print("-" * 80)
    
    for i, msg in enumerate(messages, 1):
        role = msg.__class__.__name__
        content = msg.content if hasattr(msg, "content") else str(msg)
        
        # Format based on message type
        if role == "HumanMessage":
            print(f"\n👤 Customer: {content}")
        elif role == "AIMessage":
            # Check if this is from a specialist or supervisor
            name = getattr(msg, "name", None)
            if name:
                # Specialist response
                emoji = "📦" if "order" in name else "🛍️" if "product" in name else "👤"
                print(f"\n{emoji} {name.replace('_', ' ').title()}: {content}")
            else:
                # Supervisor response
                print(f"\n🎯 Supervisor: {content}")
            
            # Show tool calls if present
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                print(f"   └─ Tools called: {[tc['name'] for tc in msg.tool_calls]}")
        elif role == "ToolMessage":
            print(f"   └─ Tool result: {content[:100]}...")
    
    print("\n" + "-" * 80)


def run_demo():
    """Run interactive demo scenarios."""
    print("=" * 80)
    print("Stage 4: Supervisor Pattern - Multi-Agent Customer Support")
    print("=" * 80)
    print("\nDemonstrating intelligent delegation with specialized agents:")
    print("  📦 Order Operations: Tracking, shipping, refunds")
    print("  🛍️ Product & Inventory: Availability, FAQs")  
    print("  👤 Customer Account: Account info, escalations")
    print_separator()
    
    # Initialize workflow
    print("🔧 Initializing Supervisor Workflow...")
    workflow = SupervisorWorkflow(
        model_type=cast(ModelType, config.DEFAULT_MODEL_TYPE),
        enable_checkpointing=config.ENABLE_CHECKPOINTING
    )
    print(f"✓ Workflow ready with model: {config.DEFAULT_MODEL_TYPE}")
    print(f"✓ Checkpointing: {'Enabled' if config.ENABLE_CHECKPOINTING else 'Disabled'}")
    
    # Demo scenarios
    scenarios = [
        {
            "name": "Simple Order Status",
            "query": "What's the status of my order #12345?",
            "expected": "Order Operations agent handles solo"
        },
        {
            "name": "Complex Birthday Gift Scenario",
            "query": "My order #12345 hasn't arrived, it was supposed to be a birthday gift for tomorrow. Can you check where it is, and if it won't arrive on time, I want to either expedite shipping or get a refund and buy locally. Also, do you have the same item in blue instead of red for future reference?",
            "expected": "Supervisor delegates to Order Operations AND Product & Inventory (parallel)"
        },
        {
            "name": "Multi-Domain Query",
            "query": "I want to check my order #12345 status, also what's your return policy, and can you look up my account history?",
            "expected": "Supervisor delegates to all 3 specialists (parallel reads)"
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print_separator()
        print(f"📋 Scenario {i}: {scenario['name']}")
        print(f"Expected: {scenario['expected']}")
        print("-" * 80)
        print(f"\n💬 Customer Query:\n{scenario['query']}")
        print("\n🤖 Processing...")
        
        try:
            # Run workflow
            result = workflow.invoke(scenario['query'])
            
            # Display results
            display_messages(result)
            
            # Show final response
            final_message = result['messages'][-1]
            if hasattr(final_message, 'content'):
                print("\n✨ Final Response to Customer:")
                print("-" * 80)
                print(final_message.content)
                print("-" * 80)
            
            print(f"\n✓ Scenario {i} completed successfully")
            
        except Exception as e:
            logger.error(f"Scenario {i} failed: {str(e)}")
            print(f"\n❌ Error: {str(e)}")
        
        if i < len(scenarios):
            input("\n⏸️  Press Enter to continue to next scenario...")
    
    print_separator()
    print("✅ Demo completed!")
    print("\nKey Observations:")
    print("  • Supervisor intelligently delegates to specialists")
    print("  • Specialists use their focused tool sets efficiently")
    print("  • Parallel execution for independent tasks")
    print("  • Clear aggregation of specialist findings")
    print("\nCompare this with Stage 2's struggles with 7 tools!")
    print_separator()


if __name__ == "__main__":
    try:
        run_demo()
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted by user. Goodbye!")
    except Exception as e:
        logger.error(f"Demo failed: {str(e)}", exc_info=True)
        print(f"\n❌ Demo failed: {str(e)}")
        sys.exit(1)
