import os
from dotenv import load_dotenv
import datetime
import streamlit as st
from langgraph.graph import MessagesState
from langchain_core.messages import HumanMessage

from wingman.core.wingman import Wingman

load_dotenv()

st.title("Wingman")


client = Wingman(
    model_name='qwen-2.5-32b', 
    apiKey=os.getenv('API_KEY')
    )

config = {
    "configurable": {
        "thread_id": datetime.datetime.now().strftime('%d%m%Y'),
    }
}


# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("What is up?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

        response = client.chat(MessagesState(messages=[
            HumanMessage(content=msg["content"]) for msg in st.session_state.messages
        ]), config=config)

    with st.chat_message("assistant"):
        response_text = st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})
