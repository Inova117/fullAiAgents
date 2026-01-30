#!/usr/bin/env python3
"""
Step 3: Template - Deterministic Pain Point & Email Template Mapping
Maps business categories to predefined pain points and email templates.

NO LLM USAGE - Pure deterministic hash map logic.

Input: stage2_enriched.csv
Output: stage3_content.csv with pain_point and email_template columns
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

# ============================================================================
# DETERMINISTIC PAIN POINT MAPPINGS
# These are predefined templates based on business category.
# ============================================================================

PAIN_POINTS = {
    # Fitness & Wellness
    "gym": {
        "pain_point": "Managing class schedules and member check-ins manually wastes hours every week.",
        "solution": "automated booking and member management system",
    },
    "fitness": {
        "pain_point": "Tracking member progress and retention without proper software leads to churn.",
        "solution": "integrated fitness tracking and engagement platform",
    },
    "yoga": {
        "pain_point": "Coordinating instructor schedules and class bookings via spreadsheets is error-prone.",
        "solution": "streamlined class scheduling and booking system",
    },
    "pilates": {
        "pain_point": "Managing equipment bookings and small group sessions manually limits growth.",
        "solution": "smart studio management solution",
    },
    "crossfit": {
        "pain_point": "Tracking WOD results and athlete progress across hundreds of members is overwhelming.",
        "solution": "performance tracking and community platform",
    },
    
    # Food & Beverage
    "restaurant": {
        "pain_point": "Reservation no-shows cost you money, and phone bookings waste staff time.",
        "solution": "online reservation system with automated reminders",
    },
    "cafe": {
        "pain_point": "Peak hour rushes lead to long queues and lost customers.",
        "solution": "mobile ordering and queue management system",
    },
    "bar": {
        "pain_point": "Event promotion and table reservations are scattered across platforms.",
        "solution": "unified booking and event management platform",
    },
    "bakery": {
        "pain_point": "Custom order management via phone calls leads to mistakes and missed orders.",
        "solution": "online ordering system for custom cakes and pre-orders",
    },
    
    # Healthcare
    "dentist": {
        "pain_point": "Patients expect online booking, but your phone lines are always busy.",
        "solution": "24/7 online appointment scheduling with reminders",
    },
    "doctor": {
        "pain_point": "Administrative staff spends hours calling patients for appointment confirmations.",
        "solution": "automated appointment scheduling and reminder system",
    },
    "clinic": {
        "pain_point": "Managing multiple practitioners and rooms without software causes scheduling conflicts.",
        "solution": "multi-provider scheduling and practice management system",
    },
    "physiotherapy": {
        "pain_point": "Tracking patient progress across sessions without digital records is inefficient.",
        "solution": "patient management and progress tracking platform",
    },
    "veterinary": {
        "pain_point": "Pet owners want convenient booking options, but you rely on phone calls.",
        "solution": "pet-owner friendly online booking system",
    },
    
    # Beauty & Personal Care
    "salon": {
        "pain_point": "Double bookings and no-shows hurt your revenue and stylist morale.",
        "solution": "smart scheduling with deposit collection and reminders",
    },
    "spa": {
        "pain_point": "Coordinating multiple services and practitioners for one visit is complex.",
        "solution": "multi-service booking and package management system",
    },
    "barbershop": {
        "pain_point": "Walk-in traffic is unpredictable, making staff scheduling a nightmare.",
        "solution": "online booking with real-time availability display",
    },
    "nail": {
        "pain_point": "Clients forget appointments, and calling reminders takes too much time.",
        "solution": "automated booking confirmations and reminders",
    },
    
    # Professional Services
    "lawyer": {
        "pain_point": "Potential clients go elsewhere when they can't easily schedule consultations.",
        "solution": "professional intake and appointment scheduling system",
    },
    "accountant": {
        "pain_point": "Tax season overwhelms you with scheduling requests via email and phone.",
        "solution": "client portal with self-service scheduling",
    },
    "consultant": {
        "pain_point": "You spend too much time on admin instead of billable client work.",
        "solution": "calendar management and client booking automation",
    },
    
    # Education
    "tutor": {
        "pain_point": "Coordinating sessions with multiple students across different schedules is chaos.",
        "solution": "tutoring session management and scheduling platform",
    },
    "music school": {
        "pain_point": "Managing instrument lessons, recitals, and room bookings is overwhelming.",
        "solution": "music school management and lesson scheduling system",
    },
    "driving school": {
        "pain_point": "Coordinating instructors, vehicles, and student schedules is a logistical challenge.",
        "solution": "driving school scheduling and fleet management solution",
    },
    
    # Home Services
    "plumber": {
        "pain_point": "Missing calls means missing jobs, but you can't answer while working.",
        "solution": "24/7 online booking and job management system",
    },
    "electrician": {
        "pain_point": "Quoting and scheduling multiple jobs efficiently is challenging without software.",
        "solution": "field service management and scheduling platform",
    },
    "cleaning": {
        "pain_point": "Managing recurring bookings and multiple cleaners is time-consuming.",
        "solution": "cleaning service scheduling and team management system",
    },
    
    # Default fallback
    "default": {
        "pain_point": "Managing appointments and client communications manually limits your growth.",
        "solution": "professional booking and client management system",
    },
}

# Email template structure (single line with escape sequences for CSV compatibility)
EMAIL_TEMPLATE = "Subject: Quick question about {business_name}'s booking process\\n\\nHi there,\\n\\nI noticed {business_name} while researching {category} businesses in {location}.\\n\\n{pain_point}\\n\\nI specialize in helping businesses like yours implement a {solution} that can: (1) Reduce no-shows by up to 50%, (2) Save 10+ hours per week on admin tasks, (3) Allow 24/7 bookings when you're unavailable.\\n\\nWould you be open to a quick 15-minute call this week to see if this could work for {business_name}?\\n\\nBest regards, [Your Name]\\n\\nP.S. I've helped similar {category} businesses increase bookings by 30% within the first month."


def get_category_mapping(category: str, name: str) -> dict:
    """
    Match business category to pain point mapping.
    Uses fuzzy keyword matching on category and business name.
    """
    if not category:
        category = ""
    if not name:
        name = ""
    
    search_text = f"{category} {name}".lower()
    
    # Check each keyword in order of specificity
    for keyword, mapping in PAIN_POINTS.items():
        if keyword != "default" and keyword in search_text:
            return mapping
    
    # Return default if no match
    return PAIN_POINTS["default"]


def generate_email_content(row: pd.Series, location: str) -> tuple[str, str, str]:
    """
    Generate personalized email content for a lead.
    
    Returns: (pain_point, solution, full_email)
    """
    name = row.get("name", "Your Business")
    category = row.get("category", "")
    
    mapping = get_category_mapping(category, name)
    
    pain_point = mapping["pain_point"]
    solution = mapping["solution"]
    
    # Generate the full email from template
    email_content = EMAIL_TEMPLATE.format(
        business_name=name,
        category=category if category else "local",
        location=location,
        pain_point=pain_point,
        solution=solution,
    )
    
    return pain_point, solution, email_content


def main():
    parser = argparse.ArgumentParser(description="Step 3: Generate pain points and email templates")
    parser.add_argument("--input", required=True, help="Input CSV file path (stage2_enriched.csv)")
    parser.add_argument("--output", required=True, help="Output CSV file path")
    parser.add_argument("--location", required=True, help="Original search location (for email personalization)")
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    # Validate input file exists
    if not input_path.exists():
        print(f"[STEP 3 FAILED] Input file not found: {input_path}")
        sys.exit(1)
    
    # Load input data
    df = pd.read_csv(input_path)
    
    if df.empty:
        print("[STEP 3 FAILED] Input file is empty")
        sys.exit(1)
    
    print(f"[STEP 3] Loaded {len(df)} leads from {input_path}")
    
    # Add new columns
    df["pain_point"] = ""
    df["solution"] = ""
    df["email_template"] = ""
    
    # Generate content for each lead
    for idx, row in df.iterrows():
        pain_point, solution, email_template = generate_email_content(row, args.location)
        df.at[idx, "pain_point"] = pain_point
        df.at[idx, "solution"] = solution
        df.at[idx, "email_template"] = email_template
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save output
    df.to_csv(output_path, index=False)
    
    print(f"[STEP 3 SUCCESS] Generated templates for {len(df)} leads")
    print(f"[STEP 3] Output saved to: {output_path}")


if __name__ == "__main__":
    main()
