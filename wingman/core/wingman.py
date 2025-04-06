import datetime
import tiktoken
import re

from llama_index.core.agent.workflow import ReActAgent
from llama_index.core.tools import FunctionTool
from llama_index.core.llms import ChatMessage
from llama_index.core.memory import ChatMemoryBuffer
from wingman.plugins.stocks import YahooFinanceToolSpec
from wingman.plugins.email_tool import send_email
from wingman.plugins.weather import get_weather
from wingman.plugins.file_ops import FileOpsToolSpec
from wingman.plugins.notion_func import NotionToolSpec
from wingman.plugins.calendar.events import CalendarToolSpec

from wingman.core.memory import Memory
from wingman.core.model_loader import ModelLoader
from wingman.core.prompts import MODEL_PROMPT


class Wingman():
    def __init__(self, model_name, api_key):
        self.memory = Memory()
        self.tokenizer = tiktoken.encoding_for_model("gpt-4o")
        self.model = ModelLoader(model_name, api_key=api_key).load_groq()
        self.tools = [send_email, get_weather] \
        + FileOpsToolSpec().to_tool_list() \
        + YahooFinanceToolSpec().to_tool_list() + CalendarToolSpec().to_tool_list() + NotionToolSpec().to_tool_list()
        self.memory_buffer = {}
        self.agent_cache = {}

    def get_chat_history(self, thread_id):
        history = self.memory.get_thread_history(thread_id)
        return history if history else []
    
    def classify_and_load_memory(self, user_input):
        user_input_lower = user_input.lower()

        long_keywords = [
            r"\bi am\b", r"\bi'm\b", r"\bmy name\b", r"\bfather\b", r"\bmother\b", r"\bbrother\b",
            r"\bsister\b", r"\bfamily\b", r"\buncle\b", r"\baunt\b", r"\bcousin\b"
        ]
        event_keywords = [
            r"\bbirthday\b", r"\bmeeting\b", r"\baccident\b", r"\bevent\b", r"\bwedding\b", r"\bdate\b",
            r"\bwhen\b", r"\bwhere\b", r"\bhappened\b"
        ]

        def matches_any(keywords):
            return any(re.search(pattern, user_input_lower) for pattern in keywords)

        if matches_any(long_keywords):
            mtype = "long_term"
        elif matches_any(event_keywords):
            mtype = "event"
        else:
            mtype = "none"

        if mtype == "none":
            return []
            
        return self.memory.search_recall_memories(user_input, config={"configurable": {"mtype": mtype}})

    def build_tools(self):
        tools = []
        for tool in self.tools:
            if isinstance(tool, FunctionTool):
                tools.append(tool)
            elif callable(tool):
                tools.append(FunctionTool.from_defaults(fn=tool, name=tool.__name__))
            else:
                raise TypeError(f"Unsupported tool type: {tool}")
        return tools

    def _initialize_agent(self, from_memory):
        memory_context = "\n".join(from_memory) if from_memory else "No relevant memory found."
        system_prompt = f"""
                Today is {datetime.datetime.now().strftime('%d %B %Y, %I:%M %p')}.
                Context loaded from memory:
                {memory_context}
                {MODEL_PROMPT}
                """
                
        return ReActAgent(
            system_prompt=system_prompt,
            llm=self.model,
            tools=self.build_tools(),
            verbose=True
        )

    async def chat(self, query, thread_id):
        history = self.get_chat_history(thread_id)
        chat_messages = [ChatMessage(role=msg["role"], content=msg["content"]) for msg in history]
        
        from_memory = self.classify_and_load_memory(query)
        
        if thread_id not in self.memory_buffer:
            self.memory_buffer[thread_id] = ChatMemoryBuffer.from_defaults(chat_history=chat_messages, token_limit=40000)
        else:
            for msg in chat_messages:
                if msg not in self.memory_buffer[thread_id].get_all():
                    self.memory_buffer[thread_id].put(msg)
        if thread_id not in self.agent_cache:  
            self.agent_cache[thread_id] = self._initialize_agent(from_memory)
        
        agent = self.agent_cache[thread_id]
        response = await agent.run(query, memory=self.memory_buffer[thread_id])
        response = response.response.blocks[0].text

        self.memory.save_thread_history(thread_id, [
            {"role": "user", "content": query},
            {"role": "assistant", "content": str(response)}
        ])
        
        self.memory_buffer[thread_id].put(ChatMessage(role="user", content=query))
        self.memory_buffer[thread_id].put(ChatMessage(role="assistant", content=str(response)))
        
        return response


