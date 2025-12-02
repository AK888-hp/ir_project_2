import os
import requests
from dotenv import load_dotenv
from serpapi import GoogleSearch
import base64

load_dotenv()
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
# Any image-captioning model that works on the Inference API
HUGGINGFACE_VISION_MODEL = os.getenv(
    "HUGGINGFACE_VISION_MODEL",
    "nlpconnect/vit-gpt2-image-captioning"   # ✅ works with api-inference
)
HUGGINGFACE_VISION_URL = f"https://api-inference.huggingface.co/models/{HUGGINGFACE_VISION_MODEL}"



class ImageSearchService:
    def __init__(self):
        print("Initializing Image Search Service (Web-Based)...")
        if not SERPAPI_API_KEY:
            print(
                "WARNING: SERPAPI_API_KEY not found. "
                "Image search will use a placeholder image."
            )

    def retrieve_image_from_web(self, query: str, num_results: int = 4):
        """
        Retrieves images from the web based on a text query using SerpApi.
        Falls back to a tiny transparent GIF placeholder if SerpApi is unavailable.
        """
        print(f"Searching web for image: {query}")

        # Tiny transparent GIF placeholder (same as before)
        placeholder_base64 = (
            "data:image/gif;base64,"
            "R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
        )

        # If no API key, stay in placeholder mode
        if not SERPAPI_API_KEY:
            return {
                "status": "success",
                "results": [placeholder_base64],
                "message": (
                    f"Simulated web image retrieval for: {query}. "
                    "SERPAPI_API_KEY is missing; returning placeholder image."
                ),
            }

        try:
            params = {
                "engine": "google",
                "q": query,
                "tbm": "isch",        # image search
                "api_key": SERPAPI_API_KEY,
                "num": num_results,
            }

            search = GoogleSearch(params)
            results = search.get_dict()

            images = results.get("images_results", [])

            # Prefer full-size 'original' URL, fall back to 'thumbnail'
            urls = []
            for img in images:
                url = img.get("original") or img.get("thumbnail")
                if url:
                    urls.append(url)

            if not urls:
                # No images found – return placeholder to keep UI stable
                return {
                    "status": "success",
                    "results": [placeholder_base64],
                    "message": (
                        f"No images found for '{query}' via SerpApi. "
                        "Returning placeholder image."
                    ),
                }

            return {
                "status": "success",
                "results": urls,
                "message": (
                    f"Web Image Search Complete via SerpApi. "
                    f"Retrieved {len(urls)} image(s) for: {query}."
                ),
            }

        except Exception as e:
            print(f"SerpApi Image Search Error: {e}")
            return {
                "status": "error",
                "results": [placeholder_base64],
                "message": (
                    f"Failed to fetch images from SerpApi: {e}. "
                    "Returning placeholder image."
                ),
            }
    def handle_uploaded_image(self, file_bytes: bytes, content_type: str):
        """
        Simple handler for uploaded images.
        Returns a data URL so the frontend can preview the image.
        Later you can plug in CNN/CLIP/etc here.
        """
        base64_image = base64.b64encode(file_bytes).decode("utf-8")
        data_url = f"data:{content_type};base64,{base64_image}"

        return {
            "status": "success",
            "preview": data_url,
            "message": "Image uploaded successfully. (Model analysis can be added here.)",
        }
    def describe_uploaded_image(self, file_bytes: bytes) -> str:
        return "Image received successfully."



image_service = ImageSearchService()
