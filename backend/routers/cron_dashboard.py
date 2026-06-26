from fastapi import APIRouter, HTTPException
from backend.models import CronJobUpdate
from backend.services.cron_scheduler import get_all_jobs, update_job_cron, enable_job, disable_job, manual_run, get_job_history

router = APIRouter(prefix="/api/cron", tags=["cron"])

@router.get("/jobs")
async def api_list_jobs():
    return get_all_jobs()

@router.post("/jobs/{job_id}/update")
async def api_update_job(job_id: str, body: CronJobUpdate):
    try:
        if body.cron_expression:
            update_job_cron(job_id, body.cron_expression)
        if body.enabled is True:
            enable_job(job_id)
        elif body.enabled is False:
            disable_job(job_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"ok": True, "job_id": job_id}

@router.post("/jobs/{job_id}/run-now")
async def api_run_job_now(job_id: str):
    try:
        manual_run(job_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"ok": True, "job_id": job_id}

@router.get("/jobs/{job_id}/history")
async def api_job_history(job_id: str):
    return get_job_history(job_id)
