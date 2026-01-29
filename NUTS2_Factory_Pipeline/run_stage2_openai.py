"""
run_stage2_openai.py - Company → Manufacturing Plants
Refactored to use OpenAI GPT-5 Mini (same pattern as llm_enricher.py)

Usage: python run_stage2_openai.py
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

STAGE1_INPUT_DIR = "prompt_iterations/stage1_v1_outputs"
STAGE2_OUTPUT_DIR = "prompt_iterations/stage2_v1_outputs"

os.makedirs(STAGE2_OUTPUT_DIR, exist_ok=True)


# ============================================================
# PROMPT
# ============================================================

def build_prompt(company_name: str, nuts2_code: str, nuts2_name: str) -> str:
    return f"""You are an expert on the German automotive industry.

TASK:
For the company "{company_name}" in the German NUTS-2 region "{nuts2_code} — {nuts2_name}",
list ALL manufacturing plants or factories located in this region.

INCLUDE ONLY:
- Facilities with actual production or manufacturing
- Assembly plants
- Component manufacturing plants
- Powertrain, battery, or vehicle production sites

EXCLUDE:
- Corporate headquarters without manufacturing
- Sales offices
- Logistics centers
- Pure R&D facilities with no production

If the company has NO manufacturing plants in this region,
return an EMPTY list.

OUTPUT FORMAT (JSON ONLY, no markdown, no explanations):
{{
  "company": "{company_name}",
  "nuts2_code": "{nuts2_code}",
  "nuts2_name": "{nuts2_name}",
  "plants": [
    {{
      "plant_name": "Name or identifier of the plant",
      "city": "City name",
      "primary_function": "Brief description of main production activity"
    }}
  ]
}}
"""


# ============================================================
# LLM CALL (OpenAI pattern from llm_enricher.py)
# ============================================================

def run_stage2_for_company(company_name: str, nuts2_code: str, nuts2_name: str) -> dict:
    """
    Identify manufacturing plants for a company in a region using GPT-5 Mini.
    """
    
    prompt = build_prompt(company_name, nuts2_code, nuts2_name)
    
    # Call GPT-5 Mini
    try:
        response = client.responses.create(
            model=MODEL,
            input=prompt
        )
        response_text = response.output_text
        print(f"[STAGE2] Raw response for {company_name}: {response_text[:80]}...")
    except Exception as e:
        print(f"WARNING: LLM call failed for {company_name} - {e}")
        response_text = ""
    
    # Parse JSON response
    try:
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group(0))
        else:
            data = json.loads(response_text)
    except json.JSONDecodeError as e:
        print(f"WARNING: Failed to parse JSON for {company_name} - {e}")
        data = {
            "company": company_name,
            "nuts2_code": nuts2_code,
            "nuts2_name": nuts2_name,
            "plants": []
        }
    
    # Ensure required fields
    data["company"] = company_name
    data["nuts2_code"] = nuts2_code
    data["nuts2_name"] = nuts2_name
    data["version"] = "stage2_v1_openai"
    data["date"] = str(date.today())
    data["model"] = MODEL
    
    if "plants" not in data:
        data["plants"] = []
    
    # Save output
    safe_name = company_name.replace(" ", "_").replace("/", "_")[:30]
    out_file = os.path.join(STAGE2_OUTPUT_DIR, f"stage2_{nuts2_code}_{safe_name}.json")
    with open(out_file, "w") as f:
        json.dump(data, f, indent=2)
    
    print(f"✅ Stage 2 saved: {out_file} ({len(data['plants'])} plants)")
    
    return data


# ============================================================
# BATCH RUNNER
# ============================================================

def run_stage2(regions_filter: set | None = None):
    """
    Process all Stage 1 outputs and identify plants for each company.
    """
    
    print("=" * 60)
    print("STAGE 2: Company → Plants")
    print(f"Model: {MODEL}")
    print(f"Input: {STAGE1_INPUT_DIR}")
    print("=" * 60)
    
    if not os.path.exists(STAGE1_INPUT_DIR):
        print(f"ERROR: Stage 1 output directory not found: {STAGE1_INPUT_DIR}")
        print("Run Stage 1 first: python run_stage1_openai.py")
        return []
    
    total_companies = 0
    total_plants = 0
    results = []
    
    # Process each Stage 1 output file
    for filename in sorted(os.listdir(STAGE1_INPUT_DIR)):
        if not filename.endswith(".json"):
            continue
        
        filepath = os.path.join(STAGE1_INPUT_DIR, filename)
        with open(filepath, "r") as f:
            stage1_data = json.load(f)
        
        nuts2_code = stage1_data.get("nuts2_code", "")
        if regions_filter and nuts2_code not in regions_filter:
            continue
        nuts2_name = stage1_data.get("nuts2_name", "")
        companies = stage1_data.get("companies", [])
        
        print(f"\n{'─'*60}")
        print(f"Region: {nuts2_code} - {nuts2_name}")
        print(f"Companies: {len(companies)}")
        print(f"{'─'*60}")
        
        for company in companies:
            company_name = company.get("name", "Unknown")
            total_companies += 1
            
            data = run_stage2_for_company(company_name, nuts2_code, nuts2_name)
            results.append(data)
            total_plants += len(data.get("plants", []))
    
    print("\n" + "=" * 60)
    print("STAGE 2 COMPLETE")
    print(f"Companies processed: {total_companies}")
    print(f"Total plants identified: {total_plants}")
    print(f"Output: {STAGE2_OUTPUT_DIR}")
    print("=" * 60 + "\n")
    
    return results


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    run_stage2()
