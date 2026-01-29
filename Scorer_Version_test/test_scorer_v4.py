"""
llm_scorer.py - Score components on 6 dimensions for ICE-to-EV transition
Updated for GPT-5 Mini with detailed reasoning
"""

import json
import re
from openai import OpenAI

client = OpenAI()


class ComponentScorer:
    """
    LLM Call #3: Score each component on 6 dimensions (0-100)
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
                "regulatory": 92,
                "reasoning": { ... }
            },
            ...
        ]
        """
        
        results = []
        
        for component_name in components:
            prompt = f'''You are an expert in automotive engineering, manufacturing systems, and industrial transition analysis.

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

{{
  "component": "{component_name}",
  "technical_compatibility": 0,
  "manufacturing_feasibility": 0,
  "supply_chain_concentration": 0,
  "demand_stability": 0,
  "value_added": 0,
  "regulatory_exposure": 0,
  "reasoning": {{
    "technical_compatibility": "one short sentence",
    "manufacturing_feasibility": "one short sentence",
    "supply_chain_concentration": "one short sentence",
    "demand_stability": "one short sentence",
    "value_added": "one short sentence",
    "regulatory_exposure": "one short sentence"
  }}
}}'''

            response_text = ""
            try:
                response = client.responses.create(
                    model="gpt-5-mini",
                    input=prompt
                )
                response_text = response.output_text
                print(f"[SCORER] {component_name}: {response_text[:70]}...")
            except Exception as e:
                print(f"WARNING: Error scoring {component_name}: {e}")
                response_text = ""
            
            # Parse JSON from response
            score_data = None
            try:
                # Try to find JSON object in response
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    score_data = json.loads(json_match.group(0))
            except json.JSONDecodeError as e:
                print(f"WARNING: JSON parse error for {component_name}: {e}")
            
            # Extract and map scores
            if score_data and isinstance(score_data, dict):
                scores = {
                    'tech': self._validate_score(score_data.get('technical_compatibility', 50)),
                    'manufacturing': self._validate_score(score_data.get('manufacturing_feasibility', 50)),
                    'supply_chain': self._validate_score(score_data.get('supply_chain_concentration', 50)),
                    'demand': self._validate_score(score_data.get('demand_stability', 50)),
                    'value': self._validate_score(score_data.get('value_added', 50)),
                    'regulatory': self._validate_score(score_data.get('regulatory_exposure', 50))
                }
                reasoning = score_data.get('reasoning', {})
            else:
                # Fallback: default scores
                print(f"WARNING: Using fallback scores for {component_name}")
                scores = {
                    'tech': 50,
                    'manufacturing': 50,
                    'supply_chain': 50,
                    'demand': 50,
                    'value': 50,
                    'regulatory': 50
                }
                reasoning = {
                    'technical_compatibility': 'Fallback: Could not parse response',
                    'manufacturing_feasibility': 'Fallback: Could not parse response',
                    'supply_chain_concentration': 'Fallback: Could not parse response',
                    'demand_stability': 'Fallback: Could not parse response',
                    'value_added': 'Fallback: Could not parse response',
                    'regulatory_exposure': 'Fallback: Could not parse response'
                }
            
            results.append({
                'name': component_name,
                'tech': scores['tech'],
                'manufacturing': scores['manufacturing'],
                'supply_chain': scores['supply_chain'],
                'demand': scores['demand'],
                'value': scores['value'],
                'regulatory': scores['regulatory'],
                'reasoning': reasoning
            })
        
        return results
    
    def _validate_score(self, value) -> int:
        """Validate and clamp score to 20-90 range (per prompt rules)"""
        try:
            score = int(float(value))
            return max(20, min(90, score))  # Clamp to 20-90
        except (ValueError, TypeError):
            return 50  # Default middle score


if __name__ == "__main__":
    scorer = ComponentScorer()
    
    # Test with diverse components
    components = ["Brake pads", "Fuel injector", "Battery cooling system"]
    results = scorer.score(components, "8708.30")
    
    # Pretty print
    for r in results:
        print(f"\n{'='*50}")
        print(f"Component: {r['name']}")
        print(f"{'='*50}")
        print(f"  Technical Compatibility: {r['tech']}")
        print(f"  Manufacturing Feasibility: {r['manufacturing']}")
        print(f"  Supply Chain Concentration: {r['supply_chain']}")
        print(f"  Demand Stability: {r['demand']}")
        print(f"  Value Added: {r['value']}")
        print(f"  Regulatory Exposure: {r['regulatory']}")
        
        # Calculate TFS
        tfs = int(sum([r['tech'], r['manufacturing'], r['supply_chain'], 
                       r['demand'], r['value'], r['regulatory']]) / 6)
        print(f"\n  TFS Score: {tfs}/100")
        
        # Show reasoning
        if r.get('reasoning'):
            print(f"\n  Reasoning:")
            for dim, reason in r['reasoning'].items():
                print(f"    - {dim}: {reason}")