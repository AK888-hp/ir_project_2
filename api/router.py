from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from services.text_search import text_service
from services.image_search import image_service
from api.schemas import TextSearchResult, ImageSearchResult
from services.image_search import image_service

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

@router.post("/upload-image")
async def upload_image(file: UploadFile = File(...)):
    """
    Accept an image file from the client and return a preview.
    """
    if file is None:
        raise HTTPException(status_code=400, detail="No file uploaded.")

    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are supported.")

    file_bytes = await file.read()
    result = image_service.handle_uploaded_image(file_bytes, file.content_type)
    return result

def _resolve_mode_auto(text_query: str, has_image: bool) -> str:
    """
    Decide what to do when mode='auto' based on text + image presence.
    """
    has_text = bool(text_query and text_query.strip())
    if has_image and not has_text:
        return "image_to_text"       # pure image query
    if has_image and has_text:
        return "image_and_text"      # combined
    if has_text:
        lower = text_query.lower()
        if any(k in lower for k in ["image", "picture", "photo", "show me", "see"]):
            return "text_to_image"   # 'show me an image of X'
        return "text_to_text"        # normal RAG question
    return "text_to_text"


@router.post("/multimodal_chat")
async def multimodal_chat(
    text_query: str = Form(None),
    mode: str = Form("auto"),  # 'auto', 'text_to_text', 'text_to_image', 'image_to_text', 'image_and_text'
    file: UploadFile = File(None),
):
    """
    Unified multimodal chat endpoint.
    - text only -> text-to-text (RAG)
    - text mentioning 'image/picture/...' -> text-to-image
    - image only -> image-to-text (+ similar images)
    - image + text -> combined reasoning (stubbed)
    """
    has_image = file is not None
    resolved_mode = _resolve_mode_auto(text_query, has_image) if mode == "auto" else mode

    # Normalise query
    query = (text_query or "").strip()

    answer = None
    images = []
    ner_results = []
    source_documents = []
    message = ""
    
    # --- TEXT → TEXT (RAG) ---
    if resolved_mode == "text_to_text":
        if not query:
            raise HTTPException(status_code=400, detail="text_query is required for text_to_text mode.")

        source_documents = text_service.retrieve_from_web(query)
        ner_results = text_service.extract_medical_entities(query)
        answer = text_service.generate_answer(query, source_documents)
        message = "RAG/NLP text answer generated."

    # --- TEXT → IMAGE ---
    elif resolved_mode == "text_to_image":
        if not query:
            raise HTTPException(status_code=400, detail="text_query is required for text_to_image mode.")

        img_result = image_service.retrieve_image_from_web(query)
        images = img_result.get("results", [])
        message = img_result.get("message", "Text-to-image web search complete.")

        # Optional: also generate a short text explanation based on snippets
        source_documents = text_service.retrieve_from_web(query)
        answer = text_service.generate_answer(
    (
        f"Describe what a typical image illustrating '{query}' would look like. "
        "Answer in 2 complete sentences. Make sure the final sentence is complete "
        "and does not end abruptly."
    ),
    source_documents
)


    # --- IMAGE → TEXT (and IMAGE → IMAGE) ---
    elif resolved_mode == "image_to_text":
        if not has_image:
            raise HTTPException(status_code=400, detail="Image file is required for image_to_text mode.")

        file_bytes = await file.read()

        # Preview (data URL) if you want to show uploaded image
        preview_data = image_service.handle_uploaded_image(file_bytes, file.content_type)
        # text explanation
        answer = image_service.describe_uploaded_image(file_bytes)

        # For image→image, we can use filename (without extension) as a loose query
        filename_base = (file.filename or "medical image").rsplit(".", 1)[0]
        img_result = image_service.retrieve_image_from_web(filename_base)
        images = img_result.get("results", [])
        message = "Image uploaded and described. Retrieved similar web images."

        # You can also call text_service here if you want RAG over some concept
        source_documents = []  # or some RAG based on filename_base if you want

        # Optionally include preview
        preview = preview_data.get("preview")
        if preview:
            images = [preview] + images

    # --- IMAGE + TEXT combined ---
    elif resolved_mode == "image_and_text":
        if not has_image:
            raise HTTPException(status_code=400, detail="Image file is required for image_and_text mode.")
        file_bytes = await file.read()

        # Basic description
        img_description = image_service.describe_uploaded_image(file_bytes)
        combined_query = f"{query}\n\nImage description: {img_description}"

        source_documents = text_service.retrieve_from_web(combined_query)
        ner_results = text_service.extract_medical_entities(combined_query)
        answer = text_service.generate_answer(combined_query, source_documents)

        filename_base = (file.filename or "medical image").rsplit(".", 1)[0]
        img_result = image_service.retrieve_image_from_web(filename_base)
        images = img_result.get("results", [])
        message = "Combined text + image reasoning completed."

    else:
        raise HTTPException(status_code=400, detail=f"Unknown mode: {resolved_mode}")

    return {
        "mode": resolved_mode,
        "answer": answer,
        "images": images,
        "ner_results": ner_results,
        "source_documents": source_documents,
        "message": message,
    }