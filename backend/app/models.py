"""
Pydantic Models for API requests and responses.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    """Possible job statuses."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class CampaignStatus(str, Enum):
    """Possible campaign statuses."""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


# ============================================================================
# Request Models
# ============================================================================


class SearchMode(str, Enum):
    """Available search modes."""
    LOCAL = "local"
    PEOPLE = "people"
    B2B = "b2b"


class StartJobRequest(BaseModel):
    """Request body for starting a new job."""
    niche: str = Field(..., min_length=1, max_length=100, description="Business niche to search")
    location: str = Field(..., min_length=1, max_length=200, description="Location to search")
    max_results: Optional[int] = Field(50, ge=10, le=200, description="Maximum results to fetch")
    mode: SearchMode = Field(SearchMode.LOCAL, description="Search strategy to use")


# ============================================================================
# Response Models
# ============================================================================

class JobResponse(BaseModel):
    """Response model for a single job."""
    id: str
    status: JobStatus
    niche: str
    location: str
    max_results: int = 50
    result_url: Optional[str] = None
    error_message: Optional[str] = None
    leads_count: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class StartJobResponse(BaseModel):
    """Response for job creation."""
    job_id: str
    status: JobStatus
    message: str


class JobListResponse(BaseModel):
    """Response for listing all jobs."""
    jobs: list[JobResponse]
    total: int


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    database: str


# ============================================================================
# Campaign Models
# ============================================================================

class CreateCampaignRequest(BaseModel):
    """Request body for creating a new campaign."""
    job_id: str = Field(..., description="ID of the job to create campaign from")
    name: str = Field(..., min_length=1, max_length=200, description="Campaign name")
    daily_limit: int = Field(30, ge=1, le=500, description="Maximum emails to send per day")
    scheduled_at: Optional[datetime] = Field(None, description="When to start the campaign (null = start immediately)")


class CampaignResponse(BaseModel):
    """Response model for a campaign."""
    id: str
    job_id: str
    name: str
    status: CampaignStatus
    total_leads: int
    emails_sent: int = 0
    opens: int = 0
    clicks: int = 0
    replies: int = 0
    daily_limit: int
    created_at: datetime
    scheduled_at: Optional[datetime] = None
    last_sent_at: Optional[datetime] = None
    updated_at: datetime
    
    # Computed metrics
    open_rate: Optional[float] = None
    click_rate: Optional[float] = None
    reply_rate: Optional[float] = None

    class Config:
        from_attributes = True


class CreateCampaignResponse(BaseModel):
    """Response for campaign creation."""
    campaign_id: str
    status: CampaignStatus
    total_leads: int
    message: str


class CampaignListResponse(BaseModel):
    """Response for listing all campaigns."""
    campaigns: list[CampaignResponse]
    total: int


class EmailLogResponse(BaseModel):
    """Response model for an individual email log."""
    id: str
    campaign_id: str
    lead_name: str
    lead_email: str
    subject: str
    sent_at: datetime
    opened_at: Optional[datetime] = None
    clicked_at: Optional[datetime] = None
    replied_at: Optional[datetime] = None
    bounce: bool = False
    error: Optional[str] = None
    tracking_id: str

    class Config:
        from_attributes = True


class EmailLogsResponse(BaseModel):
    """Response for listing email logs."""
    emails: list[EmailLogResponse]
    total: int
