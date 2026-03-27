"""Scheduler schemas."""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class JobInfo(BaseModel):
    """Information about a scheduled job."""
    id: str
    name: str
    next_run_time: Optional[str] = None
    trigger: str
    status: str  # active / paused


class SchedulerStatus(BaseModel):
    """Overall scheduler status."""
    running: bool
    job_count: int
    jobs: List[JobInfo]
    timezone: str


class RunLogResponse(BaseModel):
    """Scheduler run log entry."""
    id: int
    job_id: str
    job_name: Optional[str]
    started_at: datetime
    finished_at: Optional[datetime]
    duration_seconds: Optional[float]
    status: str
    result: Optional[Dict[str, Any]]
    error_message: Optional[str]

    class Config:
        from_attributes = True


class ManualRunResponse(BaseModel):
    """Response for manual job trigger."""
    job_id: str
    message: str
    run_log_id: Optional[int] = None
