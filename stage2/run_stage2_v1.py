import json
import os
import requests
import re
from datetime import date

# ===============================
# CONFIG
# ===============================
MODEL = "mistral:7b"
STAGE1_INPUT_DIR = "prompt_iterations/stage1_v1_outputs"
STAGE2_OUTPUT_DIR = "prompt_iterations/stage2_v1_outputs"

os.makedirs(STAGE2_OUTPUT_DIR, exist_ok=True)

OLLAMA_URL = "http://localhost:11434/api/generate"

# ===============================
# PROMPT FUNCTION
# ===============================
def build_prompt(company_name, nuts2_code, nuts2_name):
    return f"""
You are an expert on the German automotive industry.

TASK:
For the company "{company_name}" in the German NUTS-2 region "{nuts2_code} – {nuts2_name}",
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

OUTPUT FORMAT (JSON ONLY, no explanations):
{{
  "company": "{company_name}",
  "nuts2_code": "{nuts2_code}",
  "nuts2_name": "{nuts2_name}",
  "plants": [
    {{
      "plant_name": "...",
      "city": "...",
      "primary_function": "..."
    }}
  ]
}}
"""

# ===============================
# RUN STAGE 2
# ===============================
def run_stage2():
    for filename in os.listdir(STAGE1_INPUT_DIR):
        if not filename.endswith(".json"):
            continue

        with open(os.path.join(STAGE1_INPUT_DIR, filename), "r") as f:
            stage1_data = json.load(f)

        nuts2_code = stage1_data["nuts2_code"]
        nuts2_name = stage1_data["nuts2_name"]

        for company in stage1_data["companies"]:
            company_name = company["name"]

            prompt = build_prompt(company_name, nuts2_code, nuts2_name)

            response = requests.post(
                OLLAMA_URL,
                json={
                    "model": MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.2
                },
                timeout=120
            )

            raw = response.json().get("response", "")

            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if not match:
                print(f"⚠️ No JSON for {company_name} in {nuts2_code}")
                continue

            output = json.loads(match.group(0))
            output["version"] = "stage2_v1"
            output["date"] = str(date.today())

            safe_name = company_name.replace(" ", "_").replace("/", "_")
            out_file = f"stage2_{nuts2_code}_{safe_name}.json"

            with open(os.path.join(STAGE2_OUTPUT_DIR, out_file), "w") as f:
                json.dump(output, f, indent=2)

            print(f"✅ Saved Stage-2 output: {out_file}")

if __name__ == "__main__":
    run_stage2()

