import requests
import json
import re


def safe_int(value):
    """
    Convert model outputs safely to int 0–100.
    """
    if isinstance(value, int):
        return max(0, min(100, value))
    if isinstance(value, float):
        return max(0, min(100, int(value)))
    if isinstance(value, str):
        v = value.lower().strip()
        if v in ["low", "very low"]:
            return 20
        if v in ["medium", "moderate"]:
            return 50
        if v in ["high", "very high"]:
            return 80
        try:
            return max(0, min(100, int(v)))
        except:
            return 0
    return 0


class ComponentScorer:
    def __init__(self, model="mistral:7b"):
        self.model = model

    def score_components(self, components, hs_code):
        results = []

        for comp in components:
            component_name = ""
            if isinstance(comp, dict):
                component_name = comp.get("component", "").strip()
            elif isinstance(comp, str):
                component_name = comp.strip()

            if not component_name:
                results.append(self.empty_result(""))
                continue

            prompt = f"""
You are an expert in automotive manufacturing and electrification.

Score the following component for ICE-to-EV transition.

Component: "{component_name}"

Return ONE valid JSON object only.
NO text before or after.

Format EXACTLY:

{{
  "component": "{component_name}",
  "technical_compatibility": 0-100,
  "manufacturing_feasibility": 0-100,
  "supply_chain_concentration": 0-100,
  "demand_stability": 0-100,
  "value_added": 0-100,
  "regulatory_exposure": 0-100,
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
                r = requests.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "temperature": 0.2
                    },
                    timeout=180
                )

                raw = r.json().get("response", "")
                match = re.search(r"\{.*\}", raw, re.DOTALL)
                if not match:
                    raise ValueError("No JSON found")

                parsed = json.loads(match.group(0))

                results.append({
                    "component": component_name,
                    "technical_compatibility": safe_int(parsed.get("technical_compatibility")),
                    "manufacturing_feasibility": safe_int(parsed.get("manufacturing_feasibility")),
                    "supply_chain_concentration": safe_int(parsed.get("supply_chain_concentration")),
                    "demand_stability": safe_int(parsed.get("demand_stability")),
                    "value_added": safe_int(parsed.get("value_added")),
                    "regulatory_exposure": safe_int(parsed.get("regulatory_exposure")),
                    "reasoning": parsed.get("reasoning", {})
                })

            except Exception as e:
                print(f"WARNING: Scoring failed for {component_name}: {e}")
                results.append(self.empty_result(component_name))

        return results

    def empty_result(self, component_name):
        return {
            "component": component_name,
            "technical_compatibility": 0,
            "manufacturing_feasibility": 0,
            "supply_chain_concentration": 0,
            "demand_stability": 0,
            "value_added": 0,
            "regulatory_exposure": 0,
            "reasoning": "Parsing failure"
        }

