# Insurance Scraper (UAE Providers)

## Objective
This project scrapes insurance data from major UAE insurance providers and structures it into a clean JSON format for analysis and further processing.

## Data Sources

- Takaful Emarat (Health, Life Insurance)
- Daman (Health Insurance)
- Dubai Insurance (Multi-line Insurance)
- AXA Global Healthcare (International Health Insurance)
- QIC UAE (Motor, Travel Insurance)

## Features

- Scrapes insurance data from multiple providers
- Extracts plan name and premium information
- Cleans and standardizes data
- Saves output in JSON format
- Modular structure using separate files (sources, scraper, schema)

## Output

The scraper generates a JSON file inside the `output/` folder:

Example:
```json
{
  "provider": "Takaful Emarat",
  "plan_name": "Health Plus Plan",
  "premium": "1200",
  "currency": "AED",
  "coverage": "",
  "eligibility": "",
  "benefits": []
}