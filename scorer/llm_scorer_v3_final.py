import requests
import json
import re


class ComponentScorer:
    def __init__(self, model="mistral:7b"):
        self.model = model

    def score_components(self, components, hs_code):
        results = []

        for comp in components:
            # Robust component name extraction
            if isinstance(comp, dict):
                component_name = comp.get("component", "").strip()
            elif isinstance(comp, str):
                component_name = comp.strip()
            else:
                component_name = ""

            if not component_name:
                results.append({
                    "component": "",
                    "technical_compatibility": 0,
                    "manufacturing_feasibility": 0,
                    "supply_chain_concentration": 0,
                    "demand_stability": 0,
                    "value_added": 0,
                    "regulatory_exposure": 0,
                    "reasoning": "Parsing failure"
                })
                continue

            prompt = f"""
You are an expert in automotive manufacturing and electrification.

Your task is to score the following vehicle component for the ICE-to-EV transition.

Component:
"{component_name}"

Return EXACTLY ONE valid JSON object.
Do NOT include explanations outside JSON.
Do NOT include multiple JSON objects.
Do NOT repeat yourself.

The JSON MUST have this structure and NOTHING else:

{{
  "component": "{component_name}",
  "technical_compatibility": 0-100,
  "manufacturing_feasibility": 0-100,
  "supply_chain_concentration": 0-100,
  "demand_stability": 0-100,
  "value_added": 0-100,
  "regulatory_exposure": 0-100,
  "reasoning": {{
    "technical_compatibility": "one short sentence",
    "manufacturing_feasibility": "one short sentence",
    "supply_chain_concentration": "one short sentence",
    "demand_stability": "one short sentence",
    "value_added": "one short sentence",
    "regulatory_exposure": "one short sentence"
  }}
}}

Rules:
- Scores must be integers
- Reasoning must be brief
- Output MUST start with {{ and end with }}
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

                raw_text = response.json().get("response", "")

                # ✅ SAFETY: extract ONLY first JSON object
                json_match = re.search(r"\{.*\}", raw_text, re.DOTALL)
                if not json_match:
                    raise ValueError("No valid JSON found")

                parsed = json.loads(json_match.group(0))

                results.append({
                    "component": parsed["component"],
                    "technical_compatibility": int(parsed["technical_compatibility"]),
                    "manufacturing_feasibility": int(parsed["manufacturing_feasibility"]),
                    "supply_chain_concentration": int(parsed["supply_chain_concentration"]),
                    "demand_stability": int(parsed["demand_stability"]),
                    "value_added": int(parsed["value_added"]),
                    "regulatory_exposure": int(parsed["regulatory_exposure"]),
                    "reasoning": parsed["reasoning"]
                })

            except Exception as e:
                print(f"WARNING: Scoring failed for {component_name}: {e}")
                results.append({
                    "component": component_name,
                    "technical_compatibility": 0,
                    "manufacturing_feasibility": 0,
                    "supply_chain_concentration": 0,
                    "demand_stability": 0,
                    "value_added": 0,
                    "regulatory_exposure": 0,
                    "reasoning": "Parsing failure"
                })

        return results

