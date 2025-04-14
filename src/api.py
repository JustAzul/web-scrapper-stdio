from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, HttpUrl
import logging

from .scraper import extract_text_from_url

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Web Scraper MCP Tool",
    description="Fetches primary text content from URLs using headless browsing."
)

class ExtractRequest(BaseModel):
    url: HttpUrl

class ExtractResponse(BaseModel):
    extracted_text: str
    status: str
    error_message: str | None = None
    final_url: str

@app.post("/extract", response_model=ExtractResponse)
async def extract_content(request: ExtractRequest):
    """API endpoint to extract text from a given URL."""
    logger.info(f"Received extraction request for URL: {request.url}")
    
    # Basic URL validation is handled by Pydantic's HttpUrl
    # Add any further custom validation if needed
    if not str(request.url).startswith(("http://", "https://")):
        logger.warning(f"Invalid URL scheme provided: {request.url}")
        # Although Pydantic usually catches this, double-check
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid URL scheme. Only HTTP and HTTPS are supported."
        )

    # We rely on the scraper function to handle all errors internally
    # and return the appropriate status in the dictionary.
    try:
        result = await extract_text_from_url(str(request.url))
        
        # Log if the extraction wasn't successful, but don't raise HTTP error
        if result["status"] != "success":
             logger.warning(f"Extraction for {request.url} finished with status '{result['status']}'. Error: {result['error_message']}")
        else:
             logger.info(f"Extraction successful for {request.url}. Final URL: {result['final_url']}")
             
        # Always return HTTP 200 OK. The success/failure is in the JSON body.
        return ExtractResponse(**result)

    except Exception as e:
        # Catch unexpected errors during the call to the scraper *itself* 
        # or during response packaging. This indicates an internal server error.
        logger.exception(f"Unexpected internal error processing URL {request.url}: {e}")
        # Return a generic error response consistent with the schema, but log the real error
        # We still return 200 OK as per PRD, but status indicates failure.
        return ExtractResponse(
            extracted_text="",
            status="error_unknown",
            error_message=f"An unexpected internal server error occurred.",
            final_url=str(request.url) # Use original URL as final is unknown
        )

# Add a simple root endpoint for health checks or basic info
@app.get("/")
async def root():
    return {"message": "Web Scraper MCP Tool is running."} 