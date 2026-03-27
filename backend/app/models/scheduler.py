"""Scheduler run log model."""
from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, JSON, Float

from app.core.database import Base


class SchedulerRunLog(Base):
    """Record of each scheduled job execution."""

    __tablename__ = "scheduler_run_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Job identification
    job_id = Column(String, nullable=False, index=True)
    job_name = Column(String, nullable=True)

    # Timing
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)

    # Result
    status = Column(String, nullable=False, default="running")  # running/success/error
    result = Column(JSON, nullable=True)  # structured result data
    error_message = Column(String, nullable=True)

    def __repr__(self):
        return (
            f"<SchedulerRunLog(id={self.id}, job_id='{self.job_id}', "
            f"status='{self.status}', started_at='{self.started_at}')>"
        )
