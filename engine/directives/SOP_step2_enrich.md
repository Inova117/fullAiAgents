# SOP: Step 2 - Enrich

**Goal**: Visit each lead's website to extract contact info and detect business features.

## Inputs
- **Input File**: `stage1_{job_id}.csv` (Output from Step 1)

## Tools
- `engine/execution/step2_enrich.py`
- `requests` (HTTP client)
- `BeautifulSoup` (HTML parsing)

## Process
1. Load leads from input CSV
2. For each lead with a website URL:
   - Normalize URL (add https:// if missing)
   - Send HTTP GET request (timeout: 10s)
   - Parse HTML content
3. **Keyword Detection**: Check for presence of:
   - "Book Now" / "Schedule" (Booking system)
   - "Pricing" / "Rates" (Pricing page)
   - "Contact Us" (Contact info)
4. **Extraction**:
   - Meta description (for context)
   - Emails (regex match in body text)
5. Save results incrementally or in batch

## Output
- **File**: `engine/tmp/stage2_{job_id}.csv`
- **New Columns**: `has_booking`, `has_pricing`, `has_contact`, `meta_description`, `emails_from_website`, `scrape_success`

## Edge Cases
- **Website down/timeout**: Mark `scrape_success` as False, do not crash.
- **No website**: Skip row, standard process.
