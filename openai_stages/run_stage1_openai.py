"""
run_stage1_openai.py - NUTS-2 Region → Automotive Companies
Refactored to use OpenAI GPT-5 Mini (same pattern as llm_enricher.py)

Usage: python run_stage1_openai.py
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

OUTPUT_DIR = "prompt_iterations/stage1_v1_outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# All German NUTS-2 regions
ALL_REGIONS = {
    "DE11": "Stuttgart", "DE12": "Karlsruhe", "DE13": "Freiburg", "DE14": "Tübingen",
    "DE21": "Oberbayern", "DE22": "Niederbayern", "DE23": "Oberpfalz", "DE24": "Oberfranken",
    "DE25": "Mittelfranken", "DE26": "Unterfranken", "DE27": "Schwaben",
    "DE30": "Berlin", "DE40": "Brandenburg", "DE50": "Bremen", "DE60": "Hamburg",
    "DE71": "Darmstadt", "DE72": "Gießen", "DE73": "Kassel",
    "DE80": "Mecklenburg-Vorpommern",
    "DE91": "Braunschweig", "DE92": "Hannover", "DE93": "Lüneburg", "DE94": "Weser-Ems",
    "DEA1": "Düsseldorf", "DEA2": "Köln", "DEA3": "Münster", "DEA4": "Detmold", "DEA5": "Arnsberg",
    "DEB1": "Koblenz", "DEB2": "Trier", "DEB3": "Rheinhessen-Pfalz",
    "DEC0": "Saarland",
    "DED2": "Dresden", "DED4": "Chemnitz", "DED5": "Leipzig",
    "DEE0": "Sachsen-Anhalt", "DEF0": "Schleswig-Holstein", "DEG0": "Thüringen",
}

# Priority automotive regions
PRIORITY_REGIONS = {
    "DE11": "Stuttgart", "DE21": "Oberbayern", "DE91": "Braunschweig",
    "DE22": "Niederbayern", "DE14": "Tübingen", "DE27": "Schwaben",
    "DEA1": "Düsseldorf", "DEA2": "Köln", "DE71": "Darmstadt",
    "DEC0": "Saarland", "DE92": "Hannover", "DED2": "Dresden",
    "DE12": "Karlsruhe", "DEA5": "Arnsberg", "DE25": "Mittelfranken",
}

# Test regions
TEST_REGIONS = {
    "DE11": "Stuttgart",
    "DE21": "Oberbayern",
    "DE91": "Braunschweig",
}

# Remaining regions (not yet processed)
REMAINING_REGIONS = {
    "DE13": "Freiburg",
    "DE23": "Oberpfalz", "DE24": "Oberfranken", "DE26": "Unterfranken",
    "DE30": "Berlin", "DE40": "Brandenburg", "DE50": "Bremen", "DE60": "Hamburg",
    "DE72": "Gießen", "DE73": "Kassel",
    "DE80": "Mecklenburg-Vorpommern",
    "DE93": "Lüneburg", "DE94": "Weser-Ems",
    "DEA3": "Münster", "DEA4": "Detmold",
    "DEB1": "Koblenz", "DEB2": "Trier", "DEB3": "Rheinhessen-Pfalz",
    "DED4": "Chemnitz", "DED5": "Leipzig",
    "DEE0": "Sachsen-Anhalt", "DEF0": "Schleswig-Holstein", "DEG0": "Thüringen",
}


# ============================================================
# PROMPT
# ============================================================

def build_prompt(nuts2_code: str, nuts2_name: str) -> str:
    return f"""You are an expert in the European automotive industry.

TASK:
For the German NUTS-2 region "{nuts2_code} — {nuts2_name}", identify the 3 most
significant automotive companies that operate production or manufacturing facilities
in this region.

Include ONLY companies with real automotive manufacturing presence.

COMPANY TYPES TO INCLUDE:
- OEMs (vehicle manufacturers)
- Tier-1 suppliers (direct suppliers to OEMs)
- Tier-2 suppliers ONLY if they represent significant regional employment or strategic importance

DO NOT include:
- Sales offices
- Corporate headquarters without manufacturing
- Logistics centers
- R&D-only sites without production
- Small workshops or niche firms

FOR EACH COMPANY, PROVIDE:
- name: Official company name
- type: "OEM", "Tier-1", or "Tier-2"
- hq_in_region: true / false

