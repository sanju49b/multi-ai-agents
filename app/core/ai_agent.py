from langchain_groq import ChatGroq
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.prebuilt import create_react_agent
from langchain_core.messages.ai import AIMessage
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from app.config.settings import settings

def get_response_from_ai_agents(llm_id, query, allow_search, system_prompt):
    # Initialize the LLM
    llm = ChatGroq(model=llm_id)

    # Set up tools based on search preference
    tools = [TavilySearchResults(max_results=2)] if allow_search else []

    # Create the system prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt)
    ])

    # Create the agent with the correct parameters
    agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt=prompt  # Fixed: Using 'prompt' instead of 'state_modifier'
    )

    # Convert query strings to HumanMessage objects
    messages = [HumanMessage(content=msg) for msg in query]
    
    # Create state with properly formatted messages
    state = {"messages": messages}

    # Invoke the agent
    response = agent.invoke(state)

    # Extract messages from response
    response_messages = response.get("messages", [])

    # Filter AI messages and get their content
    ai_messages = [message.content for message in response_messages if isinstance(message, AIMessage)]

    # Return the last AI message, or a default if no AI messages found
    return ai_messages[-1] if ai_messages else "No response generated"