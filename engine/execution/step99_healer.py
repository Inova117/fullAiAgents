#!/usr/bin/env python3
"""
Step 99: The Healer Agent (Phoenix Architecture)

triggered_by: run_pipeline.py (on failure)
purpose: "Self-Rewriting Code" to fix runtime errors.

Input: --error-log path/to/error_123.json
Output: stdout message, exit code 0 if fixed, 1 if failed.
"""

import argparse
import json
import os
import sys
import difflib
from pathlib import Path

# Try to import openai, but handle if not installed
try:
    from openai import OpenAI
except ImportError:
    print("[HEALER] OpenAI library not installed. Cannot heal.")
    sys.exit(1)

from dotenv import load_dotenv

load_dotenv()

def get_llm_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("[HEALER] OPENAI_API_KEY not found. Skipping auto-heal.")
        return None
    return OpenAI(api_key=api_key)

def read_file(path):
    with open(path, "r") as f:
        return f.read()

def write_file(path, content):
    with open(path, "w") as f:
        f.write(content)

def generate_fix(client, error_details, source_code):
    """Ask LLM to fix the code based on the error."""
    
    prompt = f"""
    You are an expert Python Debugger Agent.
    
    I have a python script that crashed.
    
    ERROR DETAILS:
    ----------------
    Script: {error_details['script']}
    Arguments: {error_details['args']}
    Return Code: {error_details['return_code']}
    STDERR:
    {error_details['stderr']}
    ----------------
    
    SOURCE CODE:
    ----------------
    {source_code}
    ----------------
    
    TASK:
    Analyze the error and the source code.
    Fix the bug.
    Return ONLY the full corrected python code.
    Do not use markdown blocks.
    Do not add explanations.
    Just the raw python code.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",  # Or gpt-4-turbo
            messages=[
                {"role": "system", "content": "You are a helpful coding assistant. Return only raw code."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        print(f"[HEALER] LLM Error: {e}")
        return None

def clean_llm_output(code):
    """Remove markdown formatting if present."""
    if code.startswith("```python"):
        code = code.replace("```python", "", 1)
    if code.startswith("```"):
        code = code.replace("```", "", 1)
    if code.endswith("```"):
        code = code.rsplit("```", 1)[0]
    return code.strip()

def main():
    parser = argparse.ArgumentParser(description="Step 99: Healer Agent")
    parser.add_argument("--error-log", required=True, help="Path to error JSON log")
    
    args = parser.parse_args()
    
    # 1. Load Error Log
    error_path = Path(args.error_log)
    if not error_path.exists():
        print(f"[HEALER] Error log not found: {error_path}")
        sys.exit(1)
        
    with open(error_path, "r") as f:
        error_data = json.load(f)
        
    script_name = error_data.get("script")
    if not script_name:
        print("[HEALER] No script name in error log")
        sys.exit(1)
        
    # 2. Locate Source File
    # Assuming script is in the same directory as this healer script or relative to engine
    execution_dir = Path(__file__).parent
    source_path = execution_dir / script_name
    
    if not source_path.exists():
        print(f"[HEALER] Source file not found: {source_path}")
        sys.exit(1)
        
    print(f"[HEALER] Analyzing failure in: {script_name}")
    print(f"[HEALER] Error: {error_data.get('stderr')[:200]}...")
    
    # 3. Check for API Key
    try:
        client = get_llm_client()
        if client is None:
             print("[HEALER] No AI Brain detected. Skipping 'Self-Rewrite' capability.")
             # We exit with 1 to indicate "Not Fixed", but prompt is friendly
             sys.exit(1)
    except SystemExit:
        sys.exit(1)
    except Exception as e:
        print(f"[HEALER] Error initializing AI: {e}")
        sys.exit(1)
        
    # 4. Read Source
    original_code = read_file(source_path)
    
    # 5. Generate Fix
    print("[HEALER] Asking AI for a fix...")
    start_token = "Corrected Code:" # meaningless debug
    
    fixed_code_raw = generate_fix(client, error_data, original_code)
    
    if not fixed_code_raw:
        print("[HEALER] AI failed to generate a fix.")
        sys.exit(1)
        
    fixed_code = clean_llm_output(fixed_code_raw)
    
    # 6. Safety Check (Basic)
    if not fixed_code or len(fixed_code) < 50:
         print("[HEALER] Generated code seems invalid (too short). Aborting.")
         sys.exit(1)
         
    # 7. Apply Patch
    # Backup first
    backup_path = source_path.with_suffix(".py.bak")
    write_file(backup_path, original_code)
    print(f"[HEALER] Backup saved to {backup_path.name}")
    
    write_file(source_path, fixed_code)
    print(f"[HEALER] 🩹 Patch applied to {script_name}!")
    
    sys.exit(0)

if __name__ == "__main__":
    main()
