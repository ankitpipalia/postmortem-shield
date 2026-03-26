from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from postmortem_shield.pipeline import ShieldPipeline

app = FastAPI(title="Postmortem Shield", version="0.1.0")


class GenerateRequest(BaseModel):
    postmortem_text: str = Field(min_length=10)
    source_file: str = "api-input.md"
    provider: str = "mock"


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/generate")
def generate(request: GenerateRequest):
    try:
        pipeline = ShieldPipeline(provider_name=request.provider)
        bundle = pipeline.run_from_text(
            postmortem_text=request.postmortem_text,
            source_file=request.source_file,
            output_dir=None,
        )
        return bundle.model_dump(mode="json")
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc
