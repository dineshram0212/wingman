from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages
from typing_extensions import Annotated


class State:
    messages: Annotated[list[AnyMessage], add_messages]

    def __init__(self, messages=None):
        self.messages = messages or []