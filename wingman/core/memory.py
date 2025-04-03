import json
import uuid
import datetime
from dotenv import load_dotenv

import chromadb
from sentence_transformers import SentenceTransformer

from langchain_core.runnables import RunnableConfig
from wingman.utils.tool_decorator import tool

load_dotenv()

class Memory:
    def __init__(self):
        self.client = chromadb.PersistentClient(path="./memory/chroma_db")

        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.collection = self.client.get_or_create_collection(name="wingman_memory")

    def embed(self, text: str):
        return self.model.encode(text).tolist()

    def get_memory_type(self, config: RunnableConfig):
        mtype = config["configurable"].get("mtype")
        if mtype is None:
            raise ValueError("Memory Type needs to be provided.")
        return mtype

    def search_recall_memories(self, query: str, config: RunnableConfig):
        mtype = self.get_memory_type(config)
        print(f"Searching for query - {query} in {mtype}.")
        embedding = self.embed(query)

        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=3,
            where={"mtype": mtype}
        )
        return results.get("documents", [[]])[0]

    def save_memory(self, text: str, mtype: str):
        """
        Save a general memory (`long_term`, `event`).
        """
        metadata = {
            "mtype": mtype,
            "timestamp": datetime.datetime.now().isoformat()
        }

        self.collection.add(
            documents=[text],
            embeddings=[self.embed(text)],
            metadatas=[metadata],
            ids=[str(uuid.uuid4())]
        )

    def get_thread_history(self, thread_id: str):
        results = self.collection.get(where={"thread_id": thread_id})
        return json.loads(results["documents"][0]) if results["documents"] else []

    def save_thread_history(self, thread_id: str, conversation: list):
        """
        Save the full conversation (as a list of message dicts) for a thread.
        """
        existing_history = self.get_thread_history(thread_id)
        updated_history = existing_history + conversation

        metadata = {
            "mtype": "history",
            "thread_id": thread_id,
            "timestamp": datetime.datetime.now().isoformat()
        }

        self.collection.add(
            documents=[json.dumps(updated_history)], 
            embeddings=[self.embed(json.dumps(updated_history))],
            metadatas=[metadata],
            ids=[thread_id]
        )

    
    def delete_thread_history(self, thread_id: str):
        collection = self.client.get_collection(name="wingman_memory")
        collection.delete(where={"thread_id": thread_id})
        
        return self.client.clear_system_cache()


    @tool
    def save_recall_memory(self, chat: str, mtype: str):
        """
        Save conversation (chat) as memory to vectorstore for semantic retrieval.
        - mtype can be: 'long_term' or 'event'.
        """
        try:
            self.save_memory(chat, mtype)
            return {"message": [f"Successfully saved '{chat}' as {mtype}."]}
        except Exception as e:
            print("Error saving memory:", e)
            return {"message": ["Message failed to save."]}
