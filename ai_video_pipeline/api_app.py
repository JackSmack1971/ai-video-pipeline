from __future__ import annotations

import json
from pathlib import Path
from typing import Dict
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from utils.security_middleware import apply_security_middleware
from pydantic import BaseModel, Field

from config import load_config, get_pipeline_config, PipelineConfig
from security.auth_manager import AuthManager
from security.input_validator import InputValidator
from pipeline import ContentPipeline
from analytics.reporting import ReportingService, TimeRange
from services.factory import create_services
from utils.logging_config import setup_logging
from infrastructure.task_queue import TaskQueue, JobStatus
from infrastructure.worker_manager import WorkerManager
from infrastructure.autoscaler import Autoscaler
from analytics.usage_tracker import UsageTracker, GenerationRequest as UsageReq, GenerationResult
from analytics.cost_analyzer import CostAnalyzer
from analytics.quality_metrics import QualityMetrics

app = FastAPI()
apply_security_middleware(app)
queue = TaskQueue()
auth = AuthManager()
worker_manager: WorkerManager | None = None
autoscaler: Autoscaler | None = None
reporter: ReportingService | None = None


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    key = request.headers.get("X-API-KEY")
    token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
    user = None
    if token:
        user = await auth.validate_token(token)
    if not user and key:
        user = await auth.authenticate_api_key(key)
    if not user:
        return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
    if InputValidator.too_many_requests(user.id):
        return JSONResponse(status_code=429, content={"detail": "Too many requests"})
    request.state.user = user
    return await call_next(request)


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
    if reporter:
        await reporter.usage.track_generation_request(
            UsageReq(job_id, {"video_count": req.video_count, "user_id": req.idea_type})
        )
    try:
        result = await pipe.run_multiple_videos(req.video_count)
        out_dir = Path(req.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        for idx, item in enumerate(result):
            Path(item["video"]).rename(out_dir / f"video_{idx}.mp4")
        status.status = "completed"
        if reporter:
            await reporter.usage.track_generation_completion(GenerationResult(job_id, True))
    except Exception as exc:
        status.status = "failed"
        status.error = str(exc)
        if reporter:
            await reporter.usage.track_generation_completion(GenerationResult(job_id, False))


@app.post("/generate")
async def generate_content(req: GenerationRequest) -> Dict[str, str]:
    req.idea_type = await InputValidator.sanitize_text(req.idea_type)
    job_id = await queue.enqueue_video_generation(req)
    return {"job_id": job_id}


@app.get("/status/{job_id}")
async def job_status(job_id: str) -> Dict[str, str | int]:
    try:
        status = await queue.get_job_status(job_id)
        return {k: v for k, v in status.__dict__.items() if v is not None}
    except KeyError:
        raise HTTPException(status_code=404, detail="Job not found")


@app.get("/analytics/usage")
async def usage_analytics() -> Dict[str, int]:
    if not reporter:
        raise HTTPException(status_code=503, detail="Analytics unavailable")
    now = datetime.utcnow()
    rng = TimeRange(start=now.replace(hour=0, minute=0, second=0, microsecond=0), end=now)
    data = await reporter.usage.get_usage_patterns(rng)
    return data.__dict__


@app.get("/analytics/cost")
async def cost_analytics() -> Dict[str, float]:
    if not reporter:
        raise HTTPException(status_code=503, detail="Analytics unavailable")
    now = datetime.utcnow()
    rng = TimeRange(start=now.replace(hour=0, minute=0, second=0, microsecond=0), end=now)
    total = await reporter.costs.get_total_cost(rng)
    return {"total_cost": total}


@app.on_event("startup")
async def startup() -> None:
    global worker_manager, autoscaler, reporter
    setup_logging()
    worker_manager = WorkerManager(queue, _process_job)
    await worker_manager.start(1)
    autoscaler = Autoscaler(queue, worker_manager)
    await autoscaler.start()
    tracker = UsageTracker()
    costs = CostAnalyzer()
    quality = QualityMetrics()
    reporter = ReportingService(tracker, costs, quality)


@app.on_event("shutdown")
async def shutdown() -> None:
    if autoscaler:
        await autoscaler.stop()
    if worker_manager:
        await worker_manager.stop()
