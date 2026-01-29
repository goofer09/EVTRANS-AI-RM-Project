"""
run_stage3_openai.py - Plant → Component Categories (ICE/EV/Shared)
Refactored to use OpenAI GPT-5 Mini (same pattern as llm_enricher.py)

Usage: python run_stage3_openai.py
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

STAGE2_INPUT_DIR = "prompt_iterations/stage2_v1_outputs"
STAGE3_OUTPUT_DIR = "prompt_iterations/stage3_v2_outputs"

os.makedirs(STAGE3_OUTPUT_DIR, exist_ok=True)

# Allowed component categories (closed set)
ALLOWED_CATEGORIES = [
    "Vehicle Assembly",
    "Powertrain Components",
    "Electric Powertrain Components",
    "Battery Systems",
    "Chassis & Suspension",
    "Body & Structural Parts",
    "Interior Systems",
    "Electronics & Control Units"
]


# ============================================================
# PROMPT
# ============================================================

def build_prompt(company: str, plant_name: str, city: str, nuts2_code: str) -> str:
    categories_str = "\n".join(f"- {c}" for c in ALLOWED_CATEGORIES)
    
    return f"""You are an expert in automotive manufacturing and supply chains.

TASK:
Analyze the following automotive facility and determine whether it is a
REAL PRODUCTION / MANUFACTURING PLANT.

If it is NOT a production facility (e.g. R&D center, test track, office, logistics),
return:
{{
  "is_production_site": false,
  "reason": "Short explanation"
}}

If it IS a production facility, return:
- is_production_site = true
- AT MOST 4 component categories actually produced at THIS plant

STRICT RULES:
- Only include components manufactured at THIS specific plant
- Do NOT list company-wide product portfolios
- Use ONLY the following component categories:

ALLOWED CATEGORIES:
{categories_str}

ICE / EV LABELING:
For each component, assign EXACTLY ONE of:
- ICE = combustion-dependent (engines, fuel systems, exhaust)
- EV = exists only due to electric drivetrain (batteries, e-motors, inverters)
- Shared = drivetrain-agnostic (brakes, body, interior, most electronics)

FACILITY:
Company: {company}
Plant: {plant_name}
City: {city}
NUTS-2: {nuts2_code}

OUTPUT FORMAT (JSON ONLY, no markdown, no explanations):

{{
  "company": "{company}",
  "plant": "{plant_name}",
  "city": "{city}",
  "nuts2_code": "{nuts2_code}",
  "is_production_site": true,
  "components": [
    {{
      "category": "ONE category from the allowed list",
      "ice_ev_type": "ICE | EV | Shared",
      "confidence": "high | medium | low"
    }}
  ]
}}
"""


# ============================================================
# LLM CALL (OpenAI pattern from llm_enricher.py)
# ============================================================

def run_stage3_for_plant(company: str, plant_name: str, city: str, nuts2_code: str) -> dict:
    """
    Identify components produced at a plant using GPT-5 Mini.
    """
    
    prompt = build_prompt(company, plant_name, city, nuts2_code)
    
    # Call GPT-5 Mini
    try:
        response = client.responses.create(
            model=MODEL,
            input=prompt
        )
        response_text = response.output_text
        print(f"[STAGE3] Raw response for {plant_name}: {response_text[:80]}...")
    except Exception as e:
        print(f"WARNING: LLM call failed for {plant_name} - {e}")
        response_text = ""
    
    # Parse JSON response
    try:
        # Find JSON object
        start = response_text.find("{")
        end = response_text.rfind("}") + 1
        if start >= 0 and end > start:
            data = json.loads(response_text[start:end])
        else:
            data = json.loads(response_text)
    except json.JSONDecodeError as e:
        print(f"WARNING: Failed to parse JSON for {plant_name} - {e}")
        data = {
            "company": company,
            "plant": plant_name,
            "city": city,
            "nuts2_code": nuts2_code,
            "is_production_site": False,
            "reason": "Failed to parse LLM response"
        }
    
    # Ensure required fields
    data["company"] = company
    data["plant"] = plant_name
    data["city"] = city
    data["nuts2_code"] = nuts2_code
    data["version"] = "stage3_v2_openai"
    data["date"] = str(date.today())
    data["model"] = MODEL
    
    # Validate components if production site
    if data.get("is_production_site", False):
        valid_components = []
        for comp in data.get("components", []):
            category = comp.get("category", "")
            # Validate category is in allowed list
            if category in ALLOWED_CATEGORIES:
                valid_components.append(comp)
            else:
                # Try to match partial
                for allowed in ALLOWED_CATEGORIES:
                    if category.lower() in allowed.lower() or allowed.lower() in category.lower():
                        comp["category"] = allowed
                        valid_components.append(comp)
                        break
        data["components"] = valid_components
    
    # Save output
    safe_name = plant_name.replace(" ", "_").replace("/", "-")[:30]
    out_file = os.path.join(STAGE3_OUTPUT_DIR, f"stage3_v2_{nuts2_code}_{safe_name}.json")
    with open(out_file, "w") as f:
        json.dump(data, f, indent=2)
    
    is_prod = data.get("is_production_site", False)
    comp_count = len(data.get("components", [])) if is_prod else 0
    status = f"✓ Production ({comp_count} categories)" if is_prod else f"○ Not production: {data.get('reason', 'N/A')[:30]}"
    print(f"    {status}")
    
    return data


# ============================================================
# BATCH RUNNER
# ============================================================

def run_stage3(regions_filter: set | None = None):
    """
    Process all Stage 2 outputs and classify components for each plant.
    """
    
    print("=" * 60)
    print("STAGE 3: Plant → Components (ICE/EV/Shared)")
    print(f"Model: {MODEL}")
    print(f"Input: {STAGE2_INPUT_DIR}")
    print("=" * 60)
    
    if not os.path.exists(STAGE2_INPUT_DIR):
        print(f"ERROR: Stage 2 output directory not found: {STAGE2_INPUT_DIR}")
        print("Run Stage 2 first: python run_stage2_openai.py")
        return []
    
    total_plants = 0
    production_sites = 0
    results = []
    
    # Process each Stage 2 output file
    for filename in sorted(os.listdir(STAGE2_INPUT_DIR)):
        if not filename.endswith(".json"):
            continue
        
        filepath = os.path.join(STAGE2_INPUT_DIR, filename)
        with open(filepath, "r") as f:
            stage2_data = json.load(f)
        
        company = stage2_data.get("company", "Unknown")
        nuts2_code = stage2_data.get("nuts2_code", "")
        if regions_filter and nuts2_code not in regions_filter:
            continue
        nuts2_name = stage2_data.get("nuts2_name", "")
        plants = stage2_data.get("plants", [])
        
        if not plants:
            continue
        
        print(f"\n{'─'*60}")
        print(f"Company: {company} ({nuts2_code})")
        print(f"Plants to analyze: {len(plants)}")
        print(f"{'─'*60}")
        
        for plant in plants:
            plant_name = plant.get("plant_name", "Unknown")
            city = plant.get("city", "")
            total_plants += 1
            
            data = run_stage3_for_plant(company, plant_name, city, nuts2_code)
            results.append(data)
            
            if data.get("is_production_site", False):
                production_sites += 1
    
    print("\n" + "=" * 60)
    print("STAGE 3 COMPLETE")
    print(f"Plants analyzed: {total_plants}")
    print(f"Production sites: {production_sites}")
    print(f"Non-production: {total_plants - production_sites}")
    print(f"Output: {STAGE3_OUTPUT_DIR}")
    print("=" * 60 + "\n")
    
    return results


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    run_stage3()
