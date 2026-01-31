"""
Worker script to process pending jobs.
Run this separately or as a cron job to process jobs that are stuck in pending status.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import get_all_jobs, update_job
from app.models import JobStatus
from app.tasks import process_pipeline_job


async def process_pending_jobs():
    """Find and process all pending jobs."""
    print("[WORKER] Checking for pending jobs...")
    
    jobs = await get_all_jobs(limit=100)
    pending_jobs = [j for j in jobs if j.get("status") == JobStatus.PENDING]
    
    if not pending_jobs:
        print("[WORKER] No pending jobs found.")
        return
    
    print(f"[WORKER] Found {len(pending_jobs)} pending job(s)")
    
    for job in pending_jobs:
        job_id = str(job["_id"])
        print(f"[WORKER] Processing job {job_id}...")
        
        try:
            await process_pipeline_job(
                job_id=job_id,
                niche=job.get("niche", ""),
                location=job.get("location", ""),
                max_results=job.get("max_results", 50),
                mode=job.get("mode", "local")
            )
        except Exception as e:
            print(f"[WORKER ERROR] Failed to process job {job_id}: {e}")
            await update_job(job_id, {
                "status": JobStatus.FAILED,
                "error_message": str(e)[:500]
            })


if __name__ == "__main__":
    asyncio.run(process_pending_jobs())
