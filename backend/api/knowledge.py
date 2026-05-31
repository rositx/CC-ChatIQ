import uuid
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, status, HTTPException
from backend.tasks.ingestion import ingest_document_task

router = APIRouter(prefix="/api/v1/knowledge", tags=["knowledge"])

@router.post("/ingest", status_code=status.HTTP_202_ACCEPTED)
async def ingest_document(
    document_title: str = Form(...),
    source_url: Optional[str] = Form(None),
    tenant_id: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    """
    REST endpoint to upload documents or submit web URLs for private vector database ingestion.
    Returns 202 Accepted status with a unique job ID immediately.
    """
    # Use a default mock tenant ID if not provided, for local testing
    resolved_tenant_id = tenant_id or "00000000-0000-0000-0000-000000000000"
    
    content = ""
    if file:
        try:
            content_bytes = await file.read()
            # Handle PDF vs raw text/markdown
            filename_lower = file.filename.lower()
            if filename_lower.endswith(".pdf"):
                import io
                from backend.utils.text import extract_text_from_pdf
                pdf_stream = io.BytesIO(content_bytes)
                content = extract_text_from_pdf(pdf_stream)
            else:
                content = content_bytes.decode("utf-8", errors="ignore")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to process uploaded file: {str(e)}"
            )
    elif source_url:
        # Simple dynamic web scraping trigger
        try:
            import httpx
            from backend.utils.text import scrape_web_page
            async with httpx.AsyncClient() as client:
                res = await client.get(source_url, timeout=10.0)
                res.raise_for_status()
                content = scrape_web_page(res.text)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to scrape webpage: {str(e)}"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either an upload file or source_url is required."
        )

    job_id = str(uuid.uuid4())
    # Offload chunking, embedding generation, and saving to celery worker tasks
    ingest_document_task.delay(resolved_tenant_id, document_title, source_url, content)
    
    return {"job_id": job_id, "status": "processing"}
