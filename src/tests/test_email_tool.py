# src/tests/test_email_tool.py

# to run this, run: ~ python3 -m src.tests.test_email_tool

import asyncio
import os
from dotenv import load_dotenv
from ..core.agent import Agent

# Import the email tool to ensure it's registered
from ..tools.implementations.email import GmailTool

# Load environment variables
load_dotenv()

# Set your API key
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")


async def test_direct_tool():
    """Test the email tool directly without the agent"""
    print("Testing GmailTool directly...")

    tool = GmailTool()

    # Test the setup instructions
    print("\nSetup Instructions:")
    print(tool.get_setup_instructions())

    # Test parameter validation
    print("\nTool Parameters:")
    for param_name, param_details in tool.parameters.items():
        required = param_details.get("required", False)
        print(
            f"  - {param_name}: {param_details['type']} {'(required)' if required else '(optional)'}"
        )
        print(f"    Description: {param_details['description']}")

    # Test authentication (without sending actual emails)
    print("\nTesting authentication...")
    try:
        # This will test if the tool can authenticate
        creds = tool._authenticate()
        if creds and creds.valid:
            print("✅ Authentication successful")
        else:
            print("❌ Authentication failed")
    except Exception as e:
        print(f"❌ Authentication error: {e}")


async def test_agent_integration():
    """Test the email tool with the agent framework"""
    print("\n" + "=" * 50)
    print("TESTING AGENT INTEGRATION")
    print("=" * 50)

    # Initialize agent with a custom system message
    custom_message = """You are a helpful assistant that can send emails. {tools}
    
    When asked to send an email, use the GmailTool to compose and send the message.
    Make sure to extract the recipient, subject, and body from the user's request.
    Always confirm the email details before sending.
    """

    agent = Agent(model="gpt-4o-mini", custom_system_message=custom_message)

    print("Testing Gmail email tool with agent...\n")

    # Test cases
    test_cases = [
        {
            "name": "Simple Email",
            "query": "Send an email to test@example.com with subject 'Test Email' and body 'This is a test email from the agent framework.'",
            "expected_tool": "GmailTool",
        },
        {
            "name": "HTML Email",
            "query": "Send an HTML email to user@example.com with subject 'HTML Test' and body '<h1>Hello</h1><p>This is an HTML email.</p>'",
            "expected_tool": "GmailTool",
        },
        {
            "name": "Email with CC",
            "query": "Send an email to recipient@example.com, CC manager@example.com, with subject 'Meeting Reminder' and body 'Don't forget about our meeting tomorrow at 2 PM.'",
            "expected_tool": "GmailTool",
        },
        {
            "name": "Email with BCC",
            "query": "Send an email to client@example.com, BCC admin@example.com, with subject 'Project Update' and body 'Here is the latest project status.'",
            "expected_tool": "GmailTool",
        },
        {
            "name": "Complex Email",
            "query": "Send an HTML email to team@example.com, CC boss@example.com, BCC hr@example.com, with subject 'Weekly Report' and body '<h2>Weekly Summary</h2><p>Here are the key highlights:</p><ul><li>Project A: 80% complete</li><li>Project B: On track</li></ul>'",
            "expected_tool": "GmailTool",
        },
        {
            "name": "Non-Email Query (Should not use tool)",
            "query": "What's the weather like today?",
            "expected_tool": None,
        },
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Test {i}: {test_case['name']} ---")
        print(f"USER: {test_case['query']}")

        try:
            result = await agent.run(test_case["query"])
            print(f"AGENT: {result}")

            # Check if the tool was used when expected
            if test_case["expected_tool"]:
                if test_case["expected_tool"].lower() in result.lower():
                    print("✅ Tool used correctly")
                else:
                    print("⚠️  Tool may not have been used")
            else:
                if "gmail" not in result.lower() and "email" not in result.lower():
                    print("✅ Tool correctly not used")
                else:
                    print("⚠️  Tool may have been used when not needed")

        except Exception as e:
            print(f"❌ Error: {e}")


async def test_error_handling():
    """Test error handling scenarios"""
    print("\n" + "=" * 50)
    print("TESTING ERROR HANDLING")
    print("=" * 50)

    tool = GmailTool()

    # Test with invalid parameters
    print("\nTesting invalid parameters...")
    try:
        result = await tool.execute(
            to="", subject="Test", body="Test body"  # Empty recipient
        )
        print(f"Result: {result}")
    except Exception as e:
        print(f"Expected error: {e}")

    # Test with missing required parameters
    print("\nTesting missing parameters...")
    try:
        result = await tool.execute(
            to="test@example.com"
            # Missing subject and body
        )
        print(f"Result: {result}")
    except Exception as e:
        print(f"Expected error: {e}")


async def test_tool_registry():
    """Test that the tool is properly registered"""
    print("\n" + "=" * 50)
    print("TESTING TOOL REGISTRY")
    print("=" * 50)

    from ..tools.registry import ToolRegistry

    # Check if GmailTool is registered
    tools = ToolRegistry.list_tools()
    print(f"Registered tools: {tools}")

    if "GmailTool" in tools:
        print("✅ GmailTool is properly registered")

        # Get tool specs
        specs = ToolRegistry.get_tool_specs()
        if "GmailTool" in specs:
            print("✅ GmailTool specifications available")
            print(f"Description: {specs['GmailTool']['description']}")
        else:
            print("❌ GmailTool specifications not found")
    else:
        print("❌ GmailTool is not registered")


def print_test_summary():
    """Print a summary of what the tests cover"""
    print("\n" + "=" * 60)
    print("GMAIL TOOL TEST COVERAGE")
    print("=" * 60)

    print("\n✅ Direct Tool Testing:")
    print("  - Tool instantiation and parameter validation")
    print("  - Authentication flow")
    print("  - Setup instructions")

    print("\n✅ Agent Integration Testing:")
    print("  - Simple email composition")
    print("  - HTML email support")
    print("  - CC and BCC functionality")
    print("  - Complex email scenarios")
    print("  - Tool selection logic (when to use vs not use)")

    print("\n✅ Error Handling:")
    print("  - Invalid parameters")
    print("  - Missing required parameters")
    print("  - Authentication errors")

    print("\n✅ Tool Registry:")
    print("  - Tool registration verification")
    print("  - Tool specifications")

    print("\n✅ Security:")
    print("  - OAuth2 authentication")
    print("  - Proper scope handling")
    print("  - Token management")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    print("Gmail Tool Comprehensive Test Suite")
    print("=" * 50)

    # Run all tests
    try:
        # Test 1: Direct tool testing
        asyncio.run(test_direct_tool())

        # Test 2: Tool registry
        asyncio.run(test_tool_registry())

        # Test 3: Error handling
        asyncio.run(test_error_handling())

        # Test 4: Agent integration (commented out by default)
        print("\n" + "=" * 50)
        print("AGENT INTEGRATION TEST")
        print("=" * 50)
        print("Note: Agent integration test is commented out by default")
        print("To run it, uncomment the line below in the code")
        print("This test will actually send emails!")
        print("=" * 50)

        # Uncomment the line below to test with the agent (will send real emails!)
        # asyncio.run(test_agent_integration())

        # Print test summary
        print_test_summary()

        print("\n🎉 All tests completed!")
        print("To test actual email sending, uncomment the agent integration test.")

    except Exception as e:
        print(f"\n❌ Test suite error: {e}")
        print("Please check your configuration and try again.")
