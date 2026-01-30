# SOP: Email Campaigns

**Goal**: Automate email outreach to generated leads with tracking and analytics.

## Inputs
- **Campaign Configuration**: Name, daily send limit, scheduled start time
- **Leads CSV**: Path to final leads file from completed job
- **Email Templates**: Already embedded in leads CSV (`email_template` column)

## Tools
- `backend/app/main.py` (Campaign API endpoints)
- `engine/execution/email_sender.py` (Individual email sending)
- `engine/execution/campaign_scheduler.py` (Background campaign processor)
- **SendGrid API**: Email delivery service

## Process

### Campaign Creation
1. User creates campaign via POST `/api/campaigns`
2. System validates:
   - Job exists and is completed
   - Job has leads (leads_count > 0)
3. Campaign created with status:
   - `running` if scheduled_at is null (start immediately)
   - `scheduled` if scheduled_at is in the future

### Campaign Processing (Automated)
1. **Scheduler runs** (cron job, every hour)
2. Query database for campaigns with status `running` OR `scheduled` (if scheduled_at <= now)
3. For each campaign:
   - Check emails sent today vs daily_limit
   - Calculate remaining quota
   - If quota exhausted, skip campaign
4. Load unsent leads from CSV:
   - Cross-reference with email_logs to find already sent
   - Sort by quality_score (highest first)
5. Send emails up to daily quota:
   - Call `email_sender.py` for each lead
   - Insert tracking pixel for open tracking
   - Wrap all links for click tracking
   - Log result to email_logs collection
   - Increment campaign.emails_sent counter
6. If all leads sent, mark campaign as `completed`

### Email Tracking
1. **Open tracking**:
   - 1x1 transparent GIF embedded in email
   - When loaded, hits GET `/webhooks/email/open?tracking_id=xxx`
   - Updates email_log.opened_at
   - Increments campaign.opens counter

2. **Click tracking**:
   - All links wrapped with redirect URL
   - Original: `https://example.com`
   - Wrapped: `https://api.yourdomain.com/webhooks/email/click/TRACKING_ID?url=https%3A%2F%2Fexample.com`
   - On click, updates email_log.clicked_at
   - Redirects to original URL

## Output
- **Email Logs**: Individual send records in `email_logs` collection
- **Campaign Metrics**: Real-time stats (sent, opens, clicks, replies)
- **Analytics**: Open rate, click rate, reply rate

## Quality Gates
- **Before creating campaign**: Verify job is completed and has leads
- **Before sending email**: Verify lead has valid email address
- **Daily limit enforcement**: Respect campaign.daily_limit to avoid spam
- **Error handling**: Log failed sends but don't crash; continue with next lead

## Edge Cases
- **SendGrid API failure**: Log error, continue with next lead
- **Invalid email address**: Skip lead, log as invalid
- **Daily limit reached mid-processing**: Stop sending, resume next day
- **Campaign paused**: Scheduler skips it, does not send
- **Duplicate tracking**: Same tracking_id should not update metrics twice (idempotent)

## Rate Limiting
**Default**: 30 emails/day per campaign (configurable)

**Rationale**: 
- Avoid triggering spam filters
- Maintain domain reputation
- Gradual warm-up for new sending domains

**Recommended limits**:
- New domain (first 2 weeks): 10-20/day
- Warmed domain (1 month+): 50-100/day
- Established domain: 100-200/day

## Monitoring
- Track email_logs for errors
- Monitor campaign open_rate (healthy: 20-50%)
- Monitor bounce rate (healthy: <5%)
- If bounce rate > 10%, pause campaign and alert user
