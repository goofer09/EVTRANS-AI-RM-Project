"""
FIXED llm_scorer.py
Lean prompt with placeholders - forces LLM to think instead of echo
"""

import requests
import json
import re
from openai import OpenAI

client=OpenAI()

class ComponentScorer:
    """
    LLM Call #3: Score each component on 6 dimensions (0-100)
    FIXED: Lean prompt prevents template echoing
    """
    
    def score(self, components: list, hs_code: str) -> list:
        """
        Score each component on 6 dimensions for ICE-to-EV transition feasibility
        
        Input: ["Brake pads", "Brake calipers", ...]
        
        Returns: [
            {
                "name": "Brake pads",
                "tech": 85,
                "manufacturing": 90,
                "supply_chain": 88,
                "demand": 85,
                "value": 80,
                "regulatory": 92
            },
            ...
        ]
        """
        
        results = []
        
        for component_name in components:
            # FIXED PROMPT: Lean, no hardcoded example scores
            prompt = f"""You are an expert in automotive engineering, manufacturing systems, and industrial transition analysis.

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

            # Call GPT-5 Mini
        try:
            response = client.responses.create(
                model="gpt-5-mini",
                input=prompt
            )
            response_text = response.output_text
            print(f"[ENRICHER] Raw response: {response_text[:100]}...")
        except Exception as e:
            print(f"WARNING: LLM call failed - {e}")
            response_text = ""

            
            # Try to parse JSON from response
            score_data = None
            try:
                # Strategy 1: Find JSON object with regex
                json_match = re.search(
                    r'\{[^{}]*"tech"[^{}]*"manufacturing"[^{}]*"supply_chain"[^{}]*"demand"[^{}]*"value"[^{}]*"regulatory"[^{}]*\}',
                    response_text
                )
                if json_match:
                    score_data = json.loads(json_match.group(0))
                else:
                    # Strategy 2: Try parsing entire response
                    score_data = json.loads(response_text)
            
            except json.JSONDecodeError:
                # Will fall back to text parsing
                pass
            
            # Extract scores from parsed JSON
            if score_data and isinstance(score_data, dict):
                scores = {
                    'tech': self._validate_score(score_data.get('tech', 75)),
                    'manufacturing': self._validate_score(score_data.get('manufacturing', 75)),
                    'supply_chain': self._validate_score(score_data.get('supply_chain', 75)),
                    'demand': self._validate_score(score_data.get('demand', 75)),
                    'value': self._validate_score(score_data.get('value', 75)),
                    'regulatory': self._validate_score(score_data.get('regulatory', 75))
                }
            else:
                # Fallback: Parse text response manually
                scores = {
                    'tech': self._extract_score_text(response_text, 'tech'),
                    'manufacturing': self._extract_score_text(response_text, 'manufacturing'),
                    'supply_chain': self._extract_score_text(response_text, 'supply.?chain'),
                    'demand': self._extract_score_text(response_text, 'demand'),
                    'value': self._extract_score_text(response_text, 'value'),
                    'regulatory': self._extract_score_text(response_text, 'regulatory')
                }
            
            results.append({
                'name': component_name,
                'tech': scores['tech'],
                'manufacturing': scores['manufacturing'],
                'supply_chain': scores['supply_chain'],
                'demand': scores['demand'],
                'value': scores['value'],
                'regulatory': scores['regulatory']
            })
        
        return results
    
    def _validate_score(self, value) -> int:
        """
        Validate and clamp score to 0-100 range
        """
        try:
            score = int(float(value))
            return max(0, min(100, score))
        except (ValueError, TypeError):
            return 75
    
    def _extract_score_text(self, text: str, keyword: str) -> int:
        """
        Extract a 0-100 score for a given keyword from text response
        """
        pattern = rf'{keyword}[:\s]+(\d+)'
        match = re.search(pattern, text, re.IGNORECASE)
        
        if match:
            try:
                score = int(match.group(1))
                return max(0, min(100, score))
            except (ValueError, IndexError):
                pass
        
        return 75


if __name__ == "__main__":
    scorer = ComponentScorer()
    
    # Test with brake system components
    components = ["Brake pads", "Brake calipers", "Rotors"]
    results = scorer.score(components, "8708.30")
    
    print(json.dumps(results, indent=2))






