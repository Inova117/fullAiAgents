"""
The Bridge - FastAPI Backend
Main API application with endpoints for job management.
"""

import asyncio
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, BackgroundTasks, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from dotenv import load_dotenv

from .database import (
    connect_to_mongodb,
    close_mongodb_connection,
    create_job,
    get_job_by_id,
    get_all_jobs,
    create_campaign,
    get_campaign_by_id,
    get_all_campaigns,
    update_campaign,
    increment_campaign_metric,
    get_email_logs_by_campaign,
)
from .models import (
    StartJobRequest,
    StartJobResponse,
    JobResponse,
    JobListResponse,
    JobStatus,
    HealthResponse,
    CreateCampaignRequest,
    CreateCampaignResponse,
    CampaignResponse,
    CampaignListResponse,
    CampaignStatus,
    EmailLogsResponse,
    EmailLogResponse,
)
from .tasks import process_pipeline_job

# Load environment variables
load_dotenv()

# Configuration
EXPORTS_DIR = Path(__file__).parent.parent.parent / "data" / "exports"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown."""
    # Startup
    await connect_to_mongodb()
    yield
    # Shutdown
    await close_mongodb_connection()


# Create FastAPI app
app = FastAPI(
    title="The Bridge - Lead Generation API",
    description="Deterministic lead generation pipeline with async job processing",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Health Check
# ============================================================================

@app.get("/api/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Check API and database health."""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        database="connected"
    )


# ============================================================================
# Job Management Endpoints
# ============================================================================

from .auth import get_current_user

# ... (Previous imports)

# ============================================================================
# Job Management Endpoints
# ============================================================================

@app.post("/api/start-job", response_model=StartJobResponse, tags=["Jobs"])
async def start_job(
    request: StartJobRequest,
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user)
):
    """
    Start a new lead generation job.
    """
    # Create job in database
    job_data = {
        "user_id": user.get("sub"), # Storing Clerk User ID
        "status": JobStatus.PENDING,
        "niche": request.niche,
        "location": request.location,
        "max_results": request.max_results,
        "result_url": None,
        "error_message": None,
        "leads_count": None,
    }
    
    job_id = await create_job(job_data)
    
    # Add background task
    background_tasks.add_task(
        process_pipeline_job,
        job_id=job_id,
        niche=request.niche,
        location=request.location,
        max_results=request.max_results,
        mode=request.mode
    )
    
    return StartJobResponse(
        job_id=job_id,
        status=JobStatus.PENDING,
        message=f"Job started successfully. Search for '{request.niche}' in '{request.location}'"
    )


@app.post("/api/process-pending-jobs", tags=["Jobs"])
async def process_pending_jobs_endpoint(user: dict = Depends(get_current_user)):
    """
    Manually process all pending jobs.
    Useful when BackgroundTasks fail due to server sleep/restart.
    """
    jobs = await get_all_jobs(limit=100)
    user_pending_jobs = [
        j for j in jobs 
        if j.get("status") == JobStatus.PENDING 
        and j.get("user_id") == user.get("sub")
    ]
    
    if not user_pending_jobs:
        return {"message": "No pending jobs found", "processed": 0}
    
    processed_count = 0
    for job in user_pending_jobs:
        job_id = str(job["_id"])
        try:
            # Process synchronously (blocking, but necessary for reliability)
            await process_pipeline_job(
                job_id=job_id,
                niche=job.get("niche", ""),
                location=job.get("location", ""),
                max_results=job.get("max_results", 50),
                mode=job.get("mode", "local")
            )
            processed_count += 1
        except Exception as e:
            print(f"[ERROR] Failed to process job {job_id}: {e}")
            from .database import update_job
            await update_job(job_id, {
                "status": JobStatus.FAILED,
                "error_message": str(e)[:500]
            })
    
    return {
        "message": f"Processed {processed_count} pending job(s)",
        "processed": processed_count
    }



