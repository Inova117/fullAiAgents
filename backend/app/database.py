"""
MongoDB Database Connection and Operations.
Uses Motor for async MongoDB operations.
"""

import os
from datetime import datetime
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB connection settings
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "thebridge")

# Global database client
client: Optional[AsyncIOMotorClient] = None
database: Optional[AsyncIOMotorDatabase] = None


async def connect_to_mongodb() -> None:
    """Connect to MongoDB."""
    global client, database
    
    print(f"[DB] Connecting to MongoDB at {MONGODB_URL}...")
    
    client = AsyncIOMotorClient(MONGODB_URL)
    database = client[DATABASE_NAME]
    
    # Test connection
    try:
        await client.admin.command("ping")
        print("[DB] Successfully connected to MongoDB!")
    except Exception as e:
        print(f"[DB] Failed to connect to MongoDB: {e}")
        raise


async def close_mongodb_connection() -> None:
    """Close MongoDB connection."""
    global client
    
    if client:
        client.close()
        print("[DB] MongoDB connection closed.")


def get_database() -> AsyncIOMotorDatabase:
    """Get the database instance."""
    if database is None:
        raise RuntimeError("Database not initialized. Call connect_to_mongodb() first.")
    return database


async def get_jobs_collection():
    """Get the jobs collection."""
    db = get_database()
    return db.jobs


# ============================================================================
# Job CRUD Operations
# ============================================================================

async def create_job(job_data: dict) -> str:
    """
    Create a new job in the database.
    
    Returns the job ID as a string.
    """
    collection = await get_jobs_collection()
    
    job_data["created_at"] = datetime.utcnow()
    job_data["updated_at"] = datetime.utcnow()
    
    result = await collection.insert_one(job_data)
    return str(result.inserted_id)


async def get_job_by_id(job_id: str) -> Optional[dict]:
    """Get a job by its ID."""
    from bson import ObjectId
    
    collection = await get_jobs_collection()
    
    try:
        job = await collection.find_one({"_id": ObjectId(job_id)})
        if job:
            job["id"] = str(job.pop("_id"))
        return job
    except Exception:
        return None


async def update_job(job_id: str, update_data: dict) -> bool:
    """Update a job by its ID."""
    from bson import ObjectId
    
    collection = await get_jobs_collection()
    
    update_data["updated_at"] = datetime.utcnow()
    
    try:
        result = await collection.update_one(
            {"_id": ObjectId(job_id)},
            {"$set": update_data}
        )
        return result.modified_count > 0
    except Exception:
        return False


async def get_all_jobs(limit: int = 50) -> list[dict]:
    """Get all jobs, sorted by creation date (newest first)."""
    collection = await get_jobs_collection()
    
    cursor = collection.find().sort("created_at", -1).limit(limit)
    jobs = []
    
    async for job in cursor:
        job["id"] = str(job.pop("_id"))
        jobs.append(job)
    
    return jobs


# ============================================================================
# Campaign Collections
# ============================================================================

async def get_campaigns_collection():
    """Get the campaigns collection."""
    db = get_database()
    return db.campaigns


async def get_email_logs_collection():
    """Get the email_logs collection."""
    db = get_database()
    return db.email_logs


# ============================================================================
# Campaign CRUD Operations
# ============================================================================

async def create_campaign(campaign_data: dict) -> str:
    """
    Create a new campaign in the database.
    
    Returns the campaign ID as a string.
    """
    collection = await get_campaigns_collection()
    
    campaign_data["created_at"] = datetime.utcnow()
    campaign_data["updated_at"] = datetime.utcnow()
    campaign_data["emails_sent"] = 0
    campaign_data["opens"] = 0
    campaign_data["clicks"] = 0
    campaign_data["replies"] = 0
    
    result = await collection.insert_one(campaign_data)
    return str(result.inserted_id)


