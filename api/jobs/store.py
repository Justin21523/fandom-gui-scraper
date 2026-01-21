from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional, List

from api.jobs.models import JobStatus, UniversalJobRequest, UniversalJobProgress, UniversalJobInfo
from api.jobs.queue import get_redis_text


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _job_key(job_id: str) -> str:
    return f"job:{job_id}"


def _log_key(job_id: str) -> str:
    return f"job:{job_id}:logs"


def _control_key(job_id: str) -> str:
    return f"job:{job_id}:control"


def _jobs_zset() -> str:
    return "jobs:all"


def create_job(job_id: str, config: UniversalJobRequest, output_root: str) -> None:
    r = get_redis_text()
    info = {
        "job_id": job_id,
        "status": JobStatus.queued.value,
        "created_at": _utcnow().isoformat(),
        "started_at": "",
        "finished_at": "",
        "config": config.model_dump_json(),
        "progress": UniversalJobProgress().model_dump_json(),
        "output_root": output_root,
        "error": "",
    }
    r.hset(_job_key(job_id), mapping=info)
    r.zadd(_jobs_zset(), {job_id: _utcnow().timestamp()})
    r.hset(_control_key(job_id), mapping={"stop": "0", "pause": "0"})


def update_status(job_id: str, status: JobStatus, error: str = "") -> None:
    r = get_redis_text()
    mapping: Dict[str, str] = {"status": status.value}
    if status == JobStatus.running:
        mapping["started_at"] = _utcnow().isoformat()
    if status in (JobStatus.finished, JobStatus.failed, JobStatus.stopped):
        mapping["finished_at"] = _utcnow().isoformat()
    if error:
        mapping["error"] = error
    r.hset(_job_key(job_id), mapping=mapping)


def update_progress(job_id: str, progress: UniversalJobProgress) -> None:
    r = get_redis_text()
    r.hset(_job_key(job_id), mapping={"progress": progress.model_dump_json()})


def append_log(job_id: str, line: str, max_lines: int = 2000) -> None:
    r = get_redis_text()
    r.rpush(_log_key(job_id), line)
    r.ltrim(_log_key(job_id), -max_lines, -1)


def get_job(job_id: str) -> Optional[UniversalJobInfo]:
    r = get_redis_text()
    data = r.hgetall(_job_key(job_id))
    if not data:
        return None

    def _dt(value: str) -> Optional[datetime]:
        if not value:
            return None
        return datetime.fromisoformat(value)

    config = UniversalJobRequest.model_validate_json(data["config"])
    progress = UniversalJobProgress.model_validate_json(data.get("progress") or "{}")
    return UniversalJobInfo(
        job_id=data["job_id"],
        status=JobStatus(data["status"]),
        created_at=datetime.fromisoformat(data["created_at"]),
        started_at=_dt(data.get("started_at", "")),
        finished_at=_dt(data.get("finished_at", "")),
        config=config,
        progress=progress,
        output_root=data.get("output_root", ""),
        error=data.get("error") or None,
    )


def list_jobs(limit: int = 50) -> List[UniversalJobInfo]:
    r = get_redis_text()
    job_ids = r.zrevrange(_jobs_zset(), 0, max(0, limit - 1))
    jobs: List[UniversalJobInfo] = []
    for job_id in job_ids:
        job = get_job(job_id)
        if job:
            jobs.append(job)
    return jobs


def request_stop(job_id: str) -> None:
    get_redis_text().hset(_control_key(job_id), "stop", "1")


def request_pause(job_id: str, pause: bool) -> None:
    get_redis_text().hset(_control_key(job_id), "pause", "1" if pause else "0")


def get_controls(job_id: str) -> Dict[str, str]:
    return get_redis_text().hgetall(_control_key(job_id))


def get_logs(job_id: str, limit: int = 200) -> List[str]:
    r = get_redis_text()
    return r.lrange(_log_key(job_id), max(0, -limit), -1)


def delete_job_metadata(job_id: str) -> None:
    r = get_redis_text()
    r.delete(_job_key(job_id), _log_key(job_id), _control_key(job_id))
    r.zrem(_jobs_zset(), job_id)
