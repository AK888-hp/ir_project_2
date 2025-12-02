import os
import requests
import re
from dotenv import load_dotenv
from serpapi import GoogleSearch # Library to fetch Google search results

load_dotenv() 

# --- External API Configuration ---
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY") 
HUGGINGFACE_RAG_API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
HUGGINGFACE_NER_API_URL = "https://api-inference.huggingface.co/models/dslim/bert-base-NER" 
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY") 
# -----------------------------------

# --- Define a simple local medical vocabulary for demonstration (NLP feature) ---
MEDICAL_KEYWORDS = [
    "fever", "chills", "headache", "pain", "inflammation", 
    "antibiotics", "treatment", "diagnosis", "virus", "symptoms", "jaundice"
]
# -----------------------------------------------------------------------------

class GoogleSearchClient:
    """Uses SerpApi to fetch real organic search results."""
    def __init__(self):
        self.api_key = SERPAPI_API_KEY
        if not self.api_key:
             print("FATAL WARNING: SERPAPI_API_KEY not found. Search will use placeholder data.")

    def search(self, query: str, num_results: int = 3) -> list:
        """Fetches organic search snippets from the web."""
        if not self.api_key:
             # Placeholder fallback if key is missing
             return [
                "Placeholder Context 1: **Web Retrieval is LIVE!** The internet source confirms that the symptoms of fever include elevated body temperature and chills.",
                "Placeholder Context 2: **LLM Active!** The external LLM is now generating an answer based on this web-fetched context.",
                "Placeholder Context 3: All data is currently simulated for structure validation."
            ]

        try:
            params = {
                "engine": "google",
                "q": query,
                "api_key": self.api_key,
                "num": num_results
            }
            search = GoogleSearch(params)
            results = search.get_dict()
            
            # Extract snippets from organic results
            snippets = [
                item.get('snippet', 'No snippet available.') 
                for item in results.get('organic_results', [])
            ]
            
            return snippets if snippets else [f"No web results found for '{query}'."]
            
        except Exception as e:
            print(f"SerpApi Search Error: {e}")
            return [f"ERROR: Failed to connect to SerpApi. Check your key and network. Error: {str(e)}"]


class TextSearchService:
    def __init__(self):
        print("Initializing Text Search Service (Live Web RAG)...")
        self.search_client = GoogleSearchClient()

    def retrieve_from_web(self, query_text: str, n_results: int = 3) -> list:
        """Retrieves context from the web (via SerpApi)."""
        return self.search_client.search(query_text, n_results)

    def extract_medical_entities(self, text: str) -> list:
        """Performs local keyword extraction using regex and a predefined vocabulary."""
        found_entities = []
        text_lower = text.lower()
        
        for keyword in MEDICAL_KEYWORDS:
            if re.search(r'\b' + re.escape(keyword) + r'\b', text_lower):
                found_entities.append({
                    "entity_group": "KEYWORD",
                    "score": 1.0, 
                    "word": keyword.capitalize()
                })
        return found_entities

    def generate_answer(self, query_text: str, context_docs: list) -> str:
        """Uses Hugging Face API for RAG generation based on context."""
        if not HUGGINGFACE_API_KEY:
            return "Answer Generation Failed: HUGGINGFACE_API_KEY is missing."

        if not context_docs:
            return "No web results were retrieved. Cannot generate an answer."

        # Check for placeholder to guide the user
        if "Placeholder Context 1" in context_docs[0]:
            return "Answer generated successfully! (Using placeholder data. Integrate a live search API for real information.)"
            
        context = "\n---\n".join(context_docs)
        
        # --- RAG Prompt Construction and API Call ---
        system_prompt = "You are a professional medical chatbot. Answer the user's QUESTION concisely and accurately based ONLY on the context provided below. If the context does not contain the answer, politely state that you cannot answer from the provided documents. Do not use external knowledge. Always maintain a professional tone."
        
        full_prompt = (
            f"### SYSTEM INSTRUCTION:\n{system_prompt}\n\n"
            f"### CONTEXT DOCUMENTS:\n{context}\n\n"
            f"### QUESTION:\n{query_text}"
        )
        
        headers = {
            "Authorization": f"Bearer {HUGGINGFACE_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "inputs": full_prompt,
            "parameters": {
                "max_new_tokens": 500,
                "temperature": 0.1,
                "return_full_text": False
            }
        }
        
        try:
            response = requests.post(HUGGINGFACE_RAG_API_URL, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            if result and isinstance(result, list) and 'generated_text' in result[0]:
                return result[0]['generated_text'].strip()
            
            return f"LLM API returned an unexpected structure: {result}"

        except requests.exceptions.RequestException as e:
            return f"Answer Generation Failed due to API connection error: {e}"

text_service = TextSearchService()