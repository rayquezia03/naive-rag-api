from fastapi import APIRouter, UploadFile, File, HTTPException

from app.services.ingestion import ingest_markdown

router = APIRouter()


@router.post("/ingest")
async def ingest(file: UploadFile = File(...)):
    if not file.filename or not file.filename.endswith(".md"):
        raise HTTPException(status_code=400, detail="Only Markdown (.md) files are supported.")

    content = await file.read()
    if not content.strip():
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")

    return ingest_markdown(content, file.filename)
