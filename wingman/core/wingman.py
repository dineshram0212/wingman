import datetime

import tiktoken
from langchain.prompts import  PromptTemplate
from langchain_core.prompts.chat import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, END, MessagesState, StateGraph
from langchain_core.chat_history import InMemoryChatMessageHistory
from langgraph.prebuilt import ToolNode

from wingman.core.prompts import CLASSIFY_PROMPT, MODEL_PROMPT
from wingman.core.model_loader import ModelLoader
from wingman.utils.formatter import Classifier
from wingman.plugins.email_tool import send_email
from wingman.plugins.file_ops import read_file, write_file, find_all_user_files

from wingman.core.memory import Memory, save_recall_memory



class Wingman():
    def __init__(self, model_name, apiKey):
        self.memory = Memory()
        self.tokenizer = tiktoken.encoding_for_model("gpt-4o")
        self.chats_by_thread_id = {}
        self.tools = [save_recall_memory, send_email, read_file, write_file, find_all_user_files]
        self.tool_node = ToolNode(self.tools)
        self.model_name = model_name
        self.apiKey = apiKey
        self.graph = self.load_graph_memory()
    
    def get_chat_history(self, thread_id: str):
        chat_history = self.chats_by_thread_id.get(thread_id)
        if chat_history is None:
            chat_history = InMemoryChatMessageHistory()
            self.chats_by_thread_id[thread_id] = chat_history
        return chat_history

    def classify_and_load_memory(self, state: MessagesState):
        chat = state['messages'][-1].content
        print("Query to be searched:\n", chat)
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
        
        model = ModelLoader(model=self.model_name, apiKey=self.apiKey).load_model()
        llm = model.with_structured_output(Classifier)
        chain = prompt | llm
        result = chain.invoke(chat)
        mtype = result.mtype.strip()
        if mtype == 'none':
            return []
        else:
            convo_str = self.tokenizer.decode(self.tokenizer.encode(chat))
            recall_memories = self.memory.search_recall_memories(convo_str, config = {"configurable": {"mtype": mtype}})
            return recall_memories

    def should_continue(self, state: MessagesState):
        messages = state["messages"]
        last_message = messages[-1]
        if hasattr(last_message, "name") and last_message.name:
            print("Tool response received, getting final response from model")
            return "call_model_after_tool"
        if isinstance(last_message, AIMessage) and hasattr(last_message, "tool_calls") and last_message.tool_calls:
            print("Routing to tool nodes")
            return "tools"
        elif last_message.content.strip():
            print("Ending workflow")
            return END

        print("Ending workflow")
        return END
    
    def call_model_after_tool(self, state: MessagesState, config: RunnableConfig):
        """A simplified model call function that only generates a response after tool execution."""
        if "configurable" not in config or "thread_id" not in config["configurable"]:
            raise ValueError(
                f"Make sure that the config includes the following information: {'configurable': {'thread_id': 'some_value'}}"
            )
        
        chat_template = ChatPromptTemplate.from_messages(
            [
                SystemMessage(
                    content=(
                        "You have just completed a tool operation. Now provide a final response to the user "
                        "summarizing what was done. DO NOT use any more tools. Just respond directly to the user."
                    )   
                ),  
                HumanMessagePromptTemplate(prompt=PromptTemplate(input_variables=["messages"],template="{messages}"))
            ]
        )

        llm = ModelLoader(model=self.model_name, apiKey=self.apiKey).load_model()
        chain = chat_template | llm
        chat_history = self.get_chat_history(config["configurable"]["thread_id"])
        recent_messages = state["messages"][-3:] 
        response = chain.invoke(recent_messages)
        
        human_message = state["messages"][0].content
        ai_message = response.content
        
        if ai_message != '':
            chat_history.add_messages([HumanMessage(content=human_message), AIMessage(content=ai_message)])
        
        return {"messages": [response]}

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
                        f"Consider the suitable information from the given context loaded from memory: {','.join(from_memory)}\n\n. Don't consider tool calling based on the above memory."
                        "DO NOT SAVE QUESTIONS TO MEMORY. Consider only the latest query of the user and remaining as memory."
                        f"{MODEL_PROMPT}"
                    )   
                ),  
                HumanMessagePromptTemplate(prompt=PromptTemplate(input_variables=["messages"],template="{messages}"))
            ]
        )

        model = ModelLoader(model=self.model_name, apiKey=self.apiKey).load_model()
        llm = model.bind_tools(self.tools)

        chain = chat_template | llm
        chat_history = self.get_chat_history(config["configurable"]["thread_id"])
        
        messages = list(chat_history.messages) + list(state["messages"]) if chat_history else state["messages"]
        response = chain.invoke(messages)
        human_message = state["messages"][-1].content
        ai_message = response.content
        if ai_message != '':
            chat_history.add_messages([HumanMessage(content=human_message), AIMessage(content=ai_message)])
        return {"messages": [response]}

    def load_graph_memory(self):
        builder = StateGraph(MessagesState)

        builder.add_node("call_model", self.call_model)
        builder.add_node("call_model_after_tool", self.call_model_after_tool)
        builder.add_node("tools", self.tool_node)

        builder.add_edge(START, "call_model")
        builder.add_conditional_edges("call_model", self.should_continue, ["call_model", "call_model_after_tool", "tools", END])
        builder.add_edge("tools", "call_model_after_tool")

        memory = MemorySaver()
        graph = builder.compile(checkpointer=memory)
        return graph
    
    def chat(self, state: MessagesState, config):
        output = self.graph.invoke(state, config)
        return output["messages"][-1].content 
