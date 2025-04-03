

import datetime
import json
import tiktoken
import re

from wingman.plugins.email_tool import send_email
from wingman.plugins.file_ops import read_file, write_file, find_all_user_files, open_file
from wingman.plugins.calendar.events import Calendar
from wingman.core.memory import Memory

import datetime
from wingman.core.model_loader import ModelLoader
from wingman.core.prompts import CLASSIFY_PROMPT, MODEL_PROMPT



class WingmanOpenAI:
    def __init__(self, model_name, api_key):
        self.memory = Memory()
        self.calender = Calendar()
        self.tokenizer = tiktoken.encoding_for_model("gpt-4o")
        self.tools = {
            "send_email": send_email,
            "read_file": read_file,
            "write_file": write_file,
            "open_file": open_file,
            "find_all_user_files": find_all_user_files,
            "save_recall_memory": self.memory.save_recall_memory,
            "create_event": self.calender.create_event,
            "get_events": self.calender.get_events,
        }
        self.model_name = model_name
        self.api_key = api_key
        self.client = ModelLoader(model_name, apiKey=api_key).load_client()


    def get_chat_history(self, thread_id):
        history = self.memory.get_thread_history(thread_id)
        return history if history else []



    def should_continue(self, context):
        last_msg = context["messages"][-1]
        print("Last Message: ", last_msg)
        if isinstance(last_msg, dict) and last_msg["role"] == "function":
            return "call_model"
        if last_msg.tool_calls:
            return "tools"
        if last_msg.content:
            return "end"
        return "end"
    

    def call_model(self, context):
        messages = context["messages"]
        user_input = messages[-1]["content"]
        from_memory = self.classify_and_load_memory(user_input)

        system_prompt = f"""
                        Today is {datetime.datetime.now().strftime('%d %B %Y,  %I:%M %p')}.
                        Context loaded from memory: {', '.join(from_memory)}
                        {MODEL_PROMPT}
                        """

        full_messages = [{"role": "system", "content": system_prompt}] + messages

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=full_messages,
            temperature=0.6,
            tools=[t.tool_schema for t in self.tools.values()]
        )

        reply = response.choices[0].message
        context["messages"].append(reply)
        
        if reply.content and ("<tool_call" in reply.content or "<function" in reply.content):
            context["messages"].append({
                "role": "assistant",
                "content": "Error: Detected invalid manual tool call formatting. Please try rephrasing."
                })
            return context

        return context


    def tool_node(self, context):
        last_msg = context["messages"][-1]
        if not hasattr(last_msg, "tool_calls"):
            return context

        print("ToolCall: ", last_msg.tool_calls)
        for tool_call in last_msg.tool_calls:
            tool_name = tool_call.function.name
            try:
                args = json.loads(tool_call.function.arguments)
            except Exception as e:
                print(f"[TOOL ERROR] {tool_name} failed: {e}")
                context["messages"].append({
                    "role": "function",
                    "name": tool_name,
                    "content": f"Tool argument parsing error: {e}"
                })
                continue

            tool_func = self.tools.get(tool_name)
            if tool_func:
                try:
                    result = tool_func(**args)
                    context["messages"].append({"role": "function", "name": tool_name, "content": str(result)})
                except Exception as e:
                    context["messages"].append({"role": "function", "name": tool_name, "content": f"Tool error: {e}"})
        return context


    # def classify_and_load_memory(self, user_input):
    #     prompt = f"""
    #     Query: "{user_input}"
    #     {CLASSIFY_PROMPT}
    #     """

    #     response = self.client.chat.completions.create(
    #         model=self.model_name,
    #         messages=[{"role": "system", "content": prompt}],
    #         temperature=0.2, 
    #     )

    #     mtype = response.choices[0].message.content.strip().lower()
    #     if mtype == "none":
    #         return []
    #     convo_str = self.tokenizer.decode(self.tokenizer.encode(user_input))
    #     return self.memory.search_recall_memories(convo_str, config={"configurable": {"mtype": mtype}})


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
        convo_str = self.tokenizer.decode(self.tokenizer.encode(user_input))
        return self.memory.search_recall_memories(convo_str, config={"configurable": {"mtype": mtype}})


    def run(self, user_input, thread_id):
        history = self.get_chat_history(thread_id)

        context = {
            "messages": [],
            "state": "call_model",
            "thread_id": thread_id,
        }

        context["messages"].extend(history)

        context["messages"].append({"role": "user", "content": user_input})

        while context["state"] != "end":
            if context["state"] == "call_model":
                context = self.call_model(context)
            elif context["state"] == "tools":
                context = self.tool_node(context)
            else:
                break

            context["state"] = self.should_continue(context)

        last_msg = context["messages"][-1]

        clean_messages = [
            {"role": "user", "content": user_input},
            {"role": last_msg.role,"content": last_msg.content.replace(MODEL_PROMPT, "")}
            ]

        self.memory.save_thread_history(thread_id, clean_messages)

        print("History: ", self.memory.get_thread_history(thread_id))

        return context["messages"][-1].content
