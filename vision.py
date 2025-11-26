from fastapi import APIRouter, UploadFile, File, HTTPException
from app.agents.vision import extract_from_image_bytes, extract_from_pdf_file

router = APIRouter()


@router.post("/extract")
async def extract(file: UploadFile = File(...)):
    try:
        content = await file.read()
        if file.filename.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
            notes = extract_from_image_bytes(content, file.content_type or "image/png")
        elif file.filename.lower().endswith(".pdf"):
            notes = extract_from_pdf_file(content, max_pages=2)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type")
        return {"filename": file.filename, "notes": notes}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


from __future__ import annotations
import os, base64
from typing import List
from pypdf import PdfReader


def _gemini_model():
    import google.generativeai as genai

    api = os.getenv("GOOGLE_API_KEY")
    if not api:
        raise RuntimeError("GOOGLE_API_KEY is not set")
    genai.configure(api_key=api)
    return genai.GenerativeModel("gemini-1.5-pro")


def extract_from_image_bytes(img_bytes: bytes, mime: str = "image/png") -> str:
    mdl = _gemini_model()
    part = {"mime_type": mime, "data": img_bytes}
    prompt = (
        "Extract plan legends, general notes, key symbols, utility abbreviations, "
        "and any constraints related to trench depth, dewatering, soils, or road sections. "
        "Return as concise bullets."
    )
    resp = mdl.generate_content([prompt, part])
    return getattr(resp, "text", "") or ""


def extract_from_pdf_file(pdf_bytes: bytes, max_pages: int = 2) -> str:
    # extract page images is heavy; instead send page text to Gemini as context
    reader = PdfReader(io := __import__("io").BytesIO(pdf_bytes))
    pages = []
    for i in range(min(max_pages, len(reader.pages))):
        pages.append(reader.pages[i].extract_text() or "")
    mdl = _gemini_model()
    prompt = (
        "Given these plan pages (text-extracted), list legends, notes, abbreviations, "
        "and any constraints that affect shallow sewer design, dewatering, poor soils, "
        "and roadway sections. Use bullets.\n\n" + "\n\n---PAGE---\n\n".join(pages)
    )
    resp = mdl.generate_content(prompt)
    return getattr(resp, "text", "") or ""
