#!/usr/bin/env python3
"""
Step 1: Search - Google Maps Scraper using Apify
Uses Actor: nwua9Gu5YrADL7ZDj (Google Maps Scraper)

Input: niche + location as CLI arguments
Output: stage1.csv with raw lead data
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Optional

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



def get_keyword_variations(niche: str) -> list[str]:
    """
    Expand a broad niche into specific sub-niches to uncover more results.
    Includes both English and Spanish common variations.
    """
    niche_lower = niche.lower().strip()
    
    # Static expansion map for common industries
    expansions = {
        "restaurante": [
            "Restaurante italiano", "Pizzería", "Hamburguesería", "Sushi", 
            "Comida china", "Comida mexicana", "Asadero", "Mariscos", 
            "Cafetería", "Bar", "Restaurante elegante", "Comida rápida", 
            "Desayunos", "Almuerzos", "Cenas"
        ],
        "restaurant": [
            "Italian restaurant", "Pizzeria", "Burger joint", "Sushi bar", 
            "Chinese restaurant", "Mexican restaurant", "Steakhouse", "Seafood",
            "Cafe", "Bar", "Fine dining", "Fast food"
        ],
        "dentista": [
            "Clínica dental", "Ortodoncista", "Dentista pediátrico", 
            "Cirujano oral", "Implantes dentales", "Endodoncia"
        ],
        "dentist": [
            "Dental clinic", "Orthodontist", "Pediatric dentist", 
            "Oral surgeon", "Dental implants", "Endodontics"
        ],
        "inmobiliaria": [
            "Agente inmobiliario", "Venta de casas", "Alquiler de departamentos", 
            "Bienes raíces comercial", "Administración de propiedades"
        ],
        "real estate": [
            "Real estate agent", "Home sales", "Apartment rentals", 
            "Commercial real estate", "Property management"
        ],
        "gym": [
            "Crossfit", "Yoga studio", "Pilates", "Personal trainer", 
            "Boxing gym", "Fitness center"
        ],
        "gimnasio": [
            "Crossfit", "Estudio de Yoga", "Pilates", "Entrenador personal", 
            "Boxeo", "Centro fitness"
        ]
    }
    
    # Check for direct match or partial match
    for key, variations in expansions.items():
        if key in niche_lower:
            return variations
            
    # Default: valid but generic modifiers if no specific category found
    return [
        f"Mejores {niche}", 
        f"{niche} baratos", 
        f"{niche} exclusivos",
        f"{niche} cerca de mí"
    ]


def run_google_maps_scraper(
    client: ApifyClient,
    niche: str,
    location: str,
    max_results: int = 100,
    deep_search: bool = True
) -> list[dict]:
    """
    Run the Google Maps Scraper actor.
    
    Actor: nwua9Gu5YrADL7ZDj (Google Maps Scraper by compass)
    
    Args:
        deep_search: If True, expands the niche into multiple sub-queries to maximize results.
    """
    base_query = f"{niche} in {location}"
    queries = [base_query]
    
    if deep_search:
        print(f"[STEP 1] Deep Search ENABLED. Expanding keywords for '{niche}'...")
        variations = get_keyword_variations(niche)
        
        # Combine variations with location
        expanded_queries = [f"{var} in {location}" for var in variations]
        queries.extend(expanded_queries)
        
        print(f"[STEP 1] Generated {len(queries)} total search variations.")
        # Print first 3 for debugging
        for q in queries[:3]:
            print(f"  - {q}")
    else:
        print(f"[STEP 1] Searching for: '{base_query}'")
    
    # Optimize max results per query to avoid burning budget on duplicates
    # If doing deep search, we might want fewer results per specific query but more queries
    per_query_limit = 60 if deep_search else max_results
    
    # Prepare the actor input
    run_input = {
        "searchStringsArray": queries,
        "maxCrawledPlacesPerSearch": per_query_limit,
        "language": "es", # Default to Spanish based on user context (Ambato), or make configurable
        "exportPlaceUrls": False,
        "includeWebResults": False,
        "maxImages": 0,
        "maxReviews": 0,
        "scrapeReviewerName": False,
        "scrapeReviewerId": False,
        "scrapeReviewerUrl": False,
        "scrapeReviewId": False,
        "scrapeReviewUrl": False,
        "scrapeResponseFromOwnerText": False,
    }
    
    print("[STEP 1] Starting Apify actor run...")
    
    # Run the actor and wait for it to finish
    run = client.actor("nwua9Gu5YrADL7ZDj").call(run_input=run_input)
    
    # Fetch results from the run's dataset
    results = []
    for item in client.dataset(run["defaultDatasetId"]).iterate_items():
        results.append(item)
    
    print(f"[STEP 1] Retrieved {len(results)} raw results from Apify")
    return results


def transform_to_leads(raw_results: list[dict]) -> pd.DataFrame:
    """Transform raw Apify results to standardized lead format."""
    leads = []
    
    for item in raw_results:
        lead = {
            "name": item.get("title", ""),
            "address": item.get("address", ""),
            "phone": item.get("phone", ""),
            "website": item.get("website", ""),
            "email": "",  # Will be enriched in step 2
            "rating": item.get("totalScore", 0),
            "reviews_count": item.get("reviewsCount", 0),
            "category": item.get("categoryName", ""),
            "google_maps_url": item.get("url", ""),
            "latitude": item.get("location", {}).get("lat", ""),
            "longitude": item.get("location", {}).get("lng", ""),
        }
        leads.append(lead)
    
    df = pd.DataFrame(leads)
    
    # Remove duplicates by name + address
    df = df.drop_duplicates(subset=["name", "address"])
    
    # Remove entries without a name
    df = df[df["name"].str.strip() != ""]
    
    return df


def filter_by_location(df: pd.DataFrame, target_location: str) -> pd.DataFrame:
    """
    Filter leads by checking if address contains target city/state.
    
    Examples:
    - "Portland, Oregon" → must contain "Portland" OR "OR" OR "Oregon"
    - "Madrid, Spain" → must contain "Madrid" OR "Spain"
    
    This is a post-filter to compensate for Apify's location accuracy issues.
    """
    import re
    
    # Parse target location into keywords
    parts = [p.strip() for p in target_location.split(',')]
    
    # Create flexible regex (match any of the parts)
    keywords = '|'.join(re.escape(p) for p in parts if p)
    pattern = re.compile(keywords, re.IGNORECASE)
    
    # Filter by address match
    df['location_match'] = df['address'].str.contains(pattern, na=False, regex=True)
    matched = df[df['location_match'] == True].copy()
    filtered_out = len(df) - len(matched)
    
    if filtered_out > 0:
        print(f"[STEP 1] Location filter: Kept {len(matched)}/{len(df)} leads matching '{target_location}'")
        print(f"[STEP 1] Filtered out {filtered_out} leads from incorrect locations")
    
    # Clean up temporary column
    matched = matched.drop(columns=['location_match'])
    
    return matched


def main():
    parser = argparse.ArgumentParser(description="Step 1: Google Maps Lead Search")
    parser.add_argument("--niche", required=True, help="Business niche to search (e.g., 'gyms')")
    parser.add_argument("--location", required=True, help="Location to search (e.g., 'Madrid, Spain')")
    parser.add_argument("--output", required=True, help="Output CSV file path")
    parser.add_argument("--max-results", type=int, default=100, help="Maximum results to fetch")
    
    args = parser.parse_args()
    
    # Initialize client
    client = get_apify_client()
    
    # Run the scraper
    raw_results = run_google_maps_scraper(
        client,
        args.niche,
        args.location,
        args.max_results
    )
    
    # Quality Gate: Check minimum results
    if len(raw_results) < 5:
        print(f"[STEP 1 FAILED] Only found {len(raw_results)} results. Minimum required: 5")
        sys.exit(1)
    
    # Transform to leads
    df = transform_to_leads(raw_results)
    
    # Apply location filter to remove incorrect locations
    df = filter_by_location(df, args.location)
    
    # Quality Gate: Check transformed leads
    if len(df) < 5:
        print(f"[STEP 1 FAILED] Only {len(df)} valid leads after transformation. Minimum required: 5")
        sys.exit(1)
    
    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    
    print(f"[STEP 1 SUCCESS] Found {len(df)} leads")
    print(f"[STEP 1] Output saved to: {output_path}")


if __name__ == "__main__":
    main()
