# SOP: Step 1 - Search

**Goal**: Find potential leads for a specific niche and location using Google Maps.

## Inputs
- **Niche**: Business category (e.g., "gyms", "dentists")
- **Location**: Geographic area (e.g., "Madrid, Spain")
- **Max Results**: Limit on number of leads (default: 100)

## Tools
- `engine/execution/step1_search.py`
- **Apify Client**: Uses actor `nwua9Gu5YrADL7ZDj` (Google Maps Scraper)

## Process
1. Initialize Apify Client with token from `.env`
2. Run Google Maps Scraper actor with inputs
3. Transform raw JSON results into standardized CSV format
4. **NEW: Geographic Filtering** - Post-filter results to keep only leads matching target location
5. **Quality Gate**: Check if at least 5 leads remain. If less, fail.

## Output
- **File**: `engine/tmp/stage1_{job_id}.csv`
- **Columns**: `name`, `address`, `phone`, `website`, `rating`, `reviews_count`, `category`, `google_maps_url`, `latitude`, `longitude`

## Edge Cases
- **No results**: If Apify returns 0 results, script must exit with error code 1.
- **Missing API Token**: Script must fail fast if `APIFY_API_TOKEN` is missing.
- **Location Accuracy Issue**: Actor `nwua9Gu5YrADL7ZDj` sometimes returns results from incorrect locations (e.g., searching "Portland, Oregon" may return New York results). This is a known limitation of the Apify actor rather than our code. Potential solutions:
  - Post-filter by checking if address contains target city/state
  - Use alternative actor if accuracy is critical
  - Accept mixed results and rely on manual filtering downstream
  
**Current Approach**: We accept Apify's results as-is to maximize lead count. Users can manually filter by location in the final CSV.

