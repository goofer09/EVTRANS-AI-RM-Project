import json
from openai import OpenAI
from datetime import datetime

client = OpenAI()

SCORER_V4_PROMPT = """
You are an expert in automotive engineering, manufacturing systems, and industrial transition analysis.

Your task is to evaluate how vulnerable or adaptable a vehicle component is during the transition
from internal combustion engine (ICE) vehicles to electric vehicles (EVs).

Component:
"{component_name}"

Score the component on the following SIX dimensions (0–100):

1. technical_compatibility:
   Can this component technically exist in EV architectures?
   (Low = ICE-specific, High = EV-compatible)

2. manufacturing_feasibility:
   Can existing manufacturing equipment, processes, and skills be repurposed for EV components?
   (Low = difficult to repurpose, High = easy to repurpose)

3. supply_chain_concentration:
   How concentrated is the supplier base?
   (Low = many interchangeable suppliers, High = few specialized suppliers)

4. demand_stability:
   Expected demand stability after the ICE-to-EV transition.
   (Low = demand collapse, High = stable or growing demand)

5. value_added:
   Economic and skill intensity of production.
   (Low = commoditized, High = high value-added and skill-intensive)

6. regulatory_exposure:
   Exposure to ICE phase-out regulation.
   (Low = strongly exposed to regulation, High = largely unaffected)

IMPORTANT SCORING RULES:
- Scores must be integers between 20 and 90
- Avoid extreme values unless strongly justified
- Low scores indicate ICE lock-in
- High scores indicate EV adaptability

Provide ONE concise sentence of reasoning per dimension.
Explicitly reference the ICE-to-EV transition where relevant.

Return EXACTLY ONE valid JSON object.
Do NOT include text before or after the JSON.
Do NOT include markdown.

The JSON MUST have this structure and NOTHING else:

{
  "component": "{component_name}",
  "technical_compatibility": 0,
  "manufacturing_feasibility": 0,
  "supply_chain_concentration": 0,
  "demand_stability": 0,
  "value_added": 0,
  "regulatory_exposure": 0,
  "reasoning": {
    "technical_compatibility": "one short sentence",
    "manufacturing_feasibility": "one short sentence",
    "supply_chain_concentration": "one short sentence",
    "demand_stability": "one short sentence",
    "value_added": "one short sentence",
    "regulatory_exposure": "one short sentence"
  }
}
"""

TEST_COMPONENTS = [
    "Fuel Injection System",
    "Brake Calipers",
    "Electric Drive Inverter"
]

def main():
    results = []

    for component in TEST_COMPONENTS:
        prompt = SCORER_V4_PROMPT.format(component_name=component)

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )

        output = json.loads(response.choices[0].message.content)
        output["tested_at"] = datetime.now().isoformat()
        results.append(output)

        print(f"✅ Scored: {component}")

    with open("scorer_tests/scorer_v4_test_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print("✅ Test results saved to scorer_tests/scorer_v4_test_results.json")

if __name__ == "__main__":
    main()

