"""
run_stage4_openai.py - Plant → Employment Estimation
Refactored to use OpenAI GPT-5 Mini (same pattern as llm_enricher.py)

Usage: python run_stage4_openai.py
"""

import json
import os
import re
from datetime import date
from openai import OpenAI

# ============================================================
# CONFIGURATION
# ============================================================

client = OpenAI()
MODEL = "gpt-5-mini"

STAGE3_INPUT_DIR = "prompt_iterations/stage3_v2_outputs"
STAGE4_OUTPUT_DIR = "prompt_iterations/stage4_v1_outputs"

os.makedirs(STAGE4_OUTPUT_DIR, exist_ok=True)

# Employment size class midpoints for aggregation
SIZE_CLASS_MIDPOINTS = {
    "Small": 250,
    "Medium": 1250,
    "Large": 3500,
    "Very Large": 7500
}


# ============================================================
# PROMPT
# ============================================================

def build_prompt(company: str, plant: str, city: str, nuts2_code: str) -> str:
    return f"""You are an expert in industrial economics and automotive manufacturing.

TASK:
Estimate the employment size of the following automotive PRODUCTION PLANT.

STRICT RULES:
- Use SIZE CLASSES primarily
- Only provide a numeric estimate if reasonably confident
- If uncertain, say so clearly
- Base estimates on known information about this specific facility

SIZE CLASSES:
- Small: <500 employees
- Medium: 500–2000 employees
- Large: 2000–5000 employees
- Very Large: >5000 employees

PLANT:
Company: {company}
Plant: {plant}
City: {city}
NUTS-2: {nuts2_code}

OUTPUT FORMAT (JSON ONLY, no markdown, no explanations):

{{
  "company": "{company}",
  "plant": "{plant}",
  "city": "{city}",
  "nuts2_code": "{nuts2_code}",
  "employment": {{
    "size_class": "Small | Medium | Large | Very Large",
    "estimate": null,
    "confidence": "high | medium | low",
    "basis": "news | annual_report | inference"
  }}
}}

Note: For "estimate", provide a number if confident, or null if uncertain.
"""


# ============================================================
# LLM CALL (OpenAI pattern from llm_enricher.py)
# ============================================================

def run_stage4_for_plant(company: str, plant: str, city: str, nuts2_code: str) -> dict:
    """
    Estimate employment at a plant using GPT-5 Mini.
    """
    
    prompt = build_prompt(company, plant, city, nuts2_code)
    
    # Call GPT-5 Mini
    try:
        response = client.responses.create(
            model=MODEL,
            input=prompt
        )
        response_text = response.output_text
        print(f"[STAGE4] Raw response for {plant}: {response_text[:80]}...")
    except Exception as e:
        print(f"WARNING: LLM call failed for {plant} - {e}")
        response_text = ""
    
    # Parse JSON response
    try:
        start = response_text.find("{")
        end = response_text.rfind("}") + 1
        if start >= 0 and end > start:
            data = json.loads(response_text[start:end])
        else:
            data = json.loads(response_text)
    except json.JSONDecodeError as e:
        print(f"WARNING: Failed to parse JSON for {plant} - {e}")
        data = {
            "company": company,
            "plant": plant,
            "city": city,
            "nuts2_code": nuts2_code,
            "employment": {
                "size_class": "Medium",
                "estimate": None,
                "confidence": "low",
                "basis": "inference"
            }
        }
    
    # Ensure required fields
    data["company"] = company
    data["plant"] = plant
    data["city"] = city
    data["nuts2_code"] = nuts2_code
    data["version"] = "stage4_v1_openai"
    data["date"] = str(date.today())
    data["model"] = MODEL
    
    # Validate employment data
    if "employment" not in data:
        data["employment"] = {
            "size_class": "Medium",
            "estimate": None,
            "confidence": "low",
            "basis": "inference"
        }
    
    emp = data["employment"]
    
    # Validate size class
    if emp.get("size_class") not in SIZE_CLASS_MIDPOINTS:
        emp["size_class"] = "Medium"
    
    # Ensure estimate is numeric or None
    estimate = emp.get("estimate")
    if estimate is not None:
        try:
            emp["estimate"] = int(estimate)
        except (ValueError, TypeError):
            emp["estimate"] = None
    
    # Save output
    safe_name = plant.replace(" ", "_").replace("/", "-")[:30]
    out_file = os.path.join(STAGE4_OUTPUT_DIR, f"stage4_v1_{nuts2_code}_{safe_name}.json")
    with open(out_file, "w") as f:
        json.dump(data, f, indent=2)
    
    size_class = emp.get("size_class", "?")
    confidence = emp.get("confidence", "?")
    estimate_str = f"{emp.get('estimate'):,}" if emp.get("estimate") else "N/A"
    print(f"    {size_class} ({confidence}) - Est: {estimate_str}")
    
    return data


# ============================================================
# BATCH RUNNER
# ============================================================

def run_stage4(regions_filter: set | None = None):
    """
    Process all Stage 3 outputs (production sites only) and estimate employment.
    """
    
    print("=" * 60)
    print("STAGE 4: Plant → Employment Estimation")
    print(f"Model: {MODEL}")
    print(f"Input: {STAGE3_INPUT_DIR}")
    print("=" * 60)
    
    if not os.path.exists(STAGE3_INPUT_DIR):
        print(f"ERROR: Stage 3 output directory not found: {STAGE3_INPUT_DIR}")
        print("Run Stage 3 first: python run_stage3_openai.py")
        return []
    
    total_plants = 0
    skipped = 0
    results = []
    
    # Employment summary
    employment_by_class = {"Small": 0, "Medium": 0, "Large": 0, "Very Large": 0}
    
    # Process each Stage 3 output file
    for filename in sorted(os.listdir(STAGE3_INPUT_DIR)):
        if not filename.endswith(".json"):
            continue
        
        filepath = os.path.join(STAGE3_INPUT_DIR, filename)
        with open(filepath, "r") as f:
            stage3_data = json.load(f)
        
        # Skip non-production sites
        if not stage3_data.get("is_production_site", False):
            skipped += 1
            continue
        
        company = stage3_data.get("company", "Unknown")
        plant = stage3_data.get("plant", "Unknown")
        city = stage3_data.get("city", "")
        nuts2_code = stage3_data.get("nuts2_code", "")
        if regions_filter and nuts2_code not in regions_filter:
            continue
        
        print(f"\n{company} - {plant}:")
        total_plants += 1
        
        data = run_stage4_for_plant(company, plant, city, nuts2_code)
        results.append(data)
        
        # Track employment distribution
        size_class = data.get("employment", {}).get("size_class", "Medium")
        if size_class in employment_by_class:
            employment_by_class[size_class] += 1
    
    print("\n" + "=" * 60)
    print("STAGE 4 COMPLETE")
    print(f"Plants processed: {total_plants}")
    print(f"Non-production skipped: {skipped}")
    print(f"\nEmployment Distribution:")
    for size_class, count in employment_by_class.items():
        midpoint = SIZE_CLASS_MIDPOINTS[size_class]
        print(f"  {size_class:12} ({midpoint:,} midpoint): {count} plants")
    print(f"\nOutput: {STAGE4_OUTPUT_DIR}")
    print("=" * 60 + "\n")
    
    return results


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    run_stage4()
