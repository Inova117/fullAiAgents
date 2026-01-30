#!/usr/bin/env python3
"""
The Bridge - Pipeline Orchestrator (Layer 2: The Manager)

This script orchestrates the entire lead generation pipeline:
1. Search (Apify Google Maps)
2. Enrich (Website scraping)
3. Template (Pain point mapping)
4. Validate (Pydantic validation & deduplication)

Features:
- Sequential execution with subprocess
- Quality gates (fail-fast on errors)
- Strict logging
- File-based state transfer
"""

import argparse
import os
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
EXECUTION_DIR = Path(__file__).parent / "execution"
TMP_DIR = Path(__file__).parent / "tmp"
DATA_DIR = Path(__file__).parent / "data"


def log(stage: str, message: str, level: str = "INFO") -> None:
    """Print formatted log message."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    prefix = {
        "INFO": "",
        "SUCCESS": "✓",
        "ERROR": "✗",
        "WARNING": "⚠",
    }.get(level, "")
    print(f"[{timestamp}] [{stage}] {prefix} {message}")


def run_step(
    script_name: str,
    args: list[str],
    stage_name: str,
    env: dict = None
) -> bool:
    """
    Run a pipeline step as a subprocess.
    
    Returns: True if successful, False otherwise
    """
    script_path = EXECUTION_DIR / script_name
    
    if not script_path.exists():
        log(stage_name, f"Script not found: {script_path}", "ERROR")
        return False
    
    cmd = [sys.executable, str(script_path)] + args
    
    log(stage_name, f"Running: {' '.join(cmd)}")
    
    # Merge environment
    run_env = os.environ.copy()
    if env:
        run_env.update(env)
    
    try:
        result = subprocess.run(
            cmd,
            env=run_env,
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout per step
        )
        
        # Print stdout
        if result.stdout:
            for line in result.stdout.strip().split("\n"):
                if line:
                    print(f"    {line}")
        
        # Check for errors
        if result.returncode != 0:
            log(stage_name, f"Step failed with exit code {result.returncode}", "ERROR")
            if result.stderr:
                for line in result.stderr.strip().split("\n"):
                    if line:
                        print(f"    ERROR: {line}")
            
            # --- SELF HEALING LOGIC ---
            # Extract job_id from args if possible (it's usually passed)
            # We need job_id to name the error log
            # In run_pipeline, we generate a job_id, so we can pass it down if we update run_step signature
            # For now, let's try to find it in the output dir path or similar, OR just use 'unknown' if not present
            job_id = "unknown"
            # Attempt to parse job_id from output filename args if present
            for arg in args:
                if "stage" in arg and ".csv" in arg:
                    # e.g. /path/to/stage1_maps_12345678.csv
                    parts = arg.split("_")
                    if parts:
                        last_part = parts[-1].replace(".csv", "")
                        if len(last_part) == 8: # basic heuristic
                            job_id = last_part
                            break
            
            log_path = save_error_log(
                job_id=job_id,
                stage_name=stage_name,
                script_name=script_name,
                args=args,
                stdout=result.stdout,
                stderr=result.stderr,
                return_code=result.returncode
            )
            
            # Try to heal
            if trigger_healer(job_id, log_path):
                log(stage_name, "🔄 Retrying step after Healer patch...", "INFO")
                # Recursive retry (one time only to avoid infinite loops? 
                # For safety, let's just return False here and let the orchestrator decide, 
                # OR we can retry once using a simple flag if we update signature.
                # Ideally, run_step should support retry.
                # For this implementation, we will try running the command ONE more time immediately.
                
                log(stage_name, "Re-running patched command...")
                retry_result = subprocess.run(
                    cmd,
                    env=run_env,
                    capture_output=True,
                    text=True,
                    timeout=600
                )
                
                if retry_result.returncode == 0:
                    log(stage_name, "Step SUCCEEDED after Healer patch! 🩹", "SUCCESS")
                    return True
                else:
                    log(stage_name, "Step FAILED again after patch. Giving up.", "ERROR")
                    return False
            
            return False
        
        return True
        
        return True
        
    except subprocess.TimeoutExpired:
        log(stage_name, "Step timed out after 10 minutes", "ERROR")
        return False
    except Exception as e:
        log(stage_name, f"Step execution error: {str(e)}", "ERROR")
        return False


def save_error_log(job_id: str, stage_name: str, script_name: str, args: list[str], stdout: str, stderr: str, return_code: int):
    """Save failure details to a JSON log for the Healer Agent."""
    import json
    
    error_dir = EXECUTION_DIR.parent / "runs" / "errors"
    error_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = error_dir / f"error_{job_id}.json"
    
    error_data = {
        "job_id": job_id,
        "timestamp": datetime.now().isoformat(),
        "stage": stage_name,
        "script": script_name,
        "args": args,
        "return_code": return_code,
        "stdout": stdout,
        "stderr": stderr,
    }
    
    with open(log_file, "w") as f:
        json.dump(error_data, f, indent=2)
        
    log("HEALER", f"Error log saved to: {log_file}", "WARNING")
    return log_file


def trigger_healer(job_id: str, error_log_path: Path):
    """Call the Healer Agent to attempt a fix."""
    log("HEALER", "🚑 Summoning the Healer Agent...", "WARNING")
    
    healer_script = EXECUTION_DIR / "step99_healer.py"
    
    if not healer_script.exists():
        log("HEALER", "Healer script not found. Skipping auto-repair.", "ERROR")
        return False
        
    cmd = [sys.executable, str(healer_script), "--error-log", str(error_log_path)]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        print(result.stdout)
        if result.returncode == 0:
            log("HEALER", "Healer Agent reported SUCCESS. Retrying step...", "SUCCESS")
            return True
        else:
            log("HEALER", "Healer Agent failed to fix the issue.", "ERROR")
            print(result.stderr)
            return False
    except Exception as e:
        log("HEALER", f"Healer execution failed: {e}", "ERROR")
        return False


def validate_output_file(file_path: Path, stage_name: str, min_rows: int = 1) -> bool:
    """
    Quality Gate: Validate that output file exists and has minimum rows.
    """
    if not file_path.exists():
        log(stage_name, f"Output file not found: {file_path}", "ERROR")
        return False
    
    # Check file size
    if file_path.stat().st_size == 0:
        log(stage_name, f"Output file is empty: {file_path}", "ERROR")
        return False
    
    # Count rows (excluding header)
    try:
        with open(file_path, "r") as f:
            row_count = sum(1 for _ in f) - 1  # Subtract header
        
        if row_count < min_rows:
            log(stage_name, f"Output has only {row_count} rows (minimum: {min_rows})", "ERROR")
            return False
        
        log(stage_name, f"Output validated: {row_count} rows", "SUCCESS")
        return True
        
    except Exception as e:
        log(stage_name, f"Error reading output file: {str(e)}", "ERROR")
        return False



def merge_csv_files(file_paths: list[Path], output_path: Path) -> bool:
    """Merge multiple CSV files into one, effectively handling headers."""
    import pandas as pd
    
    combined_df = pd.DataFrame()
    
    for fp in file_paths:
        if fp.exists() and fp.stat().st_size > 0:
            try:
                df = pd.read_csv(fp)
                combined_df = pd.concat([combined_df, df], ignore_index=True)
            except Exception as e:
                print(f"[ERROR] Failed to merge {fp}: {e}")
                
    if combined_df.empty:
        return False
        
    combined_df.to_csv(output_path, index=False)
    return True


def run_pipeline(niche: str, location: str, job_id: str = None, mode: str = "local") -> tuple[bool, str]:
    """
    Run the complete lead generation pipeline with Strategy Dispatcher.
    
    Args:
        mode: Search strategy ("local", "people", "b2b")
    """
    if not job_id:
        job_id = str(uuid.uuid4())[:8]
    
    # Ensure directories exist
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Define file paths
    # Stage 1 might produce multiple files depending on mode
    stage1_unified_output = TMP_DIR / f"stage1_unified_{job_id}.csv"
    stage2_output = TMP_DIR / f"stage2_{job_id}.csv"
    stage3_output = TMP_DIR / f"stage3_{job_id}.csv"
    final_output = DATA_DIR / f"final_leads_{job_id}.csv"
    
    log("PIPELINE", f"Starting pipeline for '{niche}' in '{location}' (Mode: {mode})")
    log("PIPELINE", f"Job ID: {job_id}")
    print("-" * 60)
    
    # ========================================================================
    # STAGE 1: Discovery (Strategy Dispatcher)
    # ========================================================================
    log("STAGE 1", f"Discovery Phase - Mode: {mode.upper()}")
    
    step1_outputs = []
    
    if mode == "local":
        # 1. Google Maps (The Core)
        maps_output = TMP_DIR / f"stage1_maps_{job_id}.csv"
        log("STAGE 1A", "Google Maps Search")
        if run_step("step1_search.py", ["--niche", niche, "--location", location, "--output", str(maps_output)], "STAGE 1A"):
            step1_outputs.append(maps_output)
            
        # 2. Instagram (The Social Layer)
        ig_output = TMP_DIR / f"stage1_instagram_{job_id}.csv"
        log("STAGE 1B", "Instagram Search")
        # Try running IG scraper, but don't fail pipeline if it fails (it's secondary)
        if run_step("step1b_instagram.py", ["--niche", niche, "--location", location, "--output", str(ig_output)], "STAGE 1B"):
            step1_outputs.append(ig_output)
            
    elif mode == "people":
        # Placeholder for LinkedIn
        linkedin_output = TMP_DIR / f"stage1_linkedin_{job_id}.csv"
        log("STAGE 1", "LinkedIn People Search")
        if run_step("step1_linkedin.py", ["--niche", niche, "--location", location, "--output", str(linkedin_output)], "STAGE 1"):
            step1_outputs.append(linkedin_output)
            
    elif mode == "b2b":
        # Placeholder for B2B Web Search
        log("STAGE 1", "B2B Web Search (Not implemented yet)", "WARNING")
        
    else:
        log("PIPELINE", f"Unknown mode: {mode}", "ERROR")
        return False, ""

    # Merge Step 1 outputs
    if not step1_outputs:
        log("STAGE 1", "No leads found in Discovery phase", "ERROR")
        return False, ""
        
    log("STAGE 1", "Merging Discovery results...")
    if not merge_csv_files(step1_outputs, stage1_unified_output):
        log("STAGE 1", "Failed to merge results or no results found", "ERROR")
        return False, ""
        
    log("STAGE 1", f"Unified Discovery Output: {stage1_unified_output}")
    print("-" * 60)
    
    # ========================================================================
    # STAGE 2: Enrich (Website Scraping)
    # ========================================================================
    log("STAGE 2", "Website Enrichment")
    
    success = run_step(
        "step2_enrich.py",
        [
            "--input", str(stage1_unified_output),
            "--output", str(stage2_output),
        ],
        "STAGE 2"
    )
    
    if not success:
        log("STAGE 2", "FAILED - Pipeline terminated", "ERROR")
        return False, ""
    
    if not validate_output_file(stage2_output, "STAGE 2", min_rows=1):
        log("STAGE 2", "Output validation failed - Pipeline terminated", "ERROR")
        return False, ""
    
    print("-" * 60)
    
    # ========================================================================
    # STAGE 3: Template (Pain Point Mapping)
    # ========================================================================
    log("STAGE 3", "Pain Point & Template Generation")
    
    success = run_step(
        "step3_template.py",
        [
            "--input", str(stage2_output),
            "--output", str(stage3_output),
            "--location", location,
        ],
        "STAGE 3"
    )
    
    if not success:
        log("STAGE 3", "FAILED - Pipeline terminated", "ERROR")
        return False, ""
    
    if not validate_output_file(stage3_output, "STAGE 3", min_rows=1):
        log("STAGE 3", "Output validation failed - Pipeline terminated", "ERROR")
        return False, ""
    
    print("-" * 60)
    
    # ========================================================================
    # STAGE 4: Validate (Pydantic Validation & Deduplication)
    # ========================================================================
    log("STAGE 4", "Validation & Deduplication")
    
    success = run_step(
        "step4_validate.py",
        [
            "--input", str(stage3_output),
            "--output", str(final_output),
        ],
        "STAGE 4"
    )
    
    if not success:
        log("STAGE 4", "FAILED - Pipeline terminated", "ERROR")
        return False, ""
    
    if not validate_output_file(final_output, "STAGE 4", min_rows=1):
        log("STAGE 4", "Output validation failed - Pipeline terminated", "ERROR")
        return False, ""
    
    print("-" * 60)
    
    # ========================================================================
    # CLEANUP & SUMMARY
    # ========================================================================
    log("PIPELINE", "COMPLETED SUCCESSFULLY", "SUCCESS")
    log("PIPELINE", f"Final output: {final_output}")
    
    # Count final leads
    try:
        with open(final_output, "r") as f:
            final_count = sum(1 for _ in f) - 1
        log("PIPELINE", f"Total leads generated: {final_count}", "SUCCESS")
    except Exception:
        pass
    
    return True, str(final_output)


def main():
    parser = argparse.ArgumentParser(
        description="The Bridge - Lead Generation Pipeline Orchestrator"
    )
    parser.add_argument(
        "--niche",
        required=True,
        help="Business niche to search (e.g., 'gyms', 'restaurants')"
    )
    parser.add_argument(
        "--location",
        required=True,
        help="Location to search (e.g., 'Madrid, Spain')"
    )
    parser.add_argument(
        "--job-id",
        help="Optional job ID for file naming"
    )
    parser.add_argument(
        "--mode",
        default="local",
        choices=["local", "people", "b2b"],
        help="Search mode strategy"
    )
    
    args = parser.parse_args()
    
    # Validate Apify token is set
    if not os.getenv("APIFY_API_TOKEN"):
        print("[ERROR] APIFY_API_TOKEN environment variable is not set")
        print("Please set it in the .env file or export it")
        sys.exit(1)
    
    success, output_path = run_pipeline(
        niche=args.niche,
        location=args.location,
        job_id=args.job_id,
        mode=args.mode
    )
    
    if not success:
        print("\n[PIPELINE FAILED]")
        sys.exit(1)
    
    print(f"\n[PIPELINE COMPLETED] Output: {output_path}")
    sys.exit(0)


if __name__ == "__main__":
    main()
