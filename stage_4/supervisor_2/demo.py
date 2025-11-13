"""
Interactive demo for Stage 4 Supervisor v2 implementation.

This demo shows the CUSTOM supervisor pattern with full transparency into
how specialists are wrapped as tools and how delegation works.

Educational focus: Understanding the mechanics of supervisor coordination.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from stage_4.supervisor_2.agents.workflow import CustomSupervisorWorkflow
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
            print(f"\n🎯 Supervisor: {content[:200]}{'...' if len(content) > 200 else ''}")
            
            # Show tool calls (specialist consultations)
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                print(f"\n   🔧 Consulting Specialists:")
                for tc in msg.tool_calls:
                    specialist_name = tc['name'].replace('specialist_', '').replace('_', ' ').title()
                    print(f"      • {specialist_name}")
                    if 'request' in tc.get('args', {}):
                        print(f"        Request: {tc['args']['request'][:80]}...")
        elif role == "ToolMessage":
            tool_name = getattr(msg, "name", "unknown")
            specialist_name = tool_name.replace('specialist_', '').replace('_', ' ').title()
            print(f"\n   ↳ 📋 {specialist_name} Response:")
            print(f"      {content[:150]}{'...' if len(content) > 150 else ''}")
    
    print("\n" + "-" * 80)


def run_demo():
    """Run interactive demo scenarios."""
    print("=" * 80)
    print("Stage 4 Supervisor 2: Custom Implementation - Educational Deep Dive")
    print("=" * 80)
    print("\n🎓 Learning Focus: Understanding supervisor mechanics")
    print("\nThis implementation shows:")
    print("  • How specialists are wrapped as tools")
    print("  • How supervisor delegates using standard ReAct pattern")
    print("  • Full transparency in coordination logic")
    print_separator()
    
    # Initialize workflow
    print("🔧 Initializing Custom Supervisor Workflow...")
    workflow = CustomSupervisorWorkflow(
        model_type=cast(ModelType, config.DEFAULT_MODEL_TYPE),
        enable_checkpointing=config.ENABLE_CHECKPOINTING
    )
    print(f"✓ Workflow ready with model: {config.DEFAULT_MODEL_TYPE}")
    print(f"✓ Checkpointing: {'Enabled' if config.ENABLE_CHECKPOINTING else 'Disabled'}")
    print(f"✓ Supervisor has {len(workflow.specialist_tools)} specialist tools")
    
    # Demo scenarios
    scenarios = [
        {
            "name": "Simple Order Status",
            "query": "What's the status of my order #12345?",
            "learning": "Watch: Supervisor calls specialist_order_operations tool (which wraps the Order Operations agent)"
        },
        {
            "name": "Complex Birthday Gift Scenario",
            "query": "My order #12345 hasn't arrived, it was supposed to be a birthday gift for tomorrow. Can you check where it is, and if it won't arrive on time, I want to either expedite shipping or get a refund and buy locally. Also, do you have the same item in blue instead of red for future reference?",
            "learning": "Watch: Supervisor consults multiple specialists (order_operations AND product_inventory)"
        },
        {
            "name": "Multi-Domain Query",
            "query": "I want to check my order #12345 status, also what's your return policy, and can you look up my account history?",
            "learning": "Watch: Supervisor consults all 3 specialists for comprehensive information"
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print_separator()
        print(f"📋 Scenario {i}: {scenario['name']}")
        print(f"🎓 Learning: {scenario['learning']}")
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
            
            # Educational notes
            print("\n🎓 What Happened:")
            tool_calls = sum(1 for m in result['messages'] if hasattr(m, 'tool_calls') and m.tool_calls)
            tool_results = sum(1 for m in result['messages'] if m.__class__.__name__ == 'ToolMessage')
            print(f"   • Supervisor made {tool_calls} specialist consultation(s)")
            print(f"   • Received {tool_results} specialist response(s)")
            print(f"   • Each specialist is a full ReAct agent wrapped as a tool!")
            
        except Exception as e:
            logger.error(f"Scenario {i} failed: {str(e)}")
            print(f"\n❌ Error: {str(e)}")
        
        if i < len(scenarios):
            input("\n⏸️  Press Enter to continue to next scenario...")
    
    print_separator()
    print("✅ Demo completed!")
    print("\n🎓 Key Educational Insights:")
    print("  • Specialists are wrapped as tools using @tool decorator")
    print("  • Supervisor is just a ReAct agent with high-level tools")
    print("  • Tool calls to specialists → specialists run their own ReAct loops")
    print("  • Results flow back through tool messages")
    print("  • Supervisor aggregates and synthesizes final response")
    print("\n💡 Compare with Supervisor 1 to see the difference!")
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
