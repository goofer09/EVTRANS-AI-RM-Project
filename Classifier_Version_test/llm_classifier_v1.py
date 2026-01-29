import json
from datetime import datetime
from typing import Dict, Any

class ComponentClassifier:
    """
    Classifier v1
    Task:
    Classify a single vehicle component as ICE_ONLY, SHARED, or EV_ONLY
    """

    VERSION = "classifier_v1"
    DATE = datetime.now().strftime("%Y-%m-%d")

    SYSTEM_PROMPT = """
You are an automotive engineering expert specializing in powertrain technologies
and vehicle architecture transitions from internal combustion engines (ICE)
to battery electric vehicles (BEVs).

Your task is strictly limited to TECHNOLOGY CLASSIFICATION.
Do NOT consider economics, employment, regions, or policy.
"""

    USER_PROMPT_TEMPLATE = """
Component name: {component_name}
Component function: {component_function}
Subsystem: {subsystem}
Context HS code: {hs_code}

Task:
Classify whether this component is:

- ICE_ONLY: Used only in internal combustion engine vehicles and does not exist in battery electric vehicles.
- SHARED: Used in both internal combustion engine vehicles and battery electric vehicles.
- EV_ONLY: Primarily or exclusively used in battery electric vehicles.

Rules:
- Assume EV refers strictly to battery electric vehicles (BEVs), not hybrids.
- Focus on the physical necessity of the component in a BEV architecture.
- Ignore manufacturing feasibility, costs, or transition difficulty.
- Choose exactly ONE category.

Output format (JSON ONLY):
{{
  "classification": "ICE_ONLY | SHARED | EV_ONLY",
  "confidence": <float between 0 and 1>,
  "justification": "<one short sentence explaining the classification>"
}}
"""

    def build_prompt(self, component: Dict[str, Any], hs_code: int) -> Dict[str, str]:
        user_prompt = self.USER_PROMPT_TEMPLATE.format(
            component_name=component["name"],
            component_function=component["function"],
            subsystem=component["subsystem"],
            hs_code=hs_code
        )

        return {
            "system": self.SYSTEM_PROMPT.strip(),
            "user": user_prompt.strip()
        }

    def classify_component(self, component: Dict[str, Any], hs_code: int, llm_client) -> Dict[str, Any]:
        prompts = self.build_prompt(component, hs_code)

        response = llm_client.generate(
            system_prompt=prompts["system"],
            user_prompt=prompts["user"]
        )

        try:
            parsed = json.loads(response)
        except json.JSONDecodeError:
            raise ValueError("LLM output is not valid JSON")

        return {
            "component_name": component["name"],
            "classification": parsed["classification"],
            "confidence": parsed["confidence"],
            "justification": parsed["justification"]
        }

