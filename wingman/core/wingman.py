import datetime

import tiktoken
from langchain.prompts import  PromptTemplate
from langchain_core.prompts.chat import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, END, MessagesState, StateGraph
from langchain_core.chat_history import InMemoryChatMessageHistory

from wingman.core.prompts import CLASSIFY_PROMPT, MODEL_PROMPT
from wingman.core.model_loader import ModelLoader
from wingman.utils.formatter import Classifier, ResponseFormatter
from wingman.core.state import State

from wingman.core.memory import Memory



class Wingman():
    def __init__(self, model_name, apiKey):
        self.model = ModelLoader(model=model_name, apiKey=apiKey).load_model()
        self.memory = Memory()
        
        self.tokenizer = tiktoken.encoding_for_model("gpt-4o")
        self.chats_by_thread_id = {}
    


    def get_chat_history(self, thread_id: str):
        chat_history = self.chats_by_thread_id.get(thread_id)
        if chat_history is None:
            chat_history = InMemoryChatMessageHistory()
            self.chats_by_thread_id[thread_id] = chat_history
        return chat_history



    def classify_and_load_memory(self, state: MessagesState):
        chat = state['messages'][0].content
        prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessage(
                    content=(
                        f"""
                            Query: "{chat}"
                            {CLASSIFY_PROMPT}
                            """
                    )
                ),
                HumanMessagePromptTemplate(prompt=PromptTemplate(input_variables=["messages"],template="{messages}"))
            ]
        )

        llm = self.model.with_structured_output(Classifier)
        chain = prompt | llm
        result = chain.invoke(state)
        mtype = result.mtype.strip()
        if mtype == 'none':
            return []
        else:
            convo_str = self.tokenizer.decode(self.tokenizer.encode(chat))
            recall_memories = self.memory.search_recall_memories(convo_str, config = {"configurable": {"mtype": mtype}})
            return recall_memories



    def call_model(self, state: MessagesState, config: RunnableConfig):
        if "configurable" not in config or "thread_id" not in config["configurable"]:
            raise ValueError(
            f"Make sure that the config includes the following information: {'configurable': {'thread_id': 'some_value'}}"
        )
        from_memory = self.classify_and_load_memory(state=state)
        chat_template = ChatPromptTemplate.from_messages(
            [
                SystemMessage(
                    content=(
                        f"For reference, today's date and current time is {datetime.datetime.now().strftime('%d %B %Y,  %I:%M %p')}"
                        f"Consider the suitable information from the given context loaded from memory:\n {','.join(from_memory)}\n\n"
                        f"{MODEL_PROMPT}"
                    )
                ),  
                HumanMessagePromptTemplate(prompt=PromptTemplate(input_variables=["messages"],template="{messages}"))
            ]
        )
        llm = self.model.with_structured_output(ResponseFormatter)
        chain = chat_template | llm
        chat_history = self.get_chat_history(config["configurable"]["thread_id"])
        if chat_history is None:
            response = chain.invoke(state)
            chat = state["messages"][0].content
            mtype = response.mtype.strip()
            if mtype != 'none':
                self.memory.save_recall_memory(query=f"HumanMessage: {chat} ; AIMessage: {response.response}", config={"configurable": {"mtype": mtype}})
            chat_history.add_messages([HumanMessage(content=chat), AIMessage(content=response.response)]) 

            return response
        
        messages = list(chat_history.messages) + list(state["messages"])
        response = chain.invoke(messages)
        chat = state["messages"][0].content
        mtype = response.mtype.strip()
        chat_history.add_messages([HumanMessage(content=chat), AIMessage(content=response.response)])
        if mtype != 'none':
            self.memory.save_recall_memory(query=f"HumanMessage: {chat} ; AIMessage: {response.response}", config={"configurable": {"mtype": mtype}})
        return {"messages": [response.response]}



    def load_graph_memory(self):
        # Create the graph and add nodes
        builder = StateGraph(MessagesState)

        # Add edges to the graph
        builder.add_node(self.call_model)  # Register function as node
        builder.add_edge(START, "call_model")
        builder.add_edge("call_model", END)

        # Compile the graph
        memory = MemorySaver()
        graph = builder.compile(checkpointer=memory)
        return graph
    
    
    def chat(self, state: MessagesState, config):
        graph = self.load_graph_memory()
        output = graph.invoke(state, config)
        return output["messages"][-1].content 
