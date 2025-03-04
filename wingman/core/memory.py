import os
from dotenv import load_dotenv
import datetime

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain_postgres import PGVector
from langchain_postgres.vectorstores import PGVector

load_dotenv()


class Memory():
    
    def __init__(self):
        self.db_connection_string = os.getenv('DB_CONNECTION_STRING')

        embeddings_path = "../models/embeddings"

        if os.path.exists(embeddings_path):
            self.embeddings = HuggingFaceEmbeddings(model_name=embeddings_path)
        else:
            model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
            model.save(embeddings_path)
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
            
    def save_recall_memory(self, query: str, config: RunnableConfig):
        """Save memory to vectorstore for later semantic retrieval."""
        mtype = self.get_memory_type(config)

        document = Document(
                page_content=query + f" ; Timestamp:'{datetime.datetime.now().strftime('%d %B %Y,  %I:%M %p')}'", 
                metadata={"mtype": mtype})
        self.vector_store.add_documents([document])
        print(f"Saving - {query} as {mtype}.")
        return mtype

    def search_recall_memories(self, query: str, config: RunnableConfig):
        """Search for relevant memories."""
        mtype = self.get_memory_type(config)

        query_embeddings = self.embeddings.embed_query(query)
        print(f"Searching for query - {query} in {mtype}.")
        results = self.vector_store.similarity_search_by_vector(query_embeddings, k=3, filter=dict(mtype=mtype))
        return [doc.page_content for doc in results]