# import datetime
# import tiktoken
# import re

# from llama_index.core.agent.workflow import ReActAgent
# from llama_index.core.tools import FunctionTool
# from llama_index.core.llms import ChatMessage
# from llama_index.core.memory import ChatMemoryBuffer
# from llama_index.tools.yahoo_finance import YahooFinanceToolSpec
# from wingman.plugins.email_tool import send_email
# from wingman.plugins.file_ops import read_file, write_file, find_all_user_files, open_file
# from wingman.plugins.notion_func import NotionClient
# from wingman.plugins.calendar.events import Calendar

# from wingman.core.memory import Memory
# from wingman.core.model_loader import ModelLoader
# from wingman.core.prompts import MODEL_PROMPT


# class Wingman():
#     def __init__(self, model_name, api_key):
#         self.memory = Memory()
#         self.tokenizer = tiktoken.encoding_for_model("gpt-4o")
#         self.model = ModelLoader(model_name, api_key=api_key).load_groq()
#         self.tools = [send_email, read_file, write_file, find_all_user_files, open_file] + YahooFinanceToolSpec().to_tool_list()
#         self.agent = None

#     def get_chat_history(self, thread_id):
#         history = self.memory.get_thread_history(thread_id)
#         return history if history else []
    
#     def classify_and_load_memory(self, user_input):

#         user_input_lower = user_input.lower()

#         long_keywords = [
#             r"\bi am\b", r"\bi'm\b", r"\bmy name\b", r"\bfather\b", r"\bmother\b", r"\bbrother\b",
#             r"\bsister\b", r"\bfamily\b", r"\buncle\b", r"\baunt\b", r"\bcousin\b"
#         ]
#         event_keywords = [
#             r"\bbirthday\b", r"\bmeeting\b", r"\baccident\b", r"\bevent\b", r"\bwedding\b", r"\bdate\b",
#             r"\bwhen\b", r"\bwhere\b", r"\bhappened\b"
#         ]

#         def matches_any(keywords):
#             return any(re.search(pattern, user_input_lower) for pattern in keywords)

#         if matches_any(long_keywords):
#             mtype = "long_term"
#         elif matches_any(event_keywords):
#             mtype = "event"
#         else:
#             mtype = "none"

#         if mtype == "none":
#             return []
#         convo_str = self.tokenizer.decode(self.tokenizer.encode(user_input))
#         return self.memory.search_recall_memories(convo_str, config={"configurable": {"mtype": mtype}})


#     def build_tools(self):
#         tools = []
#         for tool in self.tools:
#             if isinstance(tool, FunctionTool):
#                 tools.append(tool)
#             elif callable(tool):
#                 tools.append(FunctionTool.from_defaults(fn=tool, name=tool.__name__))
#             else:
#                 raise TypeError(f"Unsupported tool type: {tool}")
#         return tools

#     async def chat(self, query, thread_id):
#         history = self.get_chat_history(thread_id)
#         history = [ChatMessage(role=msg["role"], content=msg["content"]) for msg in history]

#         memory = ChatMemoryBuffer.from_defaults(chat_history=history, token_limit=40000)
#         from_memory = self.classify_and_load_memory(query)
#         model = self.model
#         if not self.agent:
#             self.agent = ReActAgent(
#                 system_prompt=f"""
#                         Today is {datetime.datetime.now().strftime('%d %B %Y,  %I:%M %p')}.
#                         Context loaded from memory: {', '.join(from_memory)}
#                         {MODEL_PROMPT}
#                         """,
#                 llm=model,
#                 tools=self.build_tools()
#             )
        
#         handler = await self.agent.run(query, memory=memory)
#         response = handler
#         self.memory.save_thread_history(thread_id, [
#         {"role": "user", "content": query},
#         {"role": "assistant", "content": str(response)}
#         ])

#         return response