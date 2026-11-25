import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import evaluator
import pdf_generator

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(
    title="AI Sentinel — Enterprise AI Agent Validation Suite",
    version="1.2.0",
    description="Pre-deployment adversarial stress-testing, evaluation, and prompt optimization suite for AI agents.",
)

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


class ValidationRequest(BaseModel):
    api_key: Optional[str] = Field(default=None, description="Optional Gemini API key override")
    agent_prompt: str = Field(..., min_length=1, description="Target agent system prompt")
    knowledge_base: str = Field(default="", description="Optional FAQ/knowledge base context")
    selected_categories: List[str] = Field(..., min_length=1, description="Adversarial categories to run")
    use_sample_agent: bool = Field(default=False, description="Run pre-compiled offline sample mode")


@app.get("/", include_in_schema=False)
def serve_index() -> FileResponse:
    index_path = STATIC_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=500, detail="Frontend assets missing: static/index.html not found.")
    return FileResponse(str(index_path), media_type="text/html")


@app.get("/api/health")
def health_check() -> Dict[str, Any]:
    has_server_key = bool(os.environ.get("GEMINI_API_KEY", "").strip())
    return {
        "status": "ok",
        "model": evaluator.DEFAULT_MODEL,
        "has_server_key": has_server_key,
    }


@app.get("/api/sample-template")
def get_sample_template() -> Dict[str, str]:
    return {
        "agent_prompt": evaluator.SAMPLE_PROMPT,
        "knowledge_base": evaluator.SAMPLE_KB,
    }


@app.post("/api/validate")
def run_validation(payload: ValidationRequest) -> JSONResponse:
    effective_key = (payload.api_key or "").strip() or os.environ.get("GEMINI_API_KEY", "").strip()

    if not payload.use_sample_agent and not effective_key:
        raise HTTPException(
            status_code=400,
            detail="GEMINI_API_KEY is required for Live Validation mode. Enter an API key or enable Offline Sample Demo mode.",
        )

    try:
        result = evaluator.run_validation_pipeline(
            api_key=effective_key if not payload.use_sample_agent else None,
            agent_prompt=payload.agent_prompt,
            knowledge_base=payload.knowledge_base,
            selected_categories=payload.selected_categories,
            use_sample_agent=payload.use_sample_agent,
            progress_callback=None,
        )
        return JSONResponse(content=result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Gemini validation pipeline failed: {exc}",
        ) from exc


@app.post("/api/report")
async def generate_report(request: Request) -> Response:
    try:
        data = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON payload for PDF report.") from exc

    if not isinstance(data, dict) or not data.get("results"):
        raise HTTPException(status_code=400, detail="Validation results are required to generate a PDF report.")

    try:
        pdf_bytes = pdf_generator.generate_pdf_report(data)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to compile PDF report: {exc}") from exc

    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="No scenario results available for PDF generation.")

    filename = f"AI_Sentinel_Validation_Report_{int(time.time())}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=int(os.environ.get("PORT", "8000")), reload=True)
