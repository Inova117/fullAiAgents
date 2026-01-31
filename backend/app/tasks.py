"""
Background Tasks for Pipeline Processing.
Uses FastAPI BackgroundTasks for async job processing.
"""

import os
import subprocess
import sys
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from .database import update_job, get_job_by_id
from .models import JobStatus

# Load environment variables
load_dotenv()

# Configuration
ENGINE_PATH = Path(os.getenv("ENGINE_PATH", "../engine")).resolve()
EXPORTS_DIR = Path(__file__).parent.parent.parent / "data" / "exports"


async def process_pipeline_job(
    job_id: str,
    niche: str,
    location: str,
    max_results: int = 50,
    mode: str = "local"
) -> None:
    """
    Background task to run the lead generation pipeline.
    
    This function:
    1. Updates job status to 'processing'
    2. Runs the pipeline orchestrator
    3. Copies the result to the exports directory
    4. Updates job status to 'completed' or 'failed'
    """
    print(f"[TASK] Starting pipeline job: {job_id}")
    print(f"[TASK] Niche: {niche}, Location: {location}")
    
    # Update status to processing
    await update_job(job_id, {"status": JobStatus.PROCESSING})
    
    # Prepare paths
    pipeline_script = ENGINE_PATH / "run_pipeline.py"
    engine_env_file = ENGINE_PATH / ".env"
    
    if not pipeline_script.exists():
        error_msg = f"Pipeline script not found: {pipeline_script}"
        print(f"[TASK ERROR] {error_msg}")
        await update_job(job_id, {
            "status": JobStatus.FAILED,
            "error_message": error_msg
        })
        return
    
    # Prepare environment
    env = os.environ.copy()
    
    # Load engine .env if exists
    if engine_env_file.exists():
        from dotenv import dotenv_values
        engine_env = dotenv_values(engine_env_file)
        env.update(engine_env)
    
    # Build command
    cmd = [
        sys.executable,
        str(pipeline_script),
        "--niche", niche,
        "--location", location,
        "--job-id", job_id[:8]  # Use first 8 chars of job_id for file naming
    ]
    
    print(f"[TASK] Running command: {' '.join(cmd)}")
    
    try:
        # Run the pipeline
        result = subprocess.run(
            cmd,
            env=env,
            cwd=str(ENGINE_PATH),
            capture_output=True,
            text=True,
            timeout=1800  # 30 minute timeout
        )
        
        # Log output
        if result.stdout:
            for line in result.stdout.strip().split("\n")[:50]:  # Limit log lines
                print(f"[PIPELINE] {line}")
        
        if result.returncode != 0:
            error_msg = result.stderr[:500] if result.stderr else "Pipeline execution failed"
            print(f"[TASK ERROR] Pipeline failed: {error_msg}")
            await update_job(job_id, {
                "status": JobStatus.FAILED,
                "error_message": error_msg
            })
            return
        
        # Find the output file
        output_file = ENGINE_PATH / "data" / f"final_leads_{job_id[:8]}.csv"
        
        if not output_file.exists():
            error_msg = f"Output file not found: {output_file}"
            print(f"[TASK ERROR] {error_msg}")
            await update_job(job_id, {
                "status": JobStatus.FAILED,
                "error_message": error_msg
            })
            return
        
        # Copy to exports directory
        EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
        export_file = EXPORTS_DIR / f"{job_id}.csv"
        shutil.copy(output_file, export_file)
        
        # Count leads
        leads_count = 0
        try:
            with open(export_file, "r") as f:
                leads_count = sum(1 for _ in f) - 1  # Subtract header
        except Exception:
            pass
        
        # Update job as completed
        await update_job(job_id, {
            "status": JobStatus.COMPLETED,
            "result_url": f"/api/download/{job_id}",
            "leads_count": leads_count
        })
        
        print(f"[TASK SUCCESS] Job {job_id} completed with {leads_count} leads")
        
    except subprocess.TimeoutExpired:
        error_msg = "Pipeline execution timed out after 30 minutes"
        print(f"[TASK ERROR] {error_msg}")
        await update_job(job_id, {
            "status": JobStatus.FAILED,
            "error_message": error_msg
        })
        
    except Exception as e:
        error_msg = str(e)[:500]
        print(f"[TASK ERROR] Unexpected error: {error_msg}")
        await update_job(job_id, {
            "status": JobStatus.FAILED,
            "error_message": error_msg
        })
