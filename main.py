import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from api.router import router
from core.config import STATIC_DIR

load_dotenv() 

# --- FastAPI App Setup ---
app = FastAPI(
    title="Web-Based Multimodal AI Chatbot",
    version="1.0.0",
    description="Uses external APIs for all data retrieval (Web RAG, NER, Web Image Search).",
)

# --- Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Mount Static Files ---
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# --- Include API Routes ---
app.include_router(router)

# --- Uvicorn Execution ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)