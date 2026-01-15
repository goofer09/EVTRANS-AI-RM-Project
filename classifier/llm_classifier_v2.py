import json
from typing import List, Dict
from llm_enricher import LLMClient


class ComponentClassifier:
    """
    Classifier v2
    Task: Classify vehicle components by EV transition exposure.
    """

    def __init__(self):
        self.client = LLMClient()

    def build_prompt(self, component_name: str, hs_code: int) -> str:
        return f"""
You are an automotive engineering and EV-transition expert.

Your task is to classify a SINGLE vehicle component according to
its relevance in the transition from ICE vehicles to EVs.

DEFINITIONS (use exactly these):

ICE_ONLY:
- Component is specific to internal combustion technology
- Becomes obsolete or largely unnecessary in BEVs

EV_ONLY:
- Component exists primarily because of electric drivetrains

SHARED:
- Component is required in both ICE vehicles and EVs
- May change slightly in design, but function remains

IMPORTANT RULES:
- Default to SHARED unless the component is clearly drivetrain-specific
- Chassis, body, suspension, braking, mounting, safety → usually SHARED
- Exhaust, fuel, engine internals → usually ICE_ONLY

OUTPUT FORMAT (STRICT JSON ONLY — NO EXTRA TEXT):

{{
  "component": "{component_name}",
  "classification": "ICE_ONLY | EV_ONLY | SHARED",
  "confidence": <float between 0 and 1>,
  "reasoning": "<one short sentence explaining the classification>"
}}

HS CODE CONTEXT: {hs_code}
COMPONENT TO CLASSIFY: {component_name}
"""

    def classify_component(self, component_name: str, hs_code: int) -> Dict:
        prompt = self.build_prompt(component_name, hs_code)
        response = self.client.run(prompt)

        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON returned for {component_name}: {response}") from e

    def classify_components(self, components: List[str], hs_code: int) -> List[Dict]:
        results = []
        for comp in components:
            try:
                result = self.classify_component(comp, hs_code)
                results.append(result)
            except Exception as e:
                print(f"WARNING: Failed to classify {comp}: {e}")
        return results

