import requests
import json
import re

class ComponentScorer:
    def __init__(self, model="mistral:7b"):
        self.model = model

    def score_components(self, components, hs_code):
        scored = []

        for comp in components:
            component_name = comp.get("component") or comp.get("name")
            if not component_name:
                continue

            prompt = f"""
You are an expert in automotive engineering and industrial transition analysis.

Your task is to score how vulnerable or adaptable a vehicle component is during
the transition from internal combustion engine (ICE) vehicles to electric vehicles (EVs).

Component:
"{component_name}"

Score the component on the following SIX dimensions (0–100):

1. technical_compatibility:
   Can this component technically exist in EV architectures?
   (Low = ICE-specific, High = EV-compatible)

2. manufacturing_feasibility:
   Can existing manufacturing equipment be repurposed for EV components?
   (Low = difficult to repurpose, High = easy to repurpose)

3. supply_chain_concentration:
   How concentrated is the supplier base?
   (Low = many suppliers, High = few specialized suppliers)

4. demand_stability:
   Expected demand stability after EV transition.
   (Low = demand collapse, High = stable or growing demand)

5. value_added:
   Skill, complexity, and economic value of production.
   (Low = commoditized, High = high value-added)

6. regulatory_exposure:
   Exposure to ICE phase-out regulation.
   (Low = strongly regulated/at risk, High = largely unaffected)

IMPORTANT RULES:
- Scores must be between 20 and 90
- Avoid extreme values unless absolutely necessary
- Low scores indicate ICE lock-in
- High scores indicate EV adaptability
- Provide ONE concise sentence of reasoning per dimension
- Explicitly reference EV transition or ICE phase-out in reasoning

Return ONLY valid JSON in this format:

{{
  "technical_compatibility": 0,
  "manufacturing_feasibility": 0,
  "supply_chain_concentration": 0,
  "demand_stability": 0,
  "value_added": 0,
  "regulatory_exposure": 0,
  "reasoning": {{
    "technical_compatibility": "...",
    "manufacturing_feasibility": "...",
    "supply_chain_concentration": "...",
    "demand_stability": "...",
    "value_added": "...",
    "regulatory_exposure": "..."
  }}
}}
"""

            try:
                response = requests.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "temperature": 0.2
                    },
                    timeout=180
                )

                raw = response.json().get("response", "")
                json_match = re.search(r"\{.*\}", raw, re.DOTALL)
                if not json_match:
                    raise ValueError("No JSON found in LLM response")

                parsed = json.loads(json_match.group(0))

                parsed["component"] = component_name
                scored.append(parsed)

            except Exception as e:
                print(f"WARNING: Scoring failed for {component_name}: {e}")
                scored.append({
                    "component": component_name,
                    "technical_compatibility": 50,
                    "manufacturing_feasibility": 50,
                    "supply_chain_concentration": 50,
                    "demand_stability": 50,
                    "value_added": 50,
                    "regulatory_exposure": 50,
                    "reasoning": {
                        "technical_compatibility": "Fallback score due to parsing failure.",
                        "manufacturing_feasibility": "Fallback score due to parsing failure.",
                        "supply_chain_concentration": "Fallback score due to parsing failure.",
                        "demand_stability": "Fallback score due to parsing failure.",
                        "value_added": "Fallback score due to parsing failure.",
                        "regulatory_exposure": "Fallback score due to parsing failure."
                    }
                })

        return scored

