from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.embeddings.gemini import GeminiEmbedding
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

class InfoRetrieverAgent:
    def __init__(self):
        # Configure LlamaIndex to use Gemini embedding model
        Settings.embed_model = GeminiEmbedding(
            model_name="models/embedding-001",
            api_key=os.getenv("GOOGLE_API_KEY")
        )
        
        # Mocked LlamaIndex setup (replace with actual data loading)
        self.index = VectorStoreIndex.from_documents([])  # Placeholder
        self.model = genai.GenerativeModel("gemini-1.5-flash")

    def retrieve_info(self, state):
        destination = state.get("destination")
        interests = state.get("interests")
        
        # Mocked query to LlamaIndex or Gemini
        prompt = f"Provide detailed information about {destination} focusing on {', '.join(interests)}. Include top attractions, cultural tips, and safety info."
        response = self.model.generate_content(prompt)
        
        state["destination_info"] = response.text
        return state