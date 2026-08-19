from __future__ import annotations

from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from src.feedback import submit_feedback
from src.llm import LLMConfig
from src.pipeline import generate_production_pack
from src.storage import list_history, list_style_packs, load_history

ROOT = Path(__file__).resolve().parent
WEB_DIST = ROOT / "web" / "dist"

app = FastAPI(title="聊斋短片工作室", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class GenerateRequest(BaseModel):
    source_text: str = Field(min_length=1)
    style_pack_id: str = "guofeng-liaozhai-v0.1"
    duration_preset: Literal["8s", "12s", "15s"] = "12s"
    force_template: bool = False


class FeedbackRequest(BaseModel):
    run_id: str
    style_score: int = Field(ge=1, le=5)
    character_score: int = Field(ge=1, le=5)
    motion_score: int = Field(ge=1, le=5)
    atmosphere_score: int = Field(ge=1, le=5)
    notes: str = ""
    video_path: str = ""


@app.get("/api/health")
def health():
    llm = LLMConfig()
    return {"ok": True, "llm": llm.status_text()}


@app.get("/api/style-packs")
def style_packs():
    return [p.model_dump() for p in list_style_packs()]


@app.post("/api/generate")
def generate(req: GenerateRequest):
    try:
        pack, mode = generate_production_pack(
            source_text=req.source_text.strip(),
            style_pack_id=req.style_pack_id,
            duration_preset=req.duration_preset,
            force_template=req.force_template,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    data = pack.model_dump()
    data["mode"] = mode
    return data


@app.get("/api/history")
def history(limit: int = 50):
    items = list_history(limit=limit)
    return [
        {
            "id": it.get("id"),
            "title": (it.get("script") or {}).get("title", "未命名"),
            "created_at": it.get("created_at"),
            "duration_preset": it.get("duration_preset"),
            "has_feedback": bool(it.get("feedback")),
            "is_gold": bool((it.get("feedback") or {}).get("is_gold")),
        }
        for it in items
    ]


@app.get("/api/history/{run_id}")
def history_detail(run_id: str):
    try:
        return load_history(run_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/feedback")
def feedback(req: FeedbackRequest):
    try:
        pack = submit_feedback(
            run_id=req.run_id.strip(),
            style_score=req.style_score,
            character_score=req.character_score,
            motion_score=req.motion_score,
            atmosphere_score=req.atmosphere_score,
            notes=req.notes,
            video_path=req.video_path,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return pack.model_dump()


# Serve Vue build in production: `npm run build` then `python server.py`
if WEB_DIST.exists():
    assets = WEB_DIST / "assets"
    if assets.exists():
        app.mount("/assets", StaticFiles(directory=assets), name="assets")

    @app.get("/{full_path:path}")
    def spa(full_path: str):
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found")
        candidate = WEB_DIST / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(WEB_DIST / "index.html")


def main() -> None:
    import uvicorn

    uvicorn.run("server:app", host="127.0.0.1", port=7860, reload=True)


if __name__ == "__main__":
    main()
