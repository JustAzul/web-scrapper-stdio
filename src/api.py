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

    try:
        result = await extract_text_from_url(str(request.url))
        
        # Determine appropriate HTTP status code based on scraper status
        response_status_code = status.HTTP_200_OK
        if result["status"] not in ["success"]:
            if result["status"] in ["error_fetching", "error_timeout", "error_invalid_url"]:
                 # Treat fetching/timeout errors as potentially server-side or external issues
                 # Using 503 might be appropriate if the service couldn't reach the target
                 response_status_code = status.HTTP_503_SERVICE_UNAVAILABLE 
            elif result["status"] == "error_parsing":
                 # Parsing errors might indicate issues with the content itself, but the fetch was ok
                 # Still return 200 OK, but the status field indicates the problem
                 response_status_code = status.HTTP_200_OK 
            else:
                 # Unknown errors -> Internal Server Error
                 response_status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

            # Log the error status being returned
            logger.error(f"Extraction failed for {request.url}. Status: {result['status']}, Message: {result['error_message']}")
            
            # If it's a server-side issue, raise HTTPException to return non-200 status
            # Otherwise, return 200 OK with the error details in the response body
            if response_status_code != status.HTTP_200_OK:
                 raise HTTPException(
                    status_code=response_status_code,
                    detail=result["error_message"] or "Extraction failed"
                 )
        
        # If status is success or a non-HTTP-error status like 'error_parsing', return 200 OK
        return ExtractResponse(**result)

    except HTTPException as http_exc: # Re-raise HTTPExceptions
        raise http_exc
    except Exception as e:
        logger.exception(f"Unexpected error in API handler for URL {request.url}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected internal error occurred: {str(e)}"
        )

# Add a simple root endpoint for health checks or basic info
@app.get("/")
async def root():
    return {"message": "Web Scraper MCP Tool is running."} 