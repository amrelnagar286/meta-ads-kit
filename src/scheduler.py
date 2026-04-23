"""
Scheduler — Background extraction scheduling with configurable intervals.
Uses APScheduler for reliable cron-style and interval-based scheduling.
"""
import logging
import os
import json
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

log = logging.getLogger(__name__)


class ExtractionJob:
    """Represents a scheduled extraction configuration."""

    def __init__(
        self,
        job_id: str,
        name: str,
        access_token: str,
        ad_account_id: str,
        levels: List[str],
        breakdowns: List[str],
        preset: str = "last_30d",
        interval_minutes: int = 60,
        enabled: bool = True,
        output_dir: str = "output",
    ):
        self.job_id = job_id
        self.name = name
        self.access_token = access_token
        self.ad_account_id = ad_account_id
        self.levels = levels
        self.breakdowns = breakdowns
        self.preset = preset
        self.interval_minutes = interval_minutes
        self.enabled = enabled
        self.output_dir = output_dir
        self.last_run: Optional[str] = None
        self.last_status: Optional[str] = None
        self.run_count: int = 0

    def to_dict(self) -> dict:
        return {
            "job_id": self.job_id,
            "name": self.name,
            "ad_account_id": self.ad_account_id,
            "levels": self.levels,
            "breakdowns": self.breakdowns,
            "preset": self.preset,
            "interval_minutes": self.interval_minutes,
            "enabled": self.enabled,
            "output_dir": self.output_dir,
            "last_run": self.last_run,
            "last_status": self.last_status,
            "run_count": self.run_count,
        }


class ExtractionScheduler:
    """Manages scheduled extraction jobs."""

    def __init__(self, state_file: str = "config/scheduler_state.json"):
        self.state_file = state_file
        self.jobs: Dict[str, ExtractionJob] = {}
        self._scheduler = None
        self._load_state()

    def _load_state(self) -> None:
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, encoding="utf-8") as f:
                    state = json.load(f)
                for jdata in state.get("jobs", []):
                    job = ExtractionJob(
                        job_id=jdata["job_id"],
                        name=jdata.get("name", ""),
                        access_token="",
                        ad_account_id=jdata.get("ad_account_id", ""),
                        levels=jdata.get("levels", ["ad"]),
                        breakdowns=jdata.get("breakdowns", ["none"]),
                        preset=jdata.get("preset", "last_30d"),
                        interval_minutes=jdata.get("interval_minutes", 60),
                        enabled=jdata.get("enabled", True),
                        output_dir=jdata.get("output_dir", "output"),
                    )
                    job.last_run = jdata.get("last_run")
                    job.last_status = jdata.get("last_status")
                    job.run_count = jdata.get("run_count", 0)
                    self.jobs[job.job_id] = job
            except Exception as e:
                log.error(f"Failed to load scheduler state: {e}")

    def _save_state(self) -> None:
        os.makedirs(os.path.dirname(self.state_file) or ".", exist_ok=True)
        state = {"jobs": [j.to_dict() for j in self.jobs.values()]}
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)

    def add_job(self, job: ExtractionJob) -> None:
        self.jobs[job.job_id] = job
        self._save_state()
        log.info(f"Added job: {job.name} ({job.job_id})")

    def remove_job(self, job_id: str) -> bool:
        if job_id in self.jobs:
            del self.jobs[job_id]
            self._save_state()
            return True
        return False

    def toggle_job(self, job_id: str) -> Optional[bool]:
        job = self.jobs.get(job_id)
        if not job:
            return None
        job.enabled = not job.enabled
        self._save_state()
        return job.enabled

    def get_jobs(self) -> List[Dict]:
        return [j.to_dict() for j in self.jobs.values()]

    def record_run(
        self, job_id: str, status: str = "success"
    ) -> None:
        job = self.jobs.get(job_id)
        if job:
            job.last_run = datetime.now().isoformat()
            job.last_status = status
            job.run_count += 1
            self._save_state()

    def start(self, run_fn: Callable) -> None:
        """Start the background scheduler."""
        try:
            from apscheduler.schedulers.background import BackgroundScheduler

            self._scheduler = BackgroundScheduler()
            for job in self.jobs.values():
                if job.enabled:
                    self._scheduler.add_job(
                        run_fn,
                        "interval",
                        minutes=job.interval_minutes,
                        id=job.job_id,
                        kwargs={"job": job},
                    )
            self._scheduler.start()
            log.info("Scheduler started")
        except ImportError:
            log.warning("APScheduler not installed. Scheduling disabled.")
        except Exception as e:
            log.error(f"Failed to start scheduler: {e}")

    def stop(self) -> None:
        if self._scheduler:
            self._scheduler.shutdown(wait=False)
            log.info("Scheduler stopped")
