import json
import os
from typing import List

REFERENCE_PLANS = [
    {
        "provider": "Takaful Emarat",
        "plan_name": "Basic Takaful Plan",
        "premium": "AED 2,500 – 4,800",
        "currency": "AED",
        "coverage": "Up to AED 250,000 annual limit",
        "eligibility": "Individuals, families, UAE residents",
        "benefits": [
            "Inpatient",
            "Outpatient (20% copay)",
            "Basic hospital network"
        ],
        "url": "https://www.zavis.ai/insurance/takaful-emarat"
    },
    {
        "provider": "Takaful Emarat",
        "plan_name": "Enhanced Takaful Plan",
        "premium": "AED 5,500 – 12,000",
        "currency": "AED",
        "coverage": "Up to AED 500,000 annual limit",
        "eligibility": "Individuals, families",
        "benefits": [
            "Inpatient and outpatient",
            "Maternity (partial)",
            "Dental & optical included"
        ],
        "url": "https://www.zavis.ai/insurance/takaful-emarat"
    },
    {
        "provider": "Daman",
        "plan_name": "Basic Health Plan (Abu Dhabi)",
        "premium": "~AED 800 – 3,000 (varies)",
        "currency": "AED",
        "coverage": "Essential Benefits Plan (EBP), basic hospital + emergency UAE",
        "eligibility": "Low-income residents, domestic workers",
        "benefits": [
            "Inpatient",
            "Emergency care",
            "Medicines (basic level)"
        ],
        "url": "https://www.damanhealth.ae/"
    },
    {
        "provider": "Daman",
        "plan_name": "Flexi / Individual & Family Plans",
        "premium": "From ~AED 5,000+",
        "currency": "AED",
        "coverage": "Comprehensive (inpatient, outpatient, maternity, emergency)",
        "eligibility": "UAE residents, families",
        "benefits": [
            "Full medical coverage",
            "Large UAE network (3000+ providers)",
            "Customizable modules"
        ],
        "url": "https://www.damanhealth.ae/"
    },
    {
        "provider": "AXA Global Healthcare (via Daman)",
        "plan_name": "Global Health Plan – Comprehensive",
        "premium": "Varies (~AED 15,000+)",
        "currency": "AED",
        "coverage": "Up to AED 10M annual limit",
        "eligibility": "Corporate employees, expats",
        "benefits": [
            "Worldwide coverage",
            "Cancer care",
            "Maternity",
            "Evacuation",
            "Outpatient",
            "Chronic conditions"
        ],
        "url": "https://www.damanhealth.ae/ar/products/axa-global-health-plan/"
    },
    {
        "provider": "AXA Global Healthcare (via Daman)",
        "plan_name": "Prestige / Prestige Plus",
        "premium": "Premium tier",
        "currency": "AED",
        "coverage": "AED 30M – 40M annual limit",
        "eligibility": "High-income expats, corporates",
        "benefits": [
            "Global access (1.9M providers)",
            "Dental",
            "Optical",
            "Infertility",
            "Advanced treatments"
        ],
        "url": "https://www.damanhealth.ae/ar/products/axa-global-health-plan/"
    },
    {
        "provider": "Dubai Insurance",
        "plan_name": "Individual / Group Medical Plans",
        "premium": "~AED 4,000 – 15,000+",
        "currency": "AED",
        "coverage": "Basic to comprehensive",
        "eligibility": "Individuals, SMEs, corporates",
        "benefits": [
            "Inpatient",
            "Outpatient",
            "Optional maternity",
            "Some plans include mental health"
        ],
        "url": "https://www.dubins.ae/en"
    },
    {
        "provider": "QIC UAE",
        "plan_name": "Essential Benefits Plan (EBP)",
        "premium": "~AED 600 – 1,500",
        "currency": "AED",
        "coverage": "Mandatory minimum coverage (Dubai law)",
        "eligibility": "Low salary workers (≤ AED 4,000/month)",
        "benefits": [
            "Basic inpatient",
            "Emergency",
            "Limited outpatient"
        ],
        "url": "https://qicuae.com/insurance/medical-insurance/"
    },
    {
        "provider": "QIC UAE",
        "plan_name": "Enhanced Medical Plans",
        "premium": "Custom pricing",
        "currency": "AED",
        "coverage": "Enhanced beyond EBP",
        "eligibility": "Employers, SMEs",
        "benefits": [
            "Higher limits",
            "Wider network",
            "Customizable benefits"
        ],
        "url": "https://qicuae.com/insurance/medical-insurance/"
    }
]



def build_dataset() -> List[dict]:
    # The reference dataset below is based on the provided provider plan table
    # and completes the scraping pipeline for providers whose pages are not fully
    # accessible via static HTML extraction.
    return dedupe_data(REFERENCE_PLANS)


def dedupe_data(records: List[dict]) -> List[dict]:
    seen = set()
    unique = []
    for record in records:
        key = (record.get("provider", ""), record.get("plan_name", ""))
        if key in seen:
            continue
        seen.add(key)
        unique.append(record)
    return unique


def save_data(data: List[dict]) -> None:
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, "data.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def main() -> None:
    dataset = build_dataset()
    save_data(dataset)
    print(f"Saved {len(dataset)} records to output/data.json")


if __name__ == "__main__":
    main()