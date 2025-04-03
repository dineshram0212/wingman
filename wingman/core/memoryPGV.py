import os
from dotenv import load_dotenv
import datetime

from huggingface_hub import snapshot_download
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain_postgres import PGVector
from langchain_postgres.vectorstores import PGVector
from wingman.utils.tool_decorator import tool


load_dotenv()


class Memory():
    
    def __init__(self):
        self.db_connection_string = os.getenv('DB_CONNECTION_STRING')

        embeddings_path = "../models/embeddings"

        if not os.path.exists(embeddings_path):
            snapshot_download(
                repo_id="sentence-transformers/all-MiniLM-L6-v2",
                local_dir=embeddings_path,
                local_dir_use_symlinks=False
            )

        self.embeddings = HuggingFaceEmbeddings(model_name=embeddings_path)
        
        self.vector_store = PGVector(
            embeddings=self.embeddings,
            connection=self.db_connection_string,
        )
    
    def get_memory_type(self, config: RunnableConfig):
        mtype = config["configurable"].get("mtype")
        if mtype is None:
            raise ValueError("Memory Type needs to be provided.")
        return mtype
            
    def search_recall_memories(self, query: str, config: RunnableConfig):
        """Search for relevant memories."""
        mtype = self.get_memory_type(config)

        query_embeddings = self.embeddings.embed_query(query)
        print(f"Searching for query - {query} in {mtype}.")
        results = self.vector_store.similarity_search_by_vector(query_embeddings, k=3, filter=dict(mtype=mtype))
        return [doc.page_content for doc in results]


@tool
def save_recall_memory(chat: str, mtype: str):
    """
    Save conversation (chat) as memory to vectorstore in collection name -mtype for later semantic retrieval.

    :param chat: The conversation or message history to store in memory.
    :param mtype: The memory type or collection name (e.g., 'long_term', 'event').
    """    
    try:
        memory = Memory()
        current_datetime = datetime.datetime.now().strftime('%d %B %Y, %I:%M %p')
        document = Document(
            page_content=f"{chat} ; Timestamp: '{current_datetime}'", 
            metadata={"mtype": mtype}
        )
        memory.vector_store.add_documents([document])
        return {"message": [f"Successfully saved '{chat}' as {mtype}."]}

    except Exception as e:
        return {"message": ["Message failed to save."]}