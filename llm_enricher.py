import requests
import json
import re

class SubComponentEnricher:
    """
    LLM Call #1: Generate list of sub-components from HS code description
    """
    def enrich(self, hs_code: str, description: str) -> list:
        """
        Query LLM to get TOP 2 components for an HS code
        Returns: [
            {
                "name": "Component A",
                "description": "...",
                "function": "...",
                "subsystem": "..."
            },
            ...
        ]
        """

        prompt = f"""You are an automotive engineering expert. For HS Code {hs_code} ({description}), identify the TOP 2 most critical physical components by importance.

Return ONLY valid JSON (no markdown, no explanations):
[
  {{
    "name": "Component Name",
    "function": "Primary function",
    "subsystem": "Subsystem (Powertrain/Drivetrain/Chassis/Electronics/etc)"
  }}
]

Requirements:
- Exactly 2 components
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

            # Validate and extract top 2
            if isinstance(components_data, list):
                results = []
                for component in components_data[:2]:  # Take max 2
                    if 'name' in component:
                        results.append({
                            'name': component['name'],
                            'function': component.get('function', ''),
                            'subsystem': component.get('subsystem', '')
                        })

                if results:
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
            result = [
                {
                    'name': comp,
                    'function': '',
                    'subsystem': ''
                }
                for comp in components[:2]
            ]
            return result

        # Last resort fallback
        return [
            {
                'name': 'Primary Component',
                'function': 'Primary function',
                'subsystem': 'Subsystem'
            },
            {
                'name': 'Secondary Component',
                'function': 'Secondary function',
                'subsystem': 'Subsystem'
            }
        ]
if __name__ == "__main__":
    enricher = SubComponentEnricher()
    components = enricher.enrich("8708.30", "Brake systems")
    print(json.dumps(components, indent=2))