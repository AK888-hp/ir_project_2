import os
import requests
import re
from dotenv import load_dotenv
from serpapi import GoogleSearch # Library to fetch Google search results

load_dotenv() 

# --- External API Configuration ---
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
HUGGINGFACE_RAG_MODEL = os.getenv(
    "HUGGINGFACE_RAG_MODEL",
    "HuggingFaceTB/SmolLM3-3B:hf-inference"  # default chat model via HF Inference
)
HUGGINGFACE_RAG_API_URL = "https://router.huggingface.co/v1/chat/completions"
HUGGINGFACE_NER_API_URL = "https://api-inference.huggingface.co/models/dslim/bert-base-NER"
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")
USE_SERPAPI = os.getenv("USE_SERPAPI","true").lower() == "true" 
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
        if not self.api_key or not USE_SERPAPI:
        # placeholder mode
            return [
                "Placeholder Context 1: **Web Retrieval is LIVE!** The internet source confirms that the symptoms of fever include elevated body temperature and chills.",
                "Placeholder Context 2: **LLM Active!** The external LLM is now generating an answer based on this web-fetched context.",
                f"Placeholder Context 3: All data is currently simulated for structure validation. Original query was: '{query}'."
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
        """Uses Hugging Face Inference Providers (router API) for RAG generation based on context."""
        if not HUGGINGFACE_API_KEY:
            return "Answer Generation Failed: HUGGINGFACE_API_KEY is missing."

        if not context_docs:
            return "No web results were retrieved. Cannot generate an answer."

        # Check for placeholder to guide the user
        if "Placeholder Context 1" in context_docs[0]:
            return (
                "Answer generated successfully! (Using placeholder web context. "
                "Integrate a live search API for real information.)"
            )

        context = "\n---\n".join(context_docs)

        # System + user messages for chat completion
        system_prompt = (
            "You are a professional medical chatbot. Answer the user's QUESTION concisely and "
            "accurately based ONLY on the context provided below. If the context does not contain "
            "the answer, politely state that you cannot answer from the provided documents. "
            "Do not use external knowledge. Always maintain a professional tone."
        )

        user_content = (
            f"### CONTEXT DOCUMENTS:\n{context}\n\n"
            f"### QUESTION:\n{query_text}"
        )

        headers = {
            "Authorization": f"Bearer {HUGGINGFACE_API_KEY}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": HUGGINGFACE_RAG_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            "max_tokens": 500,
            "temperature": 0.1,
        }

        try:
            response = requests.post(
                HUGGINGFACE_RAG_API_URL, headers=headers, json=payload, timeout=60
            )
            response.raise_for_status()
            data = response.json()

            # OpenAI-style response: choices[0].message.content
            if (
                isinstance(data, dict)
                and "choices" in data
                and len(data["choices"]) > 0
                and "message" in data["choices"][0]
                and "content" in data["choices"][0]["message"]
            ):
                content = data["choices"][0]["message"]["content"].strip()
                content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
                return content
            return f"LLM API returned an unexpected structure: {data}"

        except requests.exceptions.RequestException as e:
            return f"Answer Generation Failed due to API connection error: {e}"

text_service = TextSearchService()