@app.get("/api/job/{job_id}", response_model=JobResponse, tags=["Jobs"])
async def get_job(job_id: str, user: dict = Depends(get_current_user)):
    """Get the status and details of a specific job."""
    # TODO: Filter by user_id
    job = await get_job_by_id(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    # Security Check: Ensure user owns this job
    if job.get("user_id") and job.get("user_id") != user.get("sub"):
         raise HTTPException(status_code=403, detail="Not authorized to view this job")
    
    return JobResponse(**job)


@app.get("/api/jobs", response_model=JobListResponse, tags=["Jobs"])
async def list_jobs(limit: int = 50, user: dict = Depends(get_current_user)):
    """List all jobs for the current user."""
    # We need to update get_all_jobs to filter by user_id
    # For now, we will filter in memory or update the DB function next
    jobs = await get_all_jobs(limit=limit)
    
    # Filter only user's jobs (Temporary in-memory filter until DB function update)
    user_jobs = [j for j in jobs if j.get("user_id") == user.get("sub") or not j.get("user_id")]
    
    return JobListResponse(
        jobs=[JobResponse(**job) for job in user_jobs],
        total=len(user_jobs)
    )


# ============================================================================
# Download Endpoint
# ============================================================================

@app.get("/api/download/{job_id}", tags=["Downloads"])
async def download_result(job_id: str, user: dict = Depends(get_current_user)):
    """Download the CSV result for a completed job."""
    # Check job exists and is completed
    job = await get_job_by_id(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    # Security Check
    if job.get("user_id") and job.get("user_id") != user.get("sub"):
         raise HTTPException(status_code=403, detail="Not authorized to access this file")
    
    if job.get("status") != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Job is not completed. Current status: {job.get('status')}"
        )
    
    # Find the file
    file_path = EXPORTS_DIR / f"{job_id}.csv"
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Result file not found")
    
    return FileResponse(
        path=file_path,
        filename=f"leads_{job.get('niche', 'export')}_{job.get('location', 'unknown')}.csv",
        media_type="text/csv"
    )


# ============================================================================
# Campaign Management Endpoints
# ============================================================================

# ... (create_new_campaign, get_campaign, list_campaigns processed in previous step)


@app.post("/api/campaigns/{campaign_id}/start", tags=["Campaigns"])
async def start_campaign(campaign_id: str, user: dict = Depends(get_current_user)):
    """Start or resume a campaign."""
    campaign = await get_campaign_by_id(campaign_id)
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
        
    # Security Check
    if campaign.get("user_id") and campaign.get("user_id") != user.get("sub"):
         raise HTTPException(status_code=403, detail="Not authorized to manage this campaign")
    
    if campaign["status"] not in [CampaignStatus.DRAFT, CampaignStatus.PAUSED, CampaignStatus.SCHEDULED]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot start campaign with status: {campaign['status']}"
        )
    
    await update_campaign(campaign_id, {"status": CampaignStatus.RUNNING})
    
    return {"message": "Campaign started", "campaign_id": campaign_id}


@app.post("/api/campaigns/{campaign_id}/pause", tags=["Campaigns"])
async def pause_campaign(campaign_id: str, user: dict = Depends(get_current_user)):
    """Pause a running campaign."""
    campaign = await get_campaign_by_id(campaign_id)
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
        
    # Security Check
    if campaign.get("user_id") and campaign.get("user_id") != user.get("sub"):
         raise HTTPException(status_code=403, detail="Not authorized to manage this campaign")
    
    if campaign["status"] != CampaignStatus.RUNNING:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot pause campaign with status: {campaign['status']}"
        )
    
    await update_campaign(campaign_id, {"status": CampaignStatus.PAUSED})
    
    return {"message": "Campaign paused", "campaign_id": campaign_id}


@app.get("/api/campaigns/{campaign_id}/emails", response_model=EmailLogsResponse, tags=["Campaigns"])
async def get_campaign_emails(campaign_id: str, limit: int = 100, user: dict = Depends(get_current_user)):
    """Get email logs for a campaign."""
    campaign = await get_campaign_by_id(campaign_id)
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
        
    # Security Check
    if campaign.get("user_id") and campaign.get("user_id") != user.get("sub"):
         raise HTTPException(status_code=403, detail="Not authorized to view logs")
    
    logs = await get_email_logs_by_campaign(campaign_id, limit=limit)
    
    return EmailLogsResponse(
        emails=[EmailLogResponse(**log) for log in logs],
        total=len(logs)
    )


# ============================================================================
# Campaign Management Endpoints
# ============================================================================

@app.post("/api/campaigns", response_model=CreateCampaignResponse, tags=["Campaigns"])
async def create_new_campaign(request: CreateCampaignRequest, user: dict = Depends(get_current_user)):
    """
    Create a new email campaign from an existing job's leads.
    """
    # Verify job exists and is completed
    job = await get_job_by_id(request.job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    # Security Check
    if job.get("user_id") and job.get("user_id") != user.get("sub"):
         raise HTTPException(status_code=403, detail="Not authorized to access this job")
    
    if job.get("status") != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Job must be completed to create campaign. Current status: {job.get('status')}"
        )
    
    # Get total leads count from job
    total_leads = job.get("leads_count", 0)
    
    if total_leads == 0:
        raise HTTPException(status_code=400, detail="Job has no leads to campaign")
    
    # Determine initial status
    if request.scheduled_at:
        status = CampaignStatus.SCHEDULED
    else:
        status = CampaignStatus.RUNNING
    
    # Create campaign
    campaign_data = {
        "user_id": user.get("sub"), # Storing User ID
        "job_id": request.job_id,
        "name": request.name,
        "status": status,
        "total_leads": total_leads,
        "daily_limit": request.daily_limit,
        "scheduled_at": request.scheduled_at,
        "leads_csv_path": f"data/exports/{request.job_id}.csv",  # Path to CSV
    }
    
    campaign_id = await create_campaign(campaign_data)
    
    return CreateCampaignResponse(
        campaign_id=campaign_id,
        status=status,
        total_leads=total_leads,
        message=f"Campaign '{request.name}' created successfully"
    )


