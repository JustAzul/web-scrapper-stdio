import sys
import json
import asyncio
from scraper import extract_text_from_url
import markdownify

async def process_line(line: str):
    try:
        data = json.loads(line)
        url = data.get("url")
        if not url:
            return {"status": "error_invalid_url", "error_message": "Missing 'url' field", "extracted_text": "", "final_url": None}
        # Extract content
        result = await extract_text_from_url(url)
        # Convert to Markdown if extraction succeeded
        if result["status"] == "success":
            result["extracted_text"] = markdownify.markdownify(result["extracted_text"], heading_style=markdownify.ATX)
        return result
    except json.JSONDecodeError:
        return {"status": "error_invalid_input", "error_message": "Input is not valid JSON", "extracted_text": "", "final_url": None}
    except Exception as e:
        return {"status": "error_unknown", "error_message": str(e), "extracted_text": "", "final_url": None}

async def main():
    while True:
        line = sys.stdin.readline()
        if not line:
            break
        line = line.strip()
        if not line:
            continue
        result = await process_line(line)
        print(json.dumps(result), flush=True)

if __name__ == "__main__":
    asyncio.run(main()) 