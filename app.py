# app.py
import streamlit as st
import asyncio
import os
import uuid
from dotenv import load_dotenv
from src.core.agent_manager import AgentManager

# Import your tools
from src.tools.implementations.timestamp import TimestampTool
from src.tools.implementations.news import NewsTool
from src.tools.implementations.email import GmailTool

# Load environment variables
load_dotenv()

# Set your API key
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")


# Function to run async code
def run_async(coro):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    try:
        result = loop.run_until_complete(coro)

        # Clean up any pending tasks
        pending = asyncio.all_tasks(loop)
        if pending:
            # Give tasks 2 seconds to complete
            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))

        return result
    except Exception as e:
        print(f"Error in async execution: {e}")
        raise e


# Set up the Streamlit page
st.title("AI Agent Chat")
st.subheader("Ask me anything!")

# Initialize session ID for this user
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# Initialize chat history in session state if it doesn't exist
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history (without duplicates)
displayed_messages = []
for message in st.session_state.messages:
    # Create a unique identifier for the message to detect duplicates
    message_id = f"{message['role']}_{message.get('content', '')[:50]}"

    # Only display if we haven't shown this message yet
    if message_id not in displayed_messages:
        displayed_messages.append(message_id)

        # Display the message
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

            # If this is an assistant message with tool info, show the tool
            if message["role"] == "assistant" and "tool_used" in message:
                with st.expander(f"Tool used: {message['tool_used']}"):
                    st.markdown(f"```\n{message['tool_result']}\n```")

            # If this is an assistant message with router info, show the router decision
            if message["role"] == "assistant" and "router_decision" in message:
                with st.expander(f"Query Router Decision"):
                    st.markdown(
                        f"**Decision:** {message['router_decision']['use_tool']}"
                    )
                    if message["router_decision"]["tool_name"]:
                        st.markdown(
                            f"**Tool:** {message['router_decision']['tool_name']}"
                        )
                    st.markdown(
                        f"**Reasoning:** {message['router_decision']['reasoning']}"
                    )

# Sidebar with controls
with st.sidebar:
    st.header("Settings")

    # Model selection
    model = st.selectbox(
        "Select Model", ["gpt-4o-mini", "gpt-4o", "claude-3-haiku-20240307"]
    )

    # Clear conversation button
    if st.button("Clear Conversation"):
        st.session_state.messages = []
        AgentManager.clear_agent(st.session_state.session_id)
        st.rerun()

# Input for new message
prompt = st.chat_input("What would you like to know?")

if prompt:
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)

    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Get agent with custom system message
    custom_message = """You are a helpful AI assistant with access to various tools. {tools}
    
    Use the appropriate tool when needed to provide accurate and up-to-date information.
    """

    agent = AgentManager.get_agent(
        st.session_state.session_id, model=model, custom_system_message=custom_message
    )

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # Store counts before processing to detect new additions
                tool_count_before = len(agent.memory.tool_results)
                router_count_before = len(agent.memory.router_decisions)

                response = run_async(agent.run(prompt))

                # Check if any new tool results were added during this request
                tool_was_used = len(agent.memory.tool_results) > tool_count_before
                router_decision_made = (
                    len(agent.memory.router_decisions) > router_count_before
                )

                assistant_message = {"role": "assistant", "content": response}

                # Add router decision info if a new decision was made
                if router_decision_made:
                    recent_router = agent.memory.router_decisions[-1]
                    assistant_message["router_decision"] = {
                        "use_tool": recent_router["use_tool"],
                        "tool_name": recent_router["tool_name"],
                        "reasoning": recent_router["reasoning"],
                    }

                    # Show router decision in the UI
                    with st.expander("Query Router Decision"):
                        st.markdown(f"**Decision:** {recent_router['use_tool']}")
                        if recent_router["tool_name"]:
                            st.markdown(f"**Tool:** {recent_router['tool_name']}")
                        st.markdown(f"**Reasoning:** {recent_router['reasoning']}")

                # Add tool usage info if a tool was used
                if tool_was_used:
                    # Get only the most recent tool result that was just added
                    recent_tool = agent.memory.tool_results[-1]

                    # Add tool metadata to the message for display purposes
                    assistant_message["tool_used"] = recent_tool["tool"]
                    assistant_message["tool_result"] = recent_tool["result"]

                    # Show tool usage in the UI
                    with st.expander(f"Tool used: {recent_tool['tool']}"):
                        st.markdown(f"```\n{recent_tool['result']}\n```")

                st.markdown(response)

                # Add assistant response to chat history
                st.session_state.messages.append(assistant_message)

                # Save agent state
                AgentManager.save_agent(st.session_state.session_id)
            except Exception as e:
                st.error(f"Error: {str(e)}")
                st.session_state.messages.append(
                    {"role": "assistant", "content": f"Error: {str(e)}"}
                )
