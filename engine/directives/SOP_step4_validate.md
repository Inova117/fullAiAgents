# SOP: Step 4 - Validate

**Goal**: Ensure data quality, validate email formats, and remove duplicates before final export.

## Inputs
- **Input File**: `stage3_{job_id}.csv` (Output from Step 3)

## Tools
- `engine/execution/step4_validate.py`
- `pydantic` (Data validation)

## Process
1. Load processed leads
2. **Pydantic Validation**:
   - Iterate through each row and parse into `ValidatedLead` model
   - Check Name: Not empty
   - Check Email: Valid format (regex) + blacklist (no "example.com")
   - Check URL: Valid scheme
   - Drop rows that fail critical validation
3. **Deduplication**:
   - Remove exact row duplicates
   - Remove duplicates by `phone` (keep first)
   - Remove duplicates by `website` (keep first)
   - Remove duplicates by `name` + `address`
4. **NEW: Quality Scoring**:
   - Calculate quality_score (0-100) for each lead
   - Based on: website, email, phone, rating, reviews, has_booking
   - Sort results by quality score (highest first)
5. Select final columns for export

## Output
- **File**: `engine/data/final_leads_{job_id}.csv`
- **Final Columns**: `name`, `address`, `phone`, `email`, `website`, `rating`, `reviews_count`, `category`, `has_booking`, `has_pricing`, `quality_score`, `pain_point`, `email_template`, `google_maps_url`
- **Sort Order**: Descending by `quality_score` (best leads first)

## Edge Cases
- **No valid leads**: If 0 leads remain after validation, exit with error code 1 to alert Orchestrator.
