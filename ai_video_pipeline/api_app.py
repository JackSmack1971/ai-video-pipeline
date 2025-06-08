from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from config import load_config, get_pipeline_config, PipelineConfig
from pipeline import ContentPipeline
from services.factory import create_services
from utils.logging_config import setup_logging
from infrastructure.task_queue import TaskQueue, JobStatus
from infrastructure.worker_manager import WorkerManager
from infrastructure.autoscaler import Autoscaler

app = FastAPI()
queue = TaskQueue()
worker_manager: WorkerManager | None = None
autoscaler: Autoscaler | None = None


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


async def _process_job(job_id: str, req: GenerationRequest) -> None:
    cfg = load_config()
    if req.config_file:
        cfg.pipeline = _load_custom(req.config_file)
    cfg.pipeline.default_video_duration = req.duration
    container = create_services(cfg)
    pipe = ContentPipeline(cfg, container)
    status = await queue.get_job_status(job_id)
    status.status = "running"
    try:
        result = await pipe.run_multiple_videos(req.video_count)
        out_dir = Path(req.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        for idx, item in enumerate(result):
            Path(item["video"]).rename(out_dir / f"video_{idx}.mp4")
        status.status = "completed"
    except Exception as exc:
        status.status = "failed"
        status.error = str(exc)


@app.post("/generate")
async def generate_content(req: GenerationRequest) -> Dict[str, str]:
    job_id = await queue.enqueue_video_generation(req)
    return {"job_id": job_id}


@app.get("/status/{job_id}")
async def job_status(job_id: str) -> Dict[str, str | int]:
    try:
        status = await queue.get_job_status(job_id)
        return {k: v for k, v in status.__dict__.items() if v is not None}
    except KeyError:
        raise HTTPException(status_code=404, detail="Job not found")


@app.on_event("startup")
async def startup() -> None:
    global worker_manager, autoscaler
    setup_logging()
    worker_manager = WorkerManager(queue, _process_job)
    await worker_manager.start(1)
    autoscaler = Autoscaler(queue, worker_manager)
    await autoscaler.start()


@app.on_event("shutdown")
async def shutdown() -> None:
    if autoscaler:
        await autoscaler.stop()
    if worker_manager:
        await worker_manager.stop()
