import requests
import json
import re

class ComponentClassifierV5:
    def __init__(self, model="mistral:7b"):
        self.model = model
        self.api_url = "http://localhost:11434/api/generate"

    def classify_component(self, component_name: str):
        prompt = f"""
You are an expert in automotive engineering and powertrain transitions.

Your task is to classify whether the following vehicle component:
- disappears with the transition from ICE to EVs,
- remains necessary in both ICE and EV vehicles,
- or exists only because of electric drivetrains.

Component:
"{component_name}"

You MUST evaluate the component using the following decision order:
1. First, determine whether the component is fundamentally tied to internal combustion processes
   (fuel delivery, combustion, exhaust, engine-specific mechanics).
   If yes, classify as ICE_ONLY.
2. If not ICE_ONLY, determine whether the component exists solely due to electric drivetrain architecture
   (electric torque generation, high-voltage power flow, battery energy storage).
   If yes, classify as EV_ONLY.
3. If neither condition is met, classify the component as SHARED.

If classification is ambiguous, default to SHARED and lower the confidence accordingly.

Return ONLY valid JSON in the following format:
{{
  "classification": "ICE_ONLY | SHARED | EV_ONLY",
  "confidence": 0.55,
  "reasoning": "One short sentence explaining the classification"
}}

Strict definitions:
- ICE_ONLY: Component is fundamentally required only because of combustion engines,
  fuel systems, exhaust systems, or engine-specific mechanics.
- SHARED: Component is required for vehicle operation regardless of drivetrain type.
- EV_ONLY: Component exists only because of electric drivetrain architecture.

Rules:
- Base reasoning on physical necessity and drivetrain dependence only.
- Do NOT speculate about future redesigns or technology shifts.
- Confidence must reflect clarity of classification.
- Never use confidence = 1.0.
- Do NOT include explanations outside JSON.
"""

        response = requests.post(
            self.api_url,
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "temperature": 0.2
            },
            timeout=120
        )

        raw = response.json().get("response", "")

        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            return {
                "classification": "SHARED",
                "confidence": 0.55,
                "reasoning": "Parsing failure"
            }

        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return {
                "classification": "SHARED",
                "confidence": 0.55,
                "reasoning": "JSON decode failure"
            }

