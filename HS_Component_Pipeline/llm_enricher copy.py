import requests
import json
import re

class SubComponentEnricher:
    """
    LLM Call #1: Generate list of sub-components from HS code description
    """
    def enrich(self, hs_code: str, description: str) -> list:
        """
        Query LLM to get TOP 4 components for an HS code
        Returns: [
            {
                "name": "Component A",
                "cost_share": 0.35,
                "description": "...",
                "function": "...",
                "subsystem": "..."
            },
            ...
        ]
        """

        prompt = f"""You are an automotive engineering expert. For HS Code {hs_code} ({description}), identify the TOP 4 most critical physical components by cost and importance.

Return ONLY valid JSON (no markdown, no explanations):
[
  {{
    "name": "Component Name",
    "cost_share": 0.30,
    "description": "Brief description",
    "function": "Primary function",
    "subsystem": "Subsystem (Powertrain/Drivetrain/Chassis/Electronics/etc)"
  }}
]

Requirements:
- Exactly 4 components
- cost_share must sum to 1.0
- Rank by cost (highest first)
- Use precise engineering terms
- Focus on combustion-engine vehicles"""

        # Call Mistral
        try:
            response = requests.post(
                'http://localhost:11434/api/generate',
                json={
                    'model': 'mistral:7b',
                    'prompt': prompt,
                    'stream': False,
                    'temperature': 0.2  # Lower temperature for more consistent output
                },
                timeout=180  # Extended timeout for complex reasoning
            )
            response_text = response.json()['response']
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            print(f"WARNING: LLM call failed - {e}")
            # Fall through to last resort fallback
            response_text = ""
        except Exception as e:
            print(f"WARNING: Unexpected error calling LLM - {e}")
            response_text = ""

        # Parse JSON response
        try:
            # Extract JSON from response (in case there's extra text)
            # Try to find JSON array in response
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                components_data = json.loads(json_str)
            else:
                # If no JSON found, try parsing entire response
                components_data = json.loads(response_text)

            # Validate and extract top 4
            if isinstance(components_data, list):
                results = []
                for component in components_data[:4]:  # Take max 4
                    if 'name' in component and 'cost_share' in component:
                        results.append({
                            'name': component['name'],
                            'cost_share': float(component['cost_share']),
                            'description': component.get('description', ''),
                            'function': component.get('function', ''),
                            'subsystem': component.get('subsystem', '')
                        })

                # If we have results, normalize cost shares to sum to 1.0
                if results:
                    total_share = sum(r['cost_share'] for r in results)
                    if total_share > 0:
                        for r in results:
                            r['cost_share'] = round(r['cost_share'] / total_share, 2)

                        # Adjust last item to ensure sum is exactly 1.0
                        actual_sum = sum(r['cost_share'] for r in results)
                        if actual_sum != 1.0:
                            results[-1]['cost_share'] = round(results[-1]['cost_share'] + (1.0 - actual_sum), 2)

                    return results

        except json.JSONDecodeError as e:
            print(f"WARNING: Failed to parse JSON response - {e}")
            # Fall through to fallback

        # Fallback: Parse text response manually
        lines = response_text.strip().split('\n')
        components = []

        for line in lines:
            line = line.strip()
            if not line or len(line) < 3:
                continue

            # Remove numbering if present
            if len(line) > 0:
                if line[0].isdigit() and '.' in line:
                    line = line.split('.', 1)[1].strip()
                elif line.startswith('- '):
                    line = line[2:].strip()

            if line:
                components.append(line)

        # Convert to standard format
        if components:
            cost_share = 1.0 / len(components[:4])
            result = [
                {
                    'name': comp,
                    'cost_share': round(cost_share, 2),
                    'description': '',
                    'function': '',
                    'subsystem': ''
                }
                for comp in components[:4]
            ]
            return result

        # Last resort fallback
        return [
            {
                'name': 'Primary Component',
                'cost_share': 0.35,
                'description': 'Main component',
                'function': 'Primary function',
                'subsystem': 'Subsystem'
            },
            {
                'name': 'Secondary Component',
                'cost_share': 0.25,
                'description': 'Secondary component',
                'function': 'Secondary function',
                'subsystem': 'Subsystem'
            },
            {
                'name': 'Tertiary Component',
                'cost_share': 0.20,
                'description': 'Tertiary component',
                'function': 'Tertiary function',
                'subsystem': 'Subsystem'
            },
            {
                'name': 'Quaternary Component',
                'cost_share': 0.20,
                'description': 'Quaternary component',
                'function': 'Quaternary function',
                'subsystem': 'Subsystem'
            }
        ]
if __name__ == "__main__":
    enricher = SubComponentEnricher()
    components = enricher.enrich("8708.30", "Brake systems")
    print(json.dumps(components, indent=2))