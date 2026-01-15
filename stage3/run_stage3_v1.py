import json
import os
import requests
import re
from datetime import date

# ===============================
# CONFIG
# ===============================
MODEL = "mistral:7b"
STAGE2_INPUT_DIR = "prompt_iterations/stage2_v1_outputs"
STAGE3_OUTPUT_DIR = "prompt_iterations/stage3_v1_outputs"

os.makedirs(STAGE3_OUTPUT_DIR, exist_ok=True)

OLLAMA_URL = "http://localhost:11434/api/generate"

# ===============================
# PROMPT FUNCTION
# ===============================
def build_prompt(company, plant_name, city, nuts2_code, nuts2_name):
    return f"""
You are an expert on automotive manufacturing.

TASK:
For the following factory, list ONLY the main CATEGORIES of components or products
manufactured at THIS SPECIFIC facility.

FACTORY:
Company: {company}
Plant: {plant_name}
City: {city}
Region: {nuts2_code} – {nuts2_name}

RULES:
- Focus ONLY on this factory (not other plants of the company)
- Use BROAD component categories (not specific vehicle models)
- Categories must reflect actual manufacturing activities
- If uncertain, include the category with LOWER confidence
- Do NOT speculate beyond reasonable industry knowledge

For each category, specify:
- category name
- whether it is ICE-specific, EV-specific, or Shared
- confidence level (high / medium / low)

OUTPUT FORMAT (JSON ONLY):
{{
  "company": "{company}",
  "plant": "{plant_name}",
  "city": "{city}",
  "nuts2_code": "{nuts2_code}",
  "components": [
    {{
      "category": "...",
      "ice_ev_type": "ICE | EV | Shared",
      "confidence": "high | medium | low"
    }}
  ]
}}
"""

# ===============================
# RUN STAGE 3
# ===============================
def run_stage3():
    for filename in os.listdir(STAGE2_INPUT_DIR):
        if not filename.endswith(".json"):
            continue

        with open(os.path.join(STAGE2_INPUT_DIR, filename), "r") as f:
            stage2_data = json.load(f)

        company = stage2_data["company"]
        nuts2_code = stage2_data["nuts2_code"]
        nuts2_name = stage2_data["nuts2_name"]

        for plant in stage2_data["plants"]:
            plant_name = plant["plant_name"]
            city = plant["city"]

            prompt = build_prompt(company, plant_name, city, nuts2_code, nuts2_name)

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
                print(f"⚠️ No JSON for {plant_name}")
                continue

            output = json.loads(match.group(0))
            output["version"] = "stage3_v1"
            output["date"] = str(date.today())

            safe_plant = plant_name.replace(" ", "_").replace("/", "_")
            out_file = f"stage3_{nuts2_code}_{safe_plant}.json"

            with open(os.path.join(STAGE3_OUTPUT_DIR, out_file), "w") as f:
                json.dump(output, f, indent=2)

            print(f"✅ Saved Stage-3 output: {out_file}")

if __name__ == "__main__":
    run_stage3()

