#!/usr/bin/env python3
"""
Step 1 (People Mode): LinkedIn Scraper
Uses Actor: dev_fusion/link-scraper (Mass LinkedIn Profile Scraper) or similar.
*Note: Actor IDs change frequently. We will use a reliable search scraper.*

Input: niche (Job Title/Role) + location
Output: stage1_linkedin.csv
"""

import argparse
import os
import sys
from pathlib import Path
from typing import List, Dict

import pandas as pd
from apify_client import ApifyClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def get_apify_client() -> ApifyClient:
    """Initialize Apify client with API token."""
    token = os.getenv("APIFY_API_TOKEN")
    if not token:
        print("[ERROR] APIFY_API_TOKEN not found in environment variables")
        sys.exit(1)
    return ApifyClient(token)


def run_linkedin_scraper(
    client: ApifyClient,
    role: str,
    location: str,
    max_results: int = 50
) -> List[Dict]:
    """
    Run a LinkedIn Search Scraper.
    Since direct LinkedIn scraping is hard, we often use a "Google Search for LinkedIn Profiles" approach
    OR a dedicated LinkedIn Search actor.
    
    We will use a search query approach which is more stable and cheaper than direct profile scraping.
    Actor: apify/google-search-scraper (configured for LinkedIn X-Ray)
    OR specific LinkedIn actor if credentials allowed.
    
    For this implementation, let's use the robust "Google Search" method restricted to linkedin.com/in/
    which effectively finds people without needing personal cookies.
    """
    search_query = f'site:linkedin.com/in/ "{role}" "{location}"'
    print(f"[STEP 1 - LinkedIn] Searching: '{search_query}'")
    
    run_input = {
        "queries": search_query, # Expects string (can be newline separated for multiple)
        "resultsPerPage": 100,
        "maxPagesPerQuery": 1,
    }
    
    print("[STEP 1 - LinkedIn] Starting Google Search (X-Ray) for Profiles...")
    
    # Using Google Search Scraper is often more reliable for "finding" people than direct LinkedIn search without cookies
    # Actor: apify/google-search-scraper
    run = client.actor("apify/google-search-scraper").call(run_input=run_input)
    
    results = []
    if run:
        for item in client.dataset(run["defaultDatasetId"]).iterate_items():
            results.append(item)
            
    print(f"[STEP 1 - LinkedIn] Retrieved {len(results)} raw results")
    return results


def transform_linkedin_leads(raw_results: List[Dict], role: str) -> pd.DataFrame:
    """
    Transform Google Search results of LinkedIn profiles into Lead format.
    """
    leads = []
    
    for item in raw_results:
        # Google Search Scraper structure
        organic_results = item.get("organicResults", [])
        
        for result in organic_results:
            title = result.get("title", "")
            url = result.get("url", "")
            snippet = result.get("description", "")
            
            # Simple heuristic to clean name from title
            # Title usually: "Name - Headline - LinkedIn"
            name_parts = title.split(" - ")[0]
            name = name_parts.strip()
            
            # Skip if it doesn't look like a profile
            if "linkedin.com/in/" not in url:
                continue
                
            lead = {
                "name": name,
                "address": "LinkedIn Global", # We can't be sure of exact city without deep scrape
                "phone": "",
                "website": url,
                "email": "", # Enrichment step will handle this
                "rating": 0,
                "reviews_count": 0,
                "category": role, # The searched role
                "google_maps_url": "",
                "latitude": "",
                "longitude": "",
                "source": "LinkedIn"
            }
            leads.append(lead)
            
            # Basic validation
            if len(leads) >= 500: # Safety limit
                break
                
    return pd.DataFrame(leads)


def main():
    parser = argparse.ArgumentParser(description="Step 1 (People): LinkedIn Search")
    parser.add_argument("--niche", required=True, help="Job role / Title (e.g. 'Founder')")
    parser.add_argument("--location", required=True, help="Location")
    parser.add_argument("--output", required=True, help="Output CSV file path")
    parser.add_argument("--max-results", type=int, default=50, help="Max results")
    
    args = parser.parse_args()
    
    client = get_apify_client()
    
    # 1. Run Search
    raw_results = run_linkedin_scraper(client, args.niche, args.location, args.max_results)
    
    # 2. Transform
    df = transform_linkedin_leads(raw_results, args.niche)
    
    # 3. Save
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if len(df) == 0:
        print("[STEP 1 - LinkedIn] No leads found.")
        # Create empty if needed or handle upstream
    
    df.to_csv(output_path, index=False)
    print(f"[STEP 1 - LinkedIn] Saved {len(df)} leads to {output_path}")


if __name__ == "__main__":
    main()
