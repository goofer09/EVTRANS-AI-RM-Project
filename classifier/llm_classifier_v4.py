import requests
import json
import re


class ComponentClassifier:
    def __init__(self, model="mistral:7b"):
        self.model = model

    def classify_components(self, components, hs_code):
        results = []

        for comp in components:
            # Robust handling of component formats
            if isinstance(comp, dict):
                component_name = comp.get("name", "")
            elif isinstance(comp, str):
                component_name = comp
            else:
                continue

            prompt = f"""
You are an expert in automotive engineering and powertrain transitions.

Your task is to classify whether the following vehicle component:
- disappears with the transition from ICE to EVs,
- remains necessary in both ICE and EV vehicles,
- or exists only because of electric drivetrains.

Component:
"{component_name}"

Return ONLY valid JSON in the following format:
{{
  "classification": "ICE_ONLY | SHARED | EV_ONLY",
  "confidence": 0.55-0.95,
  "reasoning": "One short sentence explaining the classification"
}}

Strict definitions:
- ICE_ONLY: Component is fundamentally tied to combustion engines, fuel systems, exhaust systems, or engine-specific mechanics.
- SHARED: Component is required for vehicle operation regardless of drivetrain (ICE or EV).
- EV_ONLY: Component exists only due to electric drivetrain architecture.

Rules:
- Do NOT speculate about future redesigns.
- Base reasoning on physical necessity and drivetrain dependence.
- Confidence must reflect clarity of classification.
- Never use confidence = 1.0.
- Do NOT include explanations outside JSON.
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
                    timeout=120
                )

                resp_json = response.json()
                raw_text = resp_json.get("response", "")

                json_match = re.search(r"\{.*\}", raw_text, re.DOTALL)
                if not json_match:
                    raise ValueError("No JSON object found in LLM response")

                parsed = json.loads(json_match.group(0))

                results.append({
                    "component": component_name,
                    "classification": parsed["classification"],
                    "confidence": float(parsed["confidence"]),
                    "reasoning": parsed["reasoning"]
                })

            except Exception as e:
                print(f"WARNING: Failed to parse classification for {component_name}: {e}")
                results.append({
                    "component": component_name,
                    "classification": "UNKNOWN",
                    "confidence": 0.0,
                    "reasoning": "Parsing failure"
                })

        return results

