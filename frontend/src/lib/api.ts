/**
 * API Client for The Bridge Backend
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Get authentication headers with Clerk token
 */
async function getAuthHeaders(): Promise<HeadersInit> {
    const headers: HeadersInit = {
        'Content-Type': 'application/json',
    };

    // Get token from Clerk (client-side only)
    if (typeof window !== 'undefined') {
        try {
            const clerk = (window as any).Clerk;
            if (clerk?.session) {
                const token = await clerk.session.getToken();
                if (token) {
                    headers['Authorization'] = `Bearer ${token}`;
                }
            }
        } catch (error) {
            console.warn('Failed to get Clerk token:', error);
        }
    }

    return headers;
}


export interface Job {
    id: string;
    status: 'pending' | 'processing' | 'completed' | 'failed';
    niche: string;
    location: string;
    max_results: number;
    result_url: string | null;
    error_message: string | null;
    leads_count: number | null;
    created_at: string;
    updated_at: string;
}

export interface StartJobRequest {
    niche: string;
    location: string;
    max_results?: number;
    mode?: 'local' | 'people' | 'b2b';
}

export interface StartJobResponse {
    job_id: string;
    status: string;
    message: string;
}

export interface JobListResponse {
    jobs: Job[];
    total: number;
}

/**
 * Start a new lead generation job
 */
export async function startJob(request: StartJobRequest): Promise<StartJobResponse> {
    const response = await fetch(`${API_URL}/api/start-job`, {
        method: 'POST',
        headers: await getAuthHeaders(),
        body: JSON.stringify(request),
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(error.detail || 'Failed to start job');
    }

    return response.json();
}

/**
 * Get a specific job by ID
 */
export async function getJob(jobId: string): Promise<Job> {
    const response = await fetch(`${API_URL}/api/job/${jobId}`, {
        headers: await getAuthHeaders(),
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(error.detail || 'Failed to get job');
    }

    return response.json();
}

/**
 * Get all jobs
 */
export async function getJobs(limit: number = 50): Promise<JobListResponse> {
    const response = await fetch(`${API_URL}/api/jobs?limit=${limit}`, {
        headers: await getAuthHeaders(),
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(error.detail || 'Failed to get jobs');
    }

    return response.json();
}

/**
 * Get download URL for a completed job
 */
export function getDownloadUrl(jobId: string): string {
    return `${API_URL}/api/download/${jobId}`;
}

/**
 * Format relative time
 */
export function formatRelativeTime(dateString: string): string {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} min ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
}

// ============================================================================
// Campaign Types
// ============================================================================

export interface Campaign {
    id: string;
    job_id: string;
    name: string;
    status: 'draft' | 'scheduled' | 'running' | 'paused' | 'completed' | 'failed';
    total_leads: number;
    emails_sent: number;
    opens: number;
    clicks: number;
    replies: number;
    daily_limit: number;
    created_at: string;
    scheduled_at: string | null;
    last_sent_at: string | null;
    updated_at: string;
    open_rate: number | null;
    click_rate: number | null;
    reply_rate: number | null;
}

export interface CreateCampaignRequest {
    job_id: string;
    name: string;
    daily_limit?: number;
    scheduled_at?: string | null;
}

export interface CreateCampaignResponse {
    campaign_id: string;
    status: string;
    total_leads: number;
    message: string;
}

export interface CampaignListResponse {
    campaigns: Campaign[];
    total: number;
}

export interface EmailLog {
    id: string;
    campaign_id: string;
    lead_name: string;
    lead_email: string;
    subject: string;
    sent_at: string;
    opened_at: string | null;
    clicked_at: string | null;
    replied_at: string | null;
    bounce: boolean;
    error: string | null;
    tracking_id: string;
}

export interface EmailLogsResponse {
    emails: EmailLog[];
    total: number;
}

// ============================================================================
// Campaign API Functions
// ============================================================================

/**
 * Create a new campaign
 */
export async function createCampaign(request: CreateCampaignRequest): Promise<CreateCampaignResponse> {
    const response = await fetch(`${API_URL}/api/campaigns`, {
        method: 'POST',
        headers: await getAuthHeaders(),
        body: JSON.stringify(request),
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(error.detail || 'Failed to create campaign');
    }

    return response.json();
}

/**
 * Get a specific campaign by ID
 */
export async function getCampaign(campaignId: string): Promise<Campaign> {
    const response = await fetch(`${API_URL}/api/campaigns/${campaignId}`, {
        headers: await getAuthHeaders(),
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(error.detail || 'Failed to get campaign');
    }

    return response.json();
}

/**
 * Get all campaigns
 */
export async function getCampaigns(limit: number = 50): Promise<CampaignListResponse> {
    const response = await fetch(`${API_URL}/api/campaigns?limit=${limit}`, {
        headers: await getAuthHeaders(),
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(error.detail || 'Failed to get campaigns');
    }

    return response.json();
}

/**
 * Start or resume a campaign
 */
export async function startCampaign(campaignId: string): Promise<void> {
    const response = await fetch(`${API_URL}/api/campaigns/${campaignId}/start`, {
        method: 'POST',
        headers: await getAuthHeaders(),
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(error.detail || 'Failed to start campaign');
    }
}

/**
 * Pause a running campaign
 */
export async function pauseCampaign(campaignId: string): Promise<void> {
    const response = await fetch(`${API_URL}/api/campaigns/${campaignId}/pause`, {
        method: 'POST',
        headers: await getAuthHeaders(),
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(error.detail || 'Failed to pause campaign');
    }
}

/**
 * Get email logs for a campaign
 */
export async function getCampaignEmails(
    campaignId: string,
    limit: number = 100
): Promise<EmailLogsResponse> {
    const response = await fetch(`${API_URL}/api/campaigns/${campaignId}/emails?limit=${limit}`, {
        headers: await getAuthHeaders(),
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(error.detail || 'Failed to get campaign emails');
    }

    return response.json();
}

/**
 * Format percentage
 */
export function formatPercentage(value: number | null): string {
    if (value === null || value === undefined) return '0%';
    return `${value.toFixed(1)}%`;
}
