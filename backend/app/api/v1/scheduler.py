"""Scheduler management API routes."""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query

from app.services.scheduler import get_data_scheduler
from app.schemas.scheduler import SchedulerStatus, RunLogResponse, ManualRunResponse

router = APIRouter(prefix="/scheduler", tags=["scheduler"])


@router.get("/status", response_model=SchedulerStatus)
def scheduler_status():
    """Get scheduler status and all registered jobs."""
    sched = get_data_scheduler()
    return sched.get_status()


@router.get("/history", response_model=List[RunLogResponse])
def run_history(
    job_id: Optional[str] = Query(None, description="Filter by job ID"),
    limit: int = Query(20, ge=1, le=100, description="Number of records"),
):
    """Get scheduler execution history."""
    sched = get_data_scheduler()
    return sched.get_run_history(limit=limit, job_id=job_id)


@router.post("/jobs/{job_id}/run", response_model=ManualRunResponse)
def run_job(job_id: str):
    """Manually trigger a job to run immediately."""
    sched = get_data_scheduler()
    if not sched.is_running:
        raise HTTPException(status_code=503, detail="Scheduler is not running")
    result = sched.run_job_now(job_id)
    if "Unknown job" in result.get("message", ""):
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    return result


@router.post("/jobs/{job_id}/pause")
def pause_job(job_id: str):
    """Pause a scheduled job."""
    sched = get_data_scheduler()
    if not sched.is_running:
        raise HTTPException(status_code=503, detail="Scheduler is not running")
    ok = sched.pause_job(job_id)
    if not ok:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    return {"message": f"Job {job_id} paused"}


@router.post("/jobs/{job_id}/resume")
def resume_job(job_id: str):
    """Resume a paused job."""
    sched = get_data_scheduler()
    if not sched.is_running:
        raise HTTPException(status_code=503, detail="Scheduler is not running")
    ok = sched.resume_job(job_id)
    if not ok:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    return {"message": f"Job {job_id} resumed"}
