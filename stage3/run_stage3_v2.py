import json
import os
import requests
from datetime import date

INPUT_FOLDER = "prompt_iterations/stage2_v1_outputs"
OUTPUT_FOLDER = "prompt_iterations/stage3_v2_outputs"

MODEL = "mistral:7b"

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def run_stage3_v2(company, plant_name, city, nuts2_code):
    prompt = f"""
You are an expert in automotive manufacturing and supply chains.

TASK:
Analyze the following automotive facility and determine whether it is a
REAL PRODUCTION / MANUFACTURING PLANT.

If it is NOT a production facility (e.g. R&D center, test track, office),
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
- Vehicle Assembly
- Powertrain Components
- Electric Powertrain Components
- Battery Systems
- Chassis & Suspension
- Body & Structural Parts
- Interior Systems
- Electronics & Control Units

ICE / EV LABELING:
- Use EXACTLY ONE of: ICE | EV | Shared
- ICE = combustion-dependent
- EV = exists only due to electric drivetrain
- Shared = drivetrain-agnostic

FACILITY:
Company: {company}
Plant: {plant_name}
City: {city}
NUTS-2: {nuts2_code}

OUTPUT FORMAT (JSON ONLY):

{{
  "company": "{company}",
  "plant": "{plant_name}",
  "city": "{city}",
  "nuts2_code": "{nuts2_code}",
  "is_production_site": true,
  "components": [
    {{
      "category": "ONE category from list",
      "ice_ev_type": "ICE | EV | Shared",
      "confidence": "high | medium | low"
    }}
  ],
  "version": "stage3_v2",
  "date": "{date.today()}"
}}
"""

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "temperature": 0.2
        },
        timeout=120
    )

    text = response.json().get("response", "")
    start = text.find("{")
    end = text.rfind("}") + 1
    return json.loads(text[start:end])


def main():
    for file in os.listdir(INPUT_FOLDER):
        if not file.endswith(".json"):
            continue

        path = os.path.join(INPUT_FOLDER, file)
        with open(path, "r") as f:
            data = json.load(f)

        company = data["company"]
        nuts2_code = data["nuts2_code"]
        nuts2_name = data["nuts2_name"]

        for plant in data["plants"]:
            plant_name = plant["plant_name"]
            city = plant["city"]

            result = run_stage3_v2(company, plant_name, city, nuts2_code)

            safe_name = plant_name.replace(" ", "_").replace("/", "-")
            out_file = f"stage3_v2_{nuts2_code}_{safe_name}.json"
            out_path = os.path.join(OUTPUT_FOLDER, out_file)

            with open(out_path, "w") as f:
                json.dump(result, f, indent=2)

            print(f"✅ Stage 3 v2 saved: {out_file}")


if __name__ == "__main__":
    main()

