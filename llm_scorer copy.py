"""
FIXED llm_scorer.py
Lean prompt with placeholders - forces LLM to think instead of echo
"""

import requests
import json
import re

class TransitionScorer:
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
            prompt = f"""Score {component_name} (HS {hs_code}) for ICE→EV transition (0-100):
- Technical compatibility
- Manufacturing feasibility  
- Supply chain continuity
- Market demand
- Value preservation
- Regulatory alignment

Return JSON: {{"tech":?,"manufacturing":?,"supply_chain":?,"demand":?,"value":?,"regulatory":?}}
Each score 0-100. Higher = easier transition."""

            response_text = ""
            try:
                response = requests.post(
                    'http://localhost:11434/api/generate',
                    json={
                        'model': 'mistral:7b',
                        'prompt': prompt,
                        'stream': False,
                        'temperature': 0.15
                    },
                    timeout=300
                )
                response_text = response.json()['response']
            
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                print(f"WARNING: LLM timeout for {component_name}")
                response_text = ""
            except Exception as e:
                print(f"WARNING: Error scoring {component_name}")
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
    scorer = TransitionScorer()
    
    # Test with brake system components
    components = ["Brake pads", "Brake calipers", "Rotors"]
    results = scorer.score(components, "8708.30")
    
    print(json.dumps(results, indent=2))