RELIABILITY RULES:
- If unsure whether a company has manufacturing in this region, DO NOT include it
- Prefer well-documented, widely known facilities
- Do NOT guess or speculate

OUTPUT FORMAT:
Return ONLY valid JSON in the following structure (no markdown, no explanations):

{{
  "nuts2_code": "{nuts2_code}",
  "nuts2_name": "{nuts2_name}",
  "companies": [
    {{
      "name": "Company Name",
      "type": "OEM",
      "hq_in_region": true
    }}
  ]
}}

IMPORTANT:
- Return EXACTLY 3 companies (most significant only).
"""


# ============================================================
# LLM CALL (OpenAI pattern from llm_enricher.py)
# ============================================================

def run_stage1(nuts2_code: str, nuts2_name: str) -> dict:
    """
    Identify automotive companies in a NUTS-2 region using GPT-5 Mini.
    """
    
    prompt = build_prompt(nuts2_code, nuts2_name)
    
    # Call GPT-5 Mini (same pattern as llm_enricher.py)
    try:
        response = client.responses.create(
            model=MODEL,
            input=prompt
        )
        response_text = response.output_text
        print(f"[STAGE1] Raw response for {nuts2_code}: {response_text[:100]}...")
    except Exception as e:
        print(f"WARNING: LLM call failed for {nuts2_code} - {e}")
        response_text = ""
    
    # Parse JSON response
    try:
        # Try to find JSON object (strip code fences if present)
        cleaned = response_text.strip()
        cleaned = re.sub(r"^```(?:json)?", "", cleaned, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()

        json_match = re.search(r'\{.*\}', cleaned, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group(0))
        else:
            data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        print(f"WARNING: Failed to parse JSON for {nuts2_code} - {e}")
        print(f"[STAGE1] Full response for {nuts2_code}: {response_text}")
        data = {
            "nuts2_code": nuts2_code,
            "nuts2_name": nuts2_name,
            "companies": []
        }
    
    # Ensure required fields
    data["nuts2_code"] = nuts2_code
    data["nuts2_name"] = nuts2_name
    data["version"] = "stage1_v1_openai"
    data["date"] = str(date.today())
    data["model"] = MODEL
    
    if "companies" not in data:
        data["companies"] = []

    data["companies"] = data["companies"][:3]
    
    # Save output
    out_file = os.path.join(OUTPUT_DIR, f"stage1_{nuts2_code}.json")
    with open(out_file, "w") as f:
        json.dump(data, f, indent=2)
    
    print(f"✅ Stage 1 saved: {out_file} ({len(data['companies'])} companies)")
    
    return data


# ============================================================
# BATCH RUNNER
# ============================================================

def run_batch(regions: dict):
    """Run Stage 1 for multiple regions."""
    
    print("=" * 60)
    print("STAGE 1: NUTS-2 → Companies")
    print(f"Model: {MODEL}")
    print(f"Regions: {len(regions)}")
    print("=" * 60)
    
    results = []
    total_companies = 0
    
    for idx, (code, name) in enumerate(regions.items(), 1):
        print(f"\n[{idx}/{len(regions)}] Processing {code} - {name}...")
        
        data = run_stage1(code, name)
        results.append(data)
        total_companies += len(data.get("companies", []))
    
    print("\n" + "=" * 60)
    print("STAGE 1 COMPLETE")
    print(f"Regions processed: {len(results)}")
    print(f"Total companies: {total_companies}")
    print(f"Output: {OUTPUT_DIR}")
    print("=" * 60 + "\n")
    
    return results


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Stage 1: Identify companies in NUTS-2 regions')
    parser.add_argument('--test', action='store_true', help='Test with 3 regions')
    parser.add_argument('--priority', action='store_true', help='Priority regions (15)')
    parser.add_argument('--all', action='store_true', help='All regions (38)')
    parser.add_argument('--remaining', action='store_true', help='Remaining unprocessed regions (23)')
    parser.add_argument('--region', type=str, help='Single region code (e.g., DE11)')
    args = parser.parse_args()

    if args.region:
        name = ALL_REGIONS.get(args.region, "Unknown")
        run_stage1(args.region, name)
    elif args.all:
        run_batch(ALL_REGIONS)
    elif args.remaining:
        run_batch(REMAINING_REGIONS)
    elif args.test:
        run_batch(TEST_REGIONS)
    else:
        # Default to priority
        run_batch(PRIORITY_REGIONS)
