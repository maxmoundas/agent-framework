# tool_test.py
import streamlit as st
import asyncio
import os
from dotenv import load_dotenv
from src.core.agent import Agent

# Import your tools
from src.tools.implementations.timestamp import TimestampTool
from src.tools.implementations.news import NewsTool

# Load environment variables
load_dotenv()

# Set your API key
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")


# Function to run async code
def run_async(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# Initialize agent
@st.cache_resource
def get_agent():
    custom_message = """You are a helpful AI assistant with access to various tools. {tools}
    
    When asked about time, date, or news, use the appropriate tool to provide up-to-date information.
    For general questions, respond conversationally without using tools.
    """
    return Agent(model="gpt-4o-mini", custom_system_message=custom_message)


st.title("Tool Testing Interface")

# Create columns
col1, col2 = st.columns(2)

with col1:
    st.subheader("Time Tool Test")
    time_query = st.text_input("Ask about time/date", "What time is it now?")
    if st.button("Test Time Tool"):
        with st.spinner("Processing..."):
            agent = get_agent()
            response = run_async(agent.run(time_query))
            st.write("Response:")
            st.write(response)

with col2:
    st.subheader("News Tool Test")
    news_query = st.text_input("Ask about news", "What's in the news today?")
    if st.button("Test News Tool"):
        with st.spinner("Processing..."):
            agent = get_agent()
            response = run_async(agent.run(news_query))
            st.write("Response:")
            st.write(response)

# Debug information
with st.expander("Debug Info"):
    agent = get_agent()

    st.subheader("Available Tools")
    tool_specs = run_async(asyncio.coroutine(lambda: agent._get_tools_info())())
    st.json(tool_specs)

    st.subheader("Router Test")
    test_query = st.text_input("Test query for router", "What time is it?")
    if st.button("Test Router"):
        use_tool, suggested_tool = run_async(agent.router.should_use_tools(test_query))
        st.write(f"Should use tools: {use_tool}")
        st.write(f"Suggested tool: {suggested_tool}")
