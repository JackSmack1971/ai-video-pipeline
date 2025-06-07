from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Dict
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from config import load_config, get_pipeline_config, PipelineConfig
from pipeline import ContentPipeline
from services.factory import create_services
from utils.logging_config import setup_logging

app = FastAPI()
_jobs: Dict[str, Dict[str, str | int]] = {}


class GenerationRequest(BaseModel):
    idea_type: str = Field(default="general", max_length=50)
    video_count: int = Field(default=get_pipeline_config().video_batch_small, ge=1, le=10)
    duration: int = Field(default=get_pipeline_config().default_video_duration, ge=1, le=60)
    output_dir: str = Field(default="outputs")
    config_file: str | None = None


def _load_custom(path: str) -> PipelineConfig:
    data = json.loads(Path(path).read_text())
    base = get_pipeline_config()
    for k, v in data.items():
        setattr(base, k, v)
    return base


async def _run_job(job_id: str, req: GenerationRequest) -> None:
    cfg = load_config()
    if req.config_file:
        cfg.pipeline = _load_custom(req.config_file)
    cfg.pipeline.default_video_duration = req.duration
    services = create_services(cfg)
    pipe = ContentPipeline(cfg, services)
    _jobs[job_id]["status"] = "running"
    try:
        result = await pipe.run_multiple_videos(req.video_count)
        out_dir = Path(req.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        for idx, item in enumerate(result):
            Path(item["video"]).rename(out_dir / f"video_{idx}.mp4")
        _jobs[job_id]["status"] = "completed"
    except Exception as exc:
        _jobs[job_id]["status"] = "failed"
        _jobs[job_id]["error"] = str(exc)


@app.post("/generate")
async def generate_content(req: GenerationRequest) -> Dict[str, str]:
    job_id = uuid4().hex
    _jobs[job_id] = {"status": "pending"}
    asyncio.create_task(_run_job(job_id, req))
    return {"job_id": job_id}


@app.get("/status/{job_id}")
async def job_status(job_id: str) -> Dict[str, str | int]:
    if job_id not in _jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return _jobs[job_id]


@app.on_event("startup")
async def startup() -> None:
    setup_logging()
