import uuid

from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from fastapi.responses import HTMLResponse, Response
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import get_session
from app.models.assets import Document
from app.utils.pdf import download_pdf

router = APIRouter(
    prefix="/downloads",
    tags=["Download Endpoints"],
)


@router.get("/documents/{id}", response_class=HTMLResponse)
async def pdf_download(id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    document = await session.get(Document, id)

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    pdf_bytes = download_pdf(document.filename)
    return Response(
        pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={document.filename}"},
    )
