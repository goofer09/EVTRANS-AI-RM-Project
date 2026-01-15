import requests
import json
from datetime import date

def build_stage1_prompt(nuts2_code, nuts2_name):
    return f"""
You are an expert in the European automotive industry.

TASK:
For the German NUTS-2 region "{nuts2_code} – {nuts2_name}", identify the most
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
Return ONLY valid JSON in the following structure:

{{
  "nuts2_code": "{nuts2_code}",
  "nuts2_name": "{nuts2_name}",
  "companies": [
    {{
      "name": "Company Name",
      "type": "OEM | Tier-1 | Tier-2",
      "hq_in_region": true
    }}
  ]
}}

Do NOT include explanations or text outside JSON.
"""

def run_stage1(nuts2_code, nuts2_name):
    prompt = build_stage1_prompt(nuts2_code, nuts2_name)

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "mistral:7b",
            "prompt": prompt,
            "stream": False,
            "temperature": 0.2
        },
        timeout=120
    )

    raw = response.json().get("response", "")
    data = json.loads(raw)

    data["version"] = "stage1_v1"
    data["date"] = str(date.today())

    out_path = f"prompt_iterations/stage1_v1_outputs/stage1_{nuts2_code}.json"
    with open(out_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"✅ Saved Stage-1 output for {nuts2_code}")

if __name__ == "__main__":
    TEST_REGIONS = [
        ("DE11", "Stuttgart"),
        ("DE71", "Darmstadt"),
        ("DE30", "Berlin")
    ]

    for code, name in TEST_REGIONS:
        run_stage1(code, name)

