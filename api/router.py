from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from services.text_search import text_service
from services.image_search import image_service
from api.schemas import TextSearchResult, ImageSearchResult

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# --- HTML/Template Routes ---

@router.get("/", response_class=HTMLResponse)
async def serve_root(request: Request):
    """Serves the main unified search page."""
    return templates.TemplateResponse("index.html", {"request": request})

# --- Web Image Search Endpoint ---

@router.post("/search_image_web", response_model=ImageSearchResult)
async def search_image_web_endpoint(query: str = Form(...)):
    """Fetches images from the web based on a text query."""
    if not query.strip():
        raise HTTPException(status_code=400, detail="Please provide a text query for the web image search.")
    
    try:
        result = image_service.retrieve_image_from_web(query)
        return result
        
    except Exception as e:
        print(f"Web Image Search Error: {e}")
        raise HTTPException(status_code=500, detail=f"Web Image Search Error: {e}")

# --- Unified Text Chat Endpoint (Web RAG/NER) ---

@router.post("/chat", response_model=TextSearchResult)
async def unified_chat(
    text_query: str = Form(...), 
    image_file: UploadFile = File(None) # File input is ignored
):
    """Handles text query for Web RAG/NER."""
    if not text_query or not text_query.strip():
        raise HTTPException(status_code=400, detail="Please provide a text query.")

    try:
        # 1. RETRIEVE context from the Web
        context_docs = text_service.retrieve_from_web(text_query)
        
        # 2. PERFORM MEDICAL NER (NLP STEP)
        ner_results = []
        if context_docs:
            most_relevant_doc = context_docs[0] 
            ner_results = text_service.extract_medical_entities(most_relevant_doc)
        
        # 3. GENERATE answer (RAG Step)
        generated_answer = text_service.generate_answer(text_query, context_docs)
        
        # 4. Return the complete result
        return {
            "status": "success",
            "answer": generated_answer,
            "source_documents": context_docs, 
            "ner_results": ner_results,
        }

    except Exception as e:
        print(f"Web RAG/NLP Error: {e}")
        raise HTTPException(status_code=500, detail=f"Web RAG/NLP Error: {e}")