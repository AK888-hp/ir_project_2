from pydantic import BaseModel
from typing import List

# --- NER Entity ---
class NEREntity(BaseModel):
    entity_group: str
    score: float
    word: str
    
# --- Search Results ---
class TextSearchResult(BaseModel):
    status: str
    answer: str                 
    source_documents: List[str] 
    ner_results: List[NEREntity] = [] 

class ImageSearchResult(BaseModel):
    status: str
    results: List[str] # List of Base64 Data URLs
    message: str | None = None