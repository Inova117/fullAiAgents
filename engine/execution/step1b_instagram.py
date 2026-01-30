#!/usr/bin/env python3
"""
Step 1b: Instagram Scraper - Social Media Lead Generation
Uses Actor: apify/instagram-scraper

Input: niche + location (converted to hashtags)
Output: stage1_instagram.csv with raw lead data
"""

import argparse
import os
import sys
import re
from pathlib import Path
from typing import List, Dict, Any

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


def generate_hashtags(niche: str, location: str) -> List[str]:
    """
    Generate relevant hashtags for the search.
    Example: niche="Restaurantes", location="Ambato"
    -> #RestaurantesAmbato, #AmbatoRestaurantes, #ComidaAmbato, #Ambato
    """
    # Clean inputs (remove spaces, special chars for hashtag format)
    clean_niche = "".join(filter(str.isalnum, niche.title()))
    clean_loc = "".join(filter(str.isalnum, location.split(',')[0].title())) # Take city only
    
    hashtags = [
        f"{clean_niche}{clean_loc}",       # RestaurantesAmbato
        f"{clean_loc}{clean_niche}",       # AmbatoRestaurantes
        f"{clean_niche}En{clean_loc}",     # RestaurantesEnAmbato
    ]
    
    # Add some generic variations based on common industries
    niche_lower = niche.lower()
    if "restaurante" in niche_lower or "comida" in niche_lower:
        hashtags.extend([f"Comida{clean_loc}", f"Gastronomia{clean_loc}", f"DondeComerEn{clean_loc}"])
    elif "moda" in niche_lower or "ropa" in niche_lower:
        hashtags.extend([f"Moda{clean_loc}", f"Boutique{clean_loc}"])
        
    return hashtags


def run_instagram_scraper(
    client: ApifyClient,
    hashtags: List[str],
    max_posts: int = 50
) -> List[Dict]:
    """
    Run the Instagram Scraper actor to find posts by hashtag, 
    then extract the profile info of the posters.
    
    Actor: apify/instagram-scraper
    """
    print(f"[STEP 1b] Searching Instagram hashtags: {hashtags}")
    
    all_results = []
    
    for tag in hashtags:
        print(f"[STEP 1b] Scraping hashtag: {tag}")
        
        # apify/instagram-scraper input
        # "search" must be a string. We search one tag at a time.
        run_input = {
            "search": tag,
            "searchType": "hashtag",
            "resultsType": "posts",
            "searchLimit": 1,
            "resultsLimit": max_posts,
        }
        
        try:
            # Run the actor
            run = client.actor("apify/instagram-scraper").call(run_input=run_input)
            
            if run:
                count = 0
                for item in client.dataset(run["defaultDatasetId"]).iterate_items():
                    all_results.append(item)
                    count += 1
                print(f"[STEP 1b] Found {count} posts for {tag}")
                
        except Exception as e:
            print(f"[ERROR] Failed to scrape {tag}: {e}")
            
    print(f"[STEP 1b] Retrieved {len(all_results)} total raw posts from Instagram")
    
    # We need to extract unique profiles from these posts
    return all_results


def transform_instagram_leads(raw_posts: List[Dict]) -> pd.DataFrame:
    """
    Transform raw Instagram post objects into our standard lead format.
    We extract metadata from the 'owner' field of the post.
    """
    leads = []
    seen_usernames = set()
    
    for post in raw_posts:
        # Extract owner/author data
        # Note: Structure depends heavily on the specific actor version output
        # Typically: item['owner'] = { 'username': '...', 'fullName': '...' }
        
        owner = post.get('owner', {})
        username = owner.get('username') or post.get('ownerUsername')
        
        if not username or username in seen_usernames:
            continue
            
        seen_usernames.add(username)
        
        # Try to find contact info in bio if available (some scrapers get this)
        # Otherwise, the 'website' is valuable
        
        full_name = owner.get('fullName') or username
        biography = owner.get('biography', '')  # Might not be in post object, need profile scrape?
        # Often post objects contain simplified owner info. 
        # For MVP, we use what's available.
        
        # Construct standard lead object
        lead = {
            "name": full_name,
            "address": "Instagram", # Field required by schema
            "phone": "", # Hard to get without deep profile scrape
            "website": f"https://instagram.com/{username}",
            "email": "", # Will need enrichment
            "rating": 0,
            "reviews_count": post.get('likesCount', 0), # Proxy for popularity
            "category": "Instagram Business",
            "google_maps_url": "",
            "latitude": "",
            "longitude": "",
            "source": "Instagram" # New field to track provenance
        }
        
        # Heuristics to find email in bio if (rarely) present in this object
        # or we might text search the caption
        caption = post.get('caption', '')
        emails = re.findall(r'[\w.+-]+@[\w-]+\.[\w.-]+', caption)
        if emails:
            lead['email'] = emails[0]
            
        leads.append(lead)
    
    return pd.DataFrame(leads)


def main():
    parser = argparse.ArgumentParser(description="Step 1b: Instagram Lead Search")
    parser.add_argument("--niche", required=True, help="Business niche")
    parser.add_argument("--location", required=True, help="Location (City)")
    parser.add_argument("--output", required=True, help="Output CSV file path")
    parser.add_argument("--max-results", type=int, default=50, help="Max posts to scrape")
    
    args = parser.parse_args()
    
    client = get_apify_client()
    
    # 1. Generate Hashtags
    hashtags = generate_hashtags(args.niche, args.location)
    
    # 2. Run Scraper
    raw_results = run_instagram_scraper(client, hashtags, args.max_results)
    
    # 3. Transform
    df = transform_instagram_leads(raw_results)
    
    if len(df) == 0:
        print("[STEP 1b] No leads found on Instagram.")
        # Create empty df with columns to prevent pipeline crash if we want
        # But usually better to exit
    
    # 4. Save
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    
    print(f"[STEP 1b] Saved {len(df)} unique Instagram leads to {output_path}")


if __name__ == "__main__":
    main()
