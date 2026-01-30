#!/usr/bin/env python3
"""
Step 4: Validate - Pydantic Validation and Deduplication
Validates lead data and removes invalid/duplicate entries.

Input: stage3_content.csv
Output: final_leads.csv with only valid, deduplicated leads
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Optional

import pandas as pd
from pydantic import BaseModel, EmailStr, HttpUrl, field_validator, ValidationError


class ValidatedLead(BaseModel):
    """Pydantic model for lead validation."""
    
    name: str
    address: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    email: Optional[str] = None
    rating: Optional[float] = None
    reviews_count: Optional[int] = None
    category: Optional[str] = None
    google_maps_url: Optional[str] = None
    pain_point: Optional[str] = None
    solution: Optional[str] = None
    email_template: Optional[str] = None
    has_booking: Optional[bool] = None
    has_pricing: Optional[bool] = None
    has_contact: Optional[bool] = None
    meta_description: Optional[str] = None
    
    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()
    
    @field_validator("email")
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        if not v or pd.isna(v) or str(v).strip() == "":
            return None
        
        v = str(v).strip().lower()
        
        # Basic email regex validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            return None  # Invalid email, set to None instead of raising
        
        # Check for suspicious/fake emails
        suspicious_domains = ["example.com", "test.com", "domain.com", "email.com"]
        domain = v.split("@")[-1] if "@" in v else ""
        if domain in suspicious_domains:
            return None
        
        return v
    
    @field_validator("phone")
    @classmethod
    def clean_phone(cls, v: Optional[str]) -> Optional[str]:
        if not v or pd.isna(v):
            return None
        
        v = str(v).strip()
        
        # Remove common formatting
        cleaned = re.sub(r'[^\d+]', '', v)
        
        # Should have at least 7 digits
        if len(re.sub(r'\D', '', cleaned)) < 7:
            return None
        
        return v
    
    @field_validator("website")
    @classmethod
    def validate_website(cls, v: Optional[str]) -> Optional[str]:
        if not v or pd.isna(v) or str(v).strip() == "":
            return None
        
        v = str(v).strip()
        
        # Basic URL validation
        if not v.startswith(("http://", "https://")):
            v = "https://" + v
        
        # Check for valid domain structure
        url_pattern = r'^https?://[a-zA-Z0-9][-a-zA-Z0-9]*(\.[a-zA-Z0-9][-a-zA-Z0-9]*)+.*$'
        if not re.match(url_pattern, v):
            return None
        
        return v
    
    @field_validator("rating")
    @classmethod
    def validate_rating(cls, v) -> Optional[float]:
        if v is None or pd.isna(v):
            return None
        try:
            rating = float(v)
            if 0 <= rating <= 5:
                return rating
            return None
        except (ValueError, TypeError):
            return None


def validate_lead(row: pd.Series) -> tuple[bool, Optional[ValidatedLead], Optional[str]]:
    """
    Validate a single lead row.
    
    Returns: (is_valid, validated_lead, error_message)
    """
    try:
        lead_dict = row.to_dict()
        
        # Handle NaN values
        for key, value in lead_dict.items():
            if pd.isna(value):
                lead_dict[key] = None
        
        validated = ValidatedLead(**lead_dict)
        return True, validated, None
        
    except ValidationError as e:
        return False, None, str(e)


def deduplicate_leads(df: pd.DataFrame) -> pd.DataFrame:
    """Remove duplicate leads based on multiple criteria."""
    original_count = len(df)
    
    # Remove exact duplicates
    df = df.drop_duplicates()
    
    # Remove duplicates by phone (keep first)
    if "phone" in df.columns:
        df = df.drop_duplicates(subset=["phone"], keep="first")
    
    # Remove duplicates by website (keep first)
    if "website" in df.columns:
        df = df.drop_duplicates(subset=["website"], keep="first")
    
    # Remove duplicates by name + address (keep first)
    if "name" in df.columns and "address" in df.columns:
        df = df.drop_duplicates(subset=["name", "address"], keep="first")
    
    removed_count = original_count - len(df)
    if removed_count > 0:
        print(f"[STEP 4] Removed {removed_count} duplicate leads")
    
    return df


def calculate_quality_score(row: pd.Series) -> int:
    """
    Calculate quality score (0-100) based on multiple factors.
    
    Scoring rubric:
    - Has website: +20 points
    - Has email: +25 points
    - Has phone: +15 points
    - Rating >= 4.0: +20 points
    - Reviews >= 10: +10 points
    - Reviews >= 50: +5 bonus
    - Has_booking flag: +5 points
    """
    score = 0
    
    # Website presence
    if row.get('website') and pd.notna(row['website']) and str(row['website']).strip():
        score += 20
    
    # Contact info
    if row.get('email') and pd.notna(row['email']) and str(row['email']).strip():
        score += 25
    if row.get('phone') and pd.notna(row['phone']) and str(row['phone']).strip():
        score += 15
    
    # Reputation
    rating = row.get('rating', 0)
    if rating and pd.notna(rating):
        try:
            rating_val = float(rating)
            if rating_val >= 4.0:
                score += 20
        except (ValueError, TypeError):
            pass
    
    # Review count
    reviews = row.get('reviews_count', 0)
    if reviews and pd.notna(reviews):
        try:
            reviews_val = int(reviews)
            if reviews_val >= 10:
                score += 10
            if reviews_val >= 50:
                score += 5  # Bonus for popular businesses
        except (ValueError, TypeError):
            pass
    
    # Features
    if row.get('has_booking'):
        score += 5
    
    return min(score, 100)


def main():
    parser = argparse.ArgumentParser(description="Step 4: Validate and deduplicate leads")
    parser.add_argument("--input", required=True, help="Input CSV file path (stage3_content.csv)")
    parser.add_argument("--output", required=True, help="Output CSV file path")
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    # Validate input file exists
    if not input_path.exists():
        print(f"[STEP 4 FAILED] Input file not found: {input_path}")
        sys.exit(1)
    
    # Load input data
    df = pd.read_csv(input_path)
    
    if df.empty:
        print("[STEP 4 FAILED] Input file is empty")
        sys.exit(1)
    
    print(f"[STEP 4] Loaded {len(df)} leads from {input_path}")
    
    # Validate each lead
    valid_leads = []
    invalid_count = 0
    
    for idx, row in df.iterrows():
        is_valid, validated_lead, error = validate_lead(row)
        
        if is_valid and validated_lead:
            valid_leads.append(validated_lead.model_dump())
        else:
            invalid_count += 1
            # Optionally log the error
            # print(f"[STEP 4] Invalid lead '{row.get('name', 'Unknown')}': {error}")
    
    if invalid_count > 0:
        print(f"[STEP 4] Dropped {invalid_count} invalid leads")
    
    # Create DataFrame from valid leads
    if not valid_leads:
        print("[STEP 4 FAILED] No valid leads remaining after validation")
        sys.exit(1)
    
    validated_df = pd.DataFrame(valid_leads)
    
    # Deduplicate
    final_df = deduplicate_leads(validated_df)
    
    # Calculate quality scores
    print(f"[STEP 4] Calculating quality scores...")
    final_df['quality_score'] = final_df.apply(calculate_quality_score, axis=1)
    
    # Sort by quality score (highest first)
    final_df = final_df.sort_values('quality_score', ascending=False)
    
    # Quality score statistics
    avg_score = final_df['quality_score'].mean()
    high_quality = len(final_df[final_df['quality_score'] >= 70])
    print(f"[STEP 4] Quality metrics: Avg score = {avg_score:.1f}, High quality (>=70) = {high_quality}/{len(final_df)}")
    
    # Final quality check
    if len(final_df) < 1:
        print("[STEP 4 FAILED] No leads remaining after deduplication")
        sys.exit(1)
    
    # Select columns for final output (clean export)
    export_columns = [
        "name",
        "address",
        "phone",
        "email",
        "website",
        "rating",
        "reviews_count",
        "category",
        "has_booking",
        "has_pricing",
        "quality_score",  # NEW: Quality score
        "pain_point",
        "email_template",
        "google_maps_url",
    ]
    
    # Only include columns that exist
    available_columns = [col for col in export_columns if col in final_df.columns]
    final_df = final_df[available_columns]
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save output
    final_df.to_csv(output_path, index=False)
    
    print(f"[STEP 4 SUCCESS] Validated {len(final_df)} leads")
    print(f"[STEP 4] Output saved to: {output_path}")


if __name__ == "__main__":
    main()
