from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from main import generate_brochure

app = FastAPI(
    title="Brochure Generator API",
    description="Generate AI-powered company brochures by crawling a website.",
    version="1.0.0"
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


class BrochureRequest(BaseModel):
    url: HttpUrl


class ContactInfo(BaseModel):
    emails: list[str]
    phones: list[str]


class BrochureResponse(BaseModel):
    company_name: str
    overview: str
    offerings: str
    industry: str
    contact: ContactInfo
    pdf_data: str


@app.post("/generate", response_model=BrochureResponse)
async def generate(request: BrochureRequest):
    try:
        brochure = generate_brochure(str(request.url))
        return brochure
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health():
    return {"status": "ok"}