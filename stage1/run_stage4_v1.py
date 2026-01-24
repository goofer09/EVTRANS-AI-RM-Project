import json
import os
import requests
from datetime import date

INPUT_FOLDER = "prompt_iterations/stage3_v2_outputs"
OUTPUT_FOLDER = "prompt_iterations/stage4_v1_outputs"

MODEL = "mistral:7b"

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def run_stage4_v1(company, plant, city, nuts2_code):
    prompt = f"""
You are an expert in industrial economics and automotive manufacturing.

TASK:
Estimate the employment size of the following automotive PRODUCTION PLANT.

STRICT RULES:
- Use SIZE CLASSES primarily
- Only provide a numeric estimate if reasonably confident
- If uncertain, say so clearly

SIZE CLASSES:
- Small: <500
- Medium: 500–2000
- Large: 2000–5000
- Very Large: >5000

PLANT:
Company: {company}
Plant: {plant}
City: {city}
NUTS-2: {nuts2_code}

OUTPUT FORMAT (JSON ONLY):

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
  }},
  "version": "stage4_v1",
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

        if not data.get("is_production_site", False):
            continue

        result = run_stage4_v1(
            data["company"],
            data["plant"],
            data["city"],
            data["nuts2_code"]
        )

        out_file = file.replace("stage3_v2", "stage4_v1")
        out_path = os.path.join(OUTPUT_FOLDER, out_file)

        with open(out_path, "w") as f:
            json.dump(result, f, indent=2)

        print(f"✅ Stage 4 v1 saved: {out_file}")


if __name__ == "__main__":
    main()

