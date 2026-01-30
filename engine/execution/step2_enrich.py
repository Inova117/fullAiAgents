#!/usr/bin/env python3
"""
Step 2: Enrich - Website Scraping with requests + BeautifulSoup
Scans websites for keywords and extracts meta information.

Input: stage1.csv
Output: stage2_enriched.csv with additional columns
"""

import argparse
import re
import sys
import time
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import pandas as pd
import requests
from bs4 import BeautifulSoup

# Configuration
REQUEST_TIMEOUT = 10  # seconds
DELAY_BETWEEN_REQUESTS = 0.5  # seconds (be respectful to servers)
MAX_RETRIES = 2

# Keywords to search for on websites
BOOKING_KEYWORDS = [
    r"book\s*now",
    r"book\s*online",
    r"schedule",
    r"appointment",
    r"reserve",
    r"reserva",  # Spanish
    r"cita",     # Spanish
]

PRICING_KEYWORDS = [
    r"pricing",
    r"prices",
    r"rates",
    r"cost",
    r"\$\d+",
    r"€\d+",
    r"precios",  # Spanish
    r"tarifas",  # Spanish
]

CONTACT_KEYWORDS = [
    r"contact\s*us",
    r"get\s*in\s*touch",
    r"contacto",  # Spanish
]


def normalize_url(url: str) -> Optional[str]:
    """Normalize and validate URL."""
    if not url or pd.isna(url):
        return None
    
    url = str(url).strip()
    
    if not url:
        return None
    
    # Add scheme if missing
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    
    # Validate URL structure
    try:
        parsed = urlparse(url)
        if not parsed.netloc:
            return None
        return url
    except Exception:
        return None


def extract_emails_from_text(text: str) -> list[str]:
    """Extract email addresses from text using regex."""
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = re.findall(email_pattern, text)
    
    # Filter out common false positives
    filtered = []
    for email in emails:
        email_lower = email.lower()
        if not any(fp in email_lower for fp in ["example.com", "domain.com", "email.com", ".png", ".jpg", ".gif"]):
            filtered.append(email)
    
    return list(set(filtered))


def check_keywords(text: str, patterns: list[str]) -> bool:
    """Check if any of the keyword patterns exist in the text."""
    text_lower = text.lower()
    for pattern in patterns:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return True
    return False


def scrape_website(url: str) -> dict:
    """
    Scrape a single website and extract relevant information.
    
    Returns dict with:
    - success: bool
    - has_booking: bool
    - has_pricing: bool
    - has_contact: bool
    - meta_description: str
    - emails_found: list[str]
    - error: Optional[str]
    """
    result = {
        "success": False,
        "has_booking": False,
        "has_pricing": False,
        "has_contact": False,
        "meta_description": "",
        "emails_found": [],
        "error": None,
    }
    
    normalized_url = normalize_url(url)
    if not normalized_url:
        result["error"] = "Invalid URL"
        return result
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(
                normalized_url,
                headers=headers,
                timeout=REQUEST_TIMEOUT,
                allow_redirects=True,
                verify=True
            )
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.text, "lxml")
            
            # Get all text content
            text_content = soup.get_text(separator=" ", strip=True)
            
            # Check for keywords
            result["has_booking"] = check_keywords(text_content, BOOKING_KEYWORDS)
            result["has_pricing"] = check_keywords(text_content, PRICING_KEYWORDS)
            result["has_contact"] = check_keywords(text_content, CONTACT_KEYWORDS)
            
            # Extract meta description
            meta_desc = soup.find("meta", attrs={"name": "description"})
            if meta_desc and meta_desc.get("content"):
                result["meta_description"] = meta_desc["content"][:500]
            
            # Extract emails
            result["emails_found"] = extract_emails_from_text(response.text)
            
            result["success"] = True
            return result
            
        except requests.exceptions.Timeout:
            result["error"] = "Timeout"
        except requests.exceptions.SSLError:
            result["error"] = "SSL Error"
        except requests.exceptions.ConnectionError:
            result["error"] = "Connection Error"
        except requests.exceptions.HTTPError as e:
            result["error"] = f"HTTP {e.response.status_code}"
        except Exception as e:
            result["error"] = str(e)[:100]
        
        if attempt < MAX_RETRIES - 1:
            time.sleep(1)  # Wait before retry
    
    return result


def enrich_leads(input_df: pd.DataFrame) -> pd.DataFrame:
    """Enrich leads with website data."""
    # Add new columns
    input_df["scrape_success"] = False
    input_df["has_booking"] = False
    input_df["has_pricing"] = False
    input_df["has_contact"] = False
    input_df["meta_description"] = ""
    input_df["emails_from_website"] = ""
    input_df["scrape_error"] = ""
    
    total = len(input_df)
    success_count = 0
    
    for idx, row in input_df.iterrows():
        website = row.get("website", "")
        
        print(f"[STEP 2] Processing {idx + 1}/{total}: {row.get('name', 'Unknown')}")
        
        if not website or pd.isna(website) or str(website).strip() == "":
            input_df.at[idx, "scrape_error"] = "No website"
            continue
        
        # Scrape the website
        result = scrape_website(website)
        
        input_df.at[idx, "scrape_success"] = result["success"]
        input_df.at[idx, "has_booking"] = result["has_booking"]
        input_df.at[idx, "has_pricing"] = result["has_pricing"]
        input_df.at[idx, "has_contact"] = result["has_contact"]
        input_df.at[idx, "meta_description"] = result["meta_description"]
        input_df.at[idx, "emails_from_website"] = ",".join(result["emails_found"])
        input_df.at[idx, "scrape_error"] = result["error"] or ""
        
        if result["success"]:
            success_count += 1
        
        # Respectful delay
        time.sleep(DELAY_BETWEEN_REQUESTS)
    
    # Update email column with found emails if original is empty
    for idx, row in input_df.iterrows():
        if (not row.get("email") or pd.isna(row["email"]) or str(row["email"]).strip() == ""):
            emails = row.get("emails_from_website", "")
            if emails:
                first_email = emails.split(",")[0]
                input_df.at[idx, "email"] = first_email
    
    print(f"[STEP 2] Scraping complete: {success_count}/{total} websites scraped successfully")
    
    return input_df


def main():
    parser = argparse.ArgumentParser(description="Step 2: Enrich leads with website data")
    parser.add_argument("--input", required=True, help="Input CSV file path (stage1.csv)")
    parser.add_argument("--output", required=True, help="Output CSV file path")
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    # Validate input file exists
    if not input_path.exists():
        print(f"[STEP 2 FAILED] Input file not found: {input_path}")
        sys.exit(1)
    
    # Load input data
    df = pd.read_csv(input_path)
    
    if df.empty:
        print("[STEP 2 FAILED] Input file is empty")
        sys.exit(1)
    
    print(f"[STEP 2] Loaded {len(df)} leads from {input_path}")
    
    # Enrich leads
    enriched_df = enrich_leads(df)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save enriched data
    enriched_df.to_csv(output_path, index=False)
    
    print(f"[STEP 2 SUCCESS] Enriched {len(enriched_df)} leads")
    print(f"[STEP 2] Output saved to: {output_path}")


if __name__ == "__main__":
    main()