@app.get("/api/campaigns/{campaign_id}", response_model=CampaignResponse, tags=["Campaigns"])
async def get_campaign(campaign_id: str, user: dict = Depends(get_current_user)):
    """Get campaign details and metrics."""
    campaign = await get_campaign_by_id(campaign_id)
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
        
    # Security Check
    if campaign.get("user_id") and campaign.get("user_id") != user.get("sub"):
         raise HTTPException(status_code=403, detail="Not authorized to view this campaign")
    
    return CampaignResponse(**campaign)


@app.get("/api/campaigns", response_model=CampaignListResponse, tags=["Campaigns"])
async def list_campaigns(limit: int = 50, user: dict = Depends(get_current_user)):
    """List all campaigns for current user."""
    # TODO: Update DB function to filter by user_id
    campaigns = await get_all_campaigns(limit=limit)
    
    # Filter in memory for now
    user_campaigns = [c for c in campaigns if c.get("user_id") == user.get("sub") or not c.get("user_id")]
    
    return CampaignListResponse(
        campaigns=[CampaignResponse(**c) for c in user_campaigns],
        total=len(user_campaigns)
    )


@app.post("/api/campaigns/{campaign_id}/start", tags=["Campaigns"])
async def start_campaign(campaign_id: str):
    """Start or resume a campaign."""
    campaign = await get_campaign_by_id(campaign_id)
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    if campaign["status"] not in [CampaignStatus.DRAFT, CampaignStatus.PAUSED, CampaignStatus.SCHEDULED]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot start campaign with status: {campaign['status']}"
        )
    
    await update_campaign(campaign_id, {"status": CampaignStatus.RUNNING})
    
    return {"message": "Campaign started", "campaign_id": campaign_id}


@app.post("/api/campaigns/{campaign_id}/pause", tags=["Campaigns"])
async def pause_campaign(campaign_id: str):
    """Pause a running campaign."""
    campaign = await get_campaign_by_id(campaign_id)
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    if campaign["status"] != CampaignStatus.RUNNING:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot pause campaign with status: {campaign['status']}"
        )
    
    await update_campaign(campaign_id, {"status": CampaignStatus.PAUSED})
    
    return {"message": "Campaign paused", "campaign_id": campaign_id}


@app.get("/api/campaigns/{campaign_id}/emails", response_model=EmailLogsResponse, tags=["Campaigns"])
async def get_campaign_emails(campaign_id: str, limit: int = 100):
    """Get email logs for a campaign."""
    campaign = await get_campaign_by_id(campaign_id)
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    logs = await get_email_logs_by_campaign(campaign_id, limit=limit)
    
    return EmailLogsResponse(
        emails=[EmailLogResponse(**log) for log in logs],
        total=len(logs)
    )


# ============================================================================
# Email Tracking Webhooks
# ============================================================================

@app.get("/webhooks/email/open", tags=["Webhooks"])
async def track_email_open(tracking_id: str):
    """
    Track email open via 1x1 pixel.
    Returns a transparent 1x1 GIF.
    """
    from datetime import datetime
    from .database import update_email_log_by_tracking_id
    
    # Update email log
    await update_email_log_by_tracking_id(tracking_id, {"opened_at": datetime.utcnow()})
    
    # TODO: Increment campaign opens counter
    # We'll need to get the campaign_id from the email_log first
    
    # Return 1x1 transparent GIF
    from fastapi.responses import Response
    return Response(
        content=bytes.fromhex('47494638396101000100800000000000ffffff21f90401000000002c00000000010001000002024401003b'),
        media_type="image/gif"
    )


@app.get("/webhooks/email/click/{tracking_id}", tags=["Webhooks"])
async def track_email_click(tracking_id: str, url: str):
    """
    Track email link click and redirect to original URL.
    """
    from datetime import datetime
    from fastapi.responses import RedirectResponse
    from .database import update_email_log_by_tracking_id
    
    # Update email log
    await update_email_log_by_tracking_id(tracking_id, {"clicked_at": datetime.utcnow()})
    
    # TODO: Increment campaign clicks counter
    
    # Redirect to original URL
    return RedirectResponse(url=url)


# ============================================================================
# Development Runner
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