async def get_campaign_by_id(campaign_id: str) -> Optional[dict]:
    """Get a campaign by its ID."""
    from bson import ObjectId
    
    collection = await get_campaigns_collection()
    
    try:
        campaign = await collection.find_one({"_id": ObjectId(campaign_id)})
        if campaign:
            campaign["id"] = str(campaign.pop("_id"))
            
            # Calculate metrics
            if campaign["emails_sent"] > 0:
                campaign["open_rate"] = round((campaign["opens"] / campaign["emails_sent"]) * 100, 1)
                campaign["click_rate"] = round((campaign["clicks"] / campaign["emails_sent"]) * 100, 1)
                campaign["reply_rate"] = round((campaign["replies"] / campaign["emails_sent"]) * 100, 1)
            else:
                campaign["open_rate"] = 0.0
                campaign["click_rate"] = 0.0
                campaign["reply_rate"] = 0.0
                
        return campaign
    except Exception:
        return None


async def update_campaign(campaign_id: str, update_data: dict) -> bool:
    """Update a campaign by its ID."""
    from bson import ObjectId
    
    collection = await get_campaigns_collection()
    
    update_data["updated_at"] = datetime.utcnow()
    
    try:
        result = await collection.update_one(
            {"_id": ObjectId(campaign_id)},
            {"$set": update_data}
        )
        return result.modified_count > 0
    except Exception:
        return False


async def get_all_campaigns(limit: int = 50) -> list[dict]:
    """Get all campaigns, sorted by creation date (newest first)."""
    collection = await get_campaigns_collection()
    
    cursor = collection.find().sort("created_at", -1).limit(limit)
    campaigns = []
    
    async for campaign in cursor:
        campaign["id"] = str(campaign.pop("_id"))
        
        # Calculate metrics
        if campaign["emails_sent"] > 0:
            campaign["open_rate"] = round((campaign["opens"] / campaign["emails_sent"]) * 100, 1)
            campaign["click_rate"] = round((campaign["clicks"] / campaign["emails_sent"]) * 100, 1)
            campaign["reply_rate"] = round((campaign["replies"] / campaign["emails_sent"]) * 100, 1)
        else:
            campaign["open_rate"] = 0.0
            campaign["click_rate"] = 0.0
            campaign["reply_rate"] = 0.0
            
        campaigns.append(campaign)
    
    return campaigns


async def increment_campaign_metric(campaign_id: str, metric: str, amount: int = 1) -> bool:
    """
    Increment a campaign metric (emails_sent, opens, clicks, replies).
    
    Args:
        campaign_id: ID of the campaign
        metric: Name of the metric to increment
        amount: Amount to increment by (default 1)
    """
    from bson import ObjectId
    
    collection = await get_campaigns_collection()
    
    try:
        result = await collection.update_one(
            {"_id": ObjectId(campaign_id)},
            {
                "$inc": {metric: amount},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        return result.modified_count > 0
    except Exception:
        return False


# ============================================================================
# Email Log Operations
# ============================================================================

async def create_email_log(email_log_data: dict) -> str:
    """
    Create a new email log entry.
    
    Returns the log ID as a string.
    """
    collection = await get_email_logs_collection()
    
    result = await collection.insert_one(email_log_data)
    return str(result.inserted_id)


async def get_email_logs_by_campaign(campaign_id: str, limit: int = 100) -> list[dict]:
    """Get all email logs for a campaign."""
    from bson import ObjectId
    
    collection = await get_email_logs_collection()
    
    try:
        cursor = collection.find({"campaign_id": campaign_id}).sort("sent_at", -1).limit(limit)
        logs = []
        
        async for log in cursor:
            log["id"] = str(log.pop("_id"))
            logs.append(log)
        
        return logs
    except Exception:
        return []


async def update_email_log_by_tracking_id(tracking_id: str, update_data: dict) -> bool:
    """Update an email log by its tracking ID (for webhooks)."""
    collection = await get_email_logs_collection()
    
    try:
        result = await collection.update_one(
            {"tracking_id": tracking_id},
            {"$set": update_data}
        )
        return result.modified_count > 0
    except Exception:
        return False


async def get_unsent_leads_for_campaign(campaign_id: str, limit: int = 30) -> list[dict]:
    """
    Get leads from a campaign that haven't been sent yet.
    
    This queries email_logs to find which leads have already been sent,
    then returns leads that are not in that list.
    """
    # This will be implemented when we have the CSV reading logic
    # For now, return empty list
    return []
