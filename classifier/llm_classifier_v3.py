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
You are an expert in automotive engineering and vehicle electrification.

Classify the following vehicle component with respect to the ICE → EV transition.

Component:
"{component_name}"

Return ONLY valid JSON in the following format:
{{
  "classification": "ICE_ONLY | SHARED | EV_ONLY",
  "confidence": 0.55-0.95,
  "reasoning": "ONE complete sentence, maximum 25 words"
}}

Rules:
- ICE_ONLY: Component tied to combustion engines, fuel systems, or exhaust systems.
- SHARED: Component required in both ICE and EV vehicles.
- EV_ONLY: Component exists only due to electric drivetrain architecture.

Constraints:
- Reasoning must be a full grammatical sentence.
- Do NOT truncate sentences.
- Do NOT include line breaks.
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
                    "confidence": parsed["confidence"],
                    "reasoning": parsed["reasoning"]
                })

            except Exception as e:
                print(f"WARNING: Failed to parse classification for {component_name}: {e}")
                results.append({
                    "component": component_name,
                    "classification": "UNKNOWN",
                    "confidence": 0.0,
                    "reasoning": "Classification could not be reliably determined."
                })

        return results

