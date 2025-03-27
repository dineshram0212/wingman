import os
from dotenv import load_dotenv
import datetime
import streamlit as st
from langgraph.graph import MessagesState
from langchain_core.messages import HumanMessage

from wingman.core.wingman import Wingman
from wingman.core.wingmanOA import WingmanOpenAI

load_dotenv()

st.title("Wingman")

if "client" not in st.session_state:
    st.session_state.client = WingmanOpenAI(
        # model_name='mistral-saba-24b', 
        model_name='gemma2-9b-it', 
        # model_name='qwen-2.5-32b', 
        # model_name='llama-3.3-70b-versatile', 
        # model_name='llama3.2', 
        api_key=os.getenv('API_KEY')
        # api_key='ollama'
    )

client = st.session_state.client

config = {
    "configurable": {
        "thread_id": datetime.datetime.now().strftime('%d%m%Y'),
    }
}

thread_id = datetime.datetime.now().strftime('%d%m%Y')


# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("What is up?"):

    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

        # response = client.chat(MessagesState(messages=[
        #     HumanMessage(content=msg["content"]) for msg in st.session_state.messages
        # ]), config=config)
        response = client.run(user_input=prompt, thread_id=thread_id)

    with st.chat_message("assistant"):
        response_text = st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})
