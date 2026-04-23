# Insurance Scraper (UAE Providers)

## Objective
This project scrapes insurance data from major UAE insurance providers and structures it into a clean JSON format for analysis and further processing.

## Data Sources

- Takaful Emarat (Health Insurance)
- Daman (Health Insurance)
- Dubai Insurance (Health Insurance)
- AXA Global Healthcare via Daman (International Health Insurance)
- QIC UAE (Health Insurance)

## Features

- Scrapes insurance data from multiple providers
- Extracts plan name and premium information
- Cleans and standardizes data
- Saves output in JSON format
- Modular structure using separate files (sources, scraper, schema)

## How it works

- The scraper loads provider pages and attempts to extract structured plan data.
- For providers whose pages are accessible via static HTML, it parses plan details directly.
- For JS-heavy or redirect-protected providers, it uses the provided reference-backed dataset.
- The final output is written to `output/data.json` in the standardized schema.

## Output

The scraper generates a JSON file inside the `output/` folder:

Example:
```json
{
  "provider": "Takaful Emarat",
  "plan_name": "Health Plus Plan",
  "premium": "1200",
  "currency": "AED",
  "coverage": "Coverage up to AED 250,000 annually",
  "eligibility": "Available to UAE residents with valid visas",
  "benefits": ["Inpatient and outpatient coverage", "Maternity included"],
  "url": "https://www.takafulemarat.com/en/health-insurance/"
}
```

For providers whose pages require JavaScript rendering or redirect protection, the scraper includes an overview entry with a link back to the provider website for manual review.

This release also supports a reference-backed dataset for providers where static scraping is not reliable, using the provided plan metadata for Daman, AXA, Dubai Insurance, and QIC.
