# SOP: Step 3 - Template

**Goal**: Generate personalized "Pain Point" and "Solution" text based on business category, without using LLMs.

## Inputs
- **Input File**: `stage2_{job_id}.csv` (Output from Step 2)
- **Location**: Original search location (for context in email)

## Tools
- `engine/execution/step3_template.py`
- **Hash Map Logic**: Pure Python dictionary lookup

## Process
1. Load enriched leads
2. For each lead:
   - Identify `category` and `name`
   - Fuzzy match against predefined `PAIN_POINTS` dictionary
   - Retrieve mapped `pain_point` and `solution`
3. **Template Generation**:
   - Construct email body using `EMAIL_TEMPLATE`
   - Insert `business_name`, `pain_point`, `solution`, `location`
   - **CRITICAL**: Use escape sequences (`\n`) for newlines to ensure CSV compatibility.
4. Save results

## Output
- **File**: `engine/tmp/stage3_{job_id}.csv`
- **New Columns**: `pain_point`, `solution`, `email_template`

## Edge Cases
- **Unknown Category**: Fallback to "Default" pain point mapping.
- **CSV Formatting**: Ensure no unescaped newlines break the CSV structure.
