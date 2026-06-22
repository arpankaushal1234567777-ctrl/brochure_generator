from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl

from config import AVAILABLE_TEMPLATES, DEFAULT_TEMPLATE
from main import generate_brochure

app = FastAPI(
    title="Brochure Generator API",
    description="Generate AI-powered company brochures by crawling a website.",
    version="2.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://brochuregenerator47.vercel.app",
    ],
    allow_credentials=False,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["Content-Type"],
)

TemplateName = Literal["corporate", "modern", "minimal", "executive"]


class BrochureRequest(BaseModel):
    url: HttpUrl
    template: TemplateName = DEFAULT_TEMPLATE


class ContactInfo(BaseModel):
    emails: list[str]
    phones: list[str]


class Traceability(BaseModel):
    overview: list[str]
    services: list[str]
    products: list[str]
    industries: list[str]
    contact: list[str]


class BrochureResponse(BaseModel):
    company_name: str
    overview: str
    services: list[str]
    products: list[str]
    industries: list[str]
    contact: ContactInfo
    generation_time: float
    generated_at: str
    template_used: TemplateName
    pdf_available: bool
    pdf_data: str
    traceability: Traceability


@app.post("/generate", response_model=BrochureResponse)
async def generate(request: BrochureRequest):
    try:
        return generate_brochure(str(request.url), request.template)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health():
    return {"status": "ok", "templates": AVAILABLE_TEMPLATES}
