import requests
import json
import re
from openai import OpenAI


client=OpenAI()

class SubComponentEnricher:
    """
    LLM Call: Generate list of sub-components from HS code description
    """
    def enrich(self, hs_code: str, description: str) -> list:
        """
        Query LLM to get TOP 4 components for an HS code
        Returns: [
            {
                "name": "Component A",
                "function": "...",
                "subsystem": "..."
            },
            ...
        ]
        """
        # ------------------------------
        # STARTING PROMPT (v6)
        # ------------------------------
        prompt = f"""You are an automotive engineering expert.

For HS Code {hs_code} ({description}), identify the TOP 4 most critical
physical sub-components typically included in this HS category.

Focus ONLY on tangible, manufactured vehicle components.
Do NOT include tools, software, electronic control units, sensors,
fasteners, or any non-essential accessories unless they are core to the product.

Return ONLY valid JSON (no markdown, no explanations):
[
  {{
    "name": "Component name",
    "function": "Primary mechanical or functional role",
    "subsystem": "Vehicle subsystem"
  }},
  {{
    "name": "Component name",
    "function": "Primary mechanical or functional role",
    "subsystem": "Vehicle subsystem"
  }},
  {{
    "name": "Component name",
    "function": "Primary mechanical or functional role",
    "subsystem": "Vehicle subsystem"
  }},
  {{
    "name": "Component name",
    "function": "Primary mechanical or functional role",
    "subsystem": "Vehicle subsystem"
  }}
]

Requirements:
- Exactly 4 components
- Use precise and consistent engineering terminology
- Components must be physically distinct parts
- Subsystems must reflect standard automotive system groupings
- Functions must be concise and technically accurate
- Do NOT reference EVs, ICEs, or future technology
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

        # ------------------------------
        # Parse JSON response
        # ------------------------------
        try:
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                components_data = json.loads(json_str)
            else:
                components_data = json.loads(response_text)

            results = []
            if isinstance(components_data, list):
                for component in components_data[:4]:
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

        # ------------------------------
        # Fallback: parse text lines
        # ------------------------------
        lines = response_text.strip().split('\n')
        components = []
        for line in lines:
            line = line.strip()
            if not line or len(line) < 3:
                continue
            if line[0].isdigit() and '.' in line:
                line = line.split('.', 1)[1].strip()
            elif line.startswith('- '):
                line = line[2:].strip()
            if line:
                components.append(line)

        if components:
            return [
                {'name': comp, 'function': '', 'subsystem': ''}
                for comp in components[:4]
            ]

        # ------------------------------
        # Last resort fallback
        # ------------------------------
        return [
            {'name': 'Primary Component', 'function': 'Primary function', 'subsystem': 'Subsystem'},
            {'name': 'Secondary Component', 'function': 'Secondary function', 'subsystem': 'Subsystem'},
            {'name': 'Tertiary Component', 'function': 'Tertiary function', 'subsystem': 'Subsystem'},
            {'name': 'Quaternary Component', 'function': 'Quaternary function', 'subsystem': 'Subsystem'}
        ]


if __name__ == "__main__":
    enricher = SubComponentEnricher()
    components = enricher.enrich("8708.30", "Brake systems")
    print(json.dumps(components, indent=2))


# Quick wrapper so other scripts can call it
def enrich_prompt(prompt_text: str) -> list:
    """
    This wrapper extracts HS code and description from the prompt string
    and calls SubComponentEnricher.enrich().
    """
    match = re.search(r"HS Code (\S+) \((.*?)\)", prompt_text)
    if not match:
        raise ValueError("Cannot extract HS code and description from prompt.")
    hs_code, description = match.groups()
    enricher = SubComponentEnricher()
    return enricher.enrich(hs_code, description)

