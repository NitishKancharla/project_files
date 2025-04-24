from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
import os

class DestinationKnowledge:
    def __init__(self):
        self.index = None
        self.load_data()
        
    def load_data(self):
        data_path = "data/destinations"
        if not os.path.exists(data_path):
            os.makedirs(data_path)
            
        documents = SimpleDirectoryReader(data_path).load_data()
        self.index = VectorStoreIndex.from_documents(documents)
        
    def query(self, question: str) -> str:
        query_engine = self.index.as_query_engine()
        return query_engine.query(question)