#!/usr/bin/env python3
"""
Campaign Scheduler - Background worker for processing email campaigns
Runs periodically (e.g., every hour) to send emails for active campaigns.

This script:
1. Fetches campaigns with status 'running' or 'scheduled' (if scheduled_at <= now)
2. For each campaign, fetches unsent leads (respecting daily_limit)
3. Calls email_sender.py for each lead
4. Updates campaign metrics and email logs in MongoDB
5. Marks campaign as 'completed' when all leads are sent
"""

import argparse
import asyncio
import os
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict

import pandas as pd
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

# Load environment variables
load_dotenv()

# MongoDB connection
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "thebridge")


async def get_running_campaigns(db) -> List[Dict]:
    """
    Get all campaigns that should be running.
    
    Returns campaigns with status='running' OR status='scheduled' and scheduled_at <= now
    """
    now = datetime.utcnow()
    
    cursor = db.campaigns.find({
        "$or": [
            {"status": "running"},
            {"status": "scheduled", "scheduled_at": {"$lte": now}}
        ]
    })
    
    campaigns = []
    async for camp in cursor:
        camp["_id"] = str(camp["_id"])
        campaigns.append(camp)
    
    return campaigns


async def get_sent_emails_today(db, campaign_id: str) -> int:
    """Count how many emails were sent today for this campaign."""
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    count = await db.email_logs.count_documents({
        "campaign_id": campaign_id,
        "sent_at": {"$gte": today_start}
    })
    
    return count


async def get_unsent_leads(db, campaign: Dict) -> List[Dict]:
    """
    Get leads that haven't been sent yet for this campaign.
    
    Reads the CSV file and cross-references with email_logs.
    """
    # Path to leads CSV
    csv_path = Path(campaign["leads_csv_path"])
    
    if not csv_path.exists():
        print(f"[WARNING] CSV file not found: {csv_path}")
        return []
    
    # Load leads from CSV
    df = pd.read_csv(csv_path)
    
    # Get already sent email addresses for this campaign
    cursor = db.email_logs.find(
        {"campaign_id": campaign["_id"]},
        {"lead_email": 1}
    )
    
    sent_emails = set()
    async for log in cursor:
        sent_emails.add(log["lead_email"])
    
    # Filter out already sent
    unsent_leads = []
    for idx, row in df.iterrows():
        email = row.get("email")
        if email and pd.notna(email) and str(email).strip() and email not in sent_emails:
            unsent_leads.append({
                "name": row.get("name", ""),
                "email": email,
                "email_template": row.get("email_template", ""),
                "quality_score": row.get("quality_score", 0)
            })
    
    # Sort by quality score (highest first)
    unsent_leads.sort(key=lambda x: x.get("quality_score", 0), reverse=True)
    
    return unsent_leads


async def send_single_email(lead: Dict, campaign: Dict) -> Dict:
    """
    Send an email to a single lead using email_sender.py
    
    Returns result dict with success status.
    """
    import subprocess
    
    tracking_id = str(uuid.uuid4())
    
    # Extract subject from email template
    email_template = lead["email_template"]
    subject_line = "Quick question"  # Default
    
    if "Subject:" in email_template:
        # Extract subject
        lines = email_template.split("\\n")
        for line in lines:
            if line.startswith("Subject:"):
                subject_line = line.replace("Subject:", "").strip()
                break
    
    # Build command
    cmd = [
        "python3",
        "engine/execution/email_sender.py",
        "--to-email", lead["email"],
        "--to-name", lead["name"],
        "--subject", subject_line,
        "--content", email_template,
        "--tracking-id", tracking_id,
        "--campaign-id", campaign["_id"]
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            check=False
        )
        
        if result.returncode == 0:
            return {
                "success": True,
                "tracking_id": tracking_id,
                "error": None
            }
        else:
            return {
                "success": False,
                "tracking_id": tracking_id,
                "error": result.stderr or "Unknown error"
            }
            
    except Exception as e:
        return {
            "success": False,
            "tracking_id": tracking_id,
            "error": str(e)
        }


async def process_campaign(db, campaign: Dict, dry_run: bool = False):
    """
    Process a single campaign: send emails up to daily limit.
    """
    campaign_id = campaign["_id"]
    daily_limit = campaign.get("daily_limit", 30)
    
    print(f"\n[CAMPAIGN] Processing: {campaign['name']} (ID: {campaign_id})")
    
    # Check how many emails sent today
    sent_today = await get_sent_emails_today(db, campaign_id)
    remaining_today = daily_limit - sent_today
    
    if remaining_today <= 0:
        print(f"[CAMPAIGN] Daily limit reached ({sent_today}/{daily_limit}). Skipping.")
        return
    
    print(f"[CAMPAIGN] Can send {remaining_today} more emails today")
    
    # Get unsent leads
    unsent_leads = await get_unsent_leads(db, campaign)
    
    if not unsent_leads:
        print("[CAMPAIGN] No more unsent leads. Marking as completed.")
        await db.campaigns.update_one(
            {"_id": campaign["_id"]},
            {"$set": {"status": "completed", "updated_at": datetime.utcnow()}}
        )
        return
    
    print(f"[CAMPAIGN] Found {len(unsent_leads)} unsent leads")
    
    # Send up to remaining_today emails
    to_send = unsent_leads[:remaining_today]
    
    print(f"[CAMPAIGN] Sending {len(to_send)} emails...")
    
    for idx, lead in enumerate(to_send, 1):
        if dry_run:
            print(f"  [{idx}/{len(to_send)}] DRY RUN: Would send to {lead['email']}")
            continue
        
        print(f"  [{idx}/{len(to_send)}] Sending to {lead['email']}...")
        
        # Send email
        result = await send_single_email(lead, campaign)
        
        # Log to database
        email_log = {
            "campaign_id": campaign_id,
            "lead_name": lead["name"],
            "lead_email": lead["email"],
            "subject": "Quick question",  # Extract from template
            "sent_at": datetime.utcnow(),
            "tracking_id": result["tracking_id"],
            "bounce": False,
            "error": result.get("error")
        }
        
        await db.email_logs.insert_one(email_log)
        
        # Increment campaign counter
        if result["success"]:
            await db.campaigns.update_one(
                {"_id": campaign_id},
                {
                    "$inc": {"emails_sent": 1},
                    "$set": {
                        "last_sent_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
        
        # Small delay to avoid rate limiting
        await asyncio.sleep(1)
    
    print(f"[CAMPAIGN] Sent {len(to_send)} emails successfully")


async def main():
    parser = argparse.ArgumentParser(description="Campaign scheduler - send queued emails")
    parser.add_argument("--dry-run", action="store_true", help="Don't actually send emails, just log what would be sent")
    
    args = parser.parse_args()
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    
    try:
        # Test connection
        await client.admin.command("ping")
        print("[SCHEDULER] Connected to MongoDB")
        
        # Get running campaigns
        campaigns = await get_running_campaigns(db)
        
        if not campaigns:
            print("[SCHEDULER] No active campaigns to process")
            return
        
        print(f"[SCHEDULER] Found {len(campaigns)} active campaign(s)")
        
        # Process each campaign
        for campaign in campaigns:
            await process_campaign(db, campaign, dry_run=args.dry_run)
        
        print("\n[SCHEDULER] ✓ Completed successfully")
        
    except Exception as e:
        print(f"[SCHEDULER ERROR] {e}")
        sys.exit(1)
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(main())
