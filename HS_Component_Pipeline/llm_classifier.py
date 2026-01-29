import json
import re
from openai import OpenAI

client = OpenAI()

class ComponentClassifier:
    """
    LLM Call #2: Classify each component as ICE_ONLY, SHARED, or EV_ONLY
    """
    
    def classify(self, components: list, hs_code: str) -> list:
        """
        Classify each component
        
        Returns: [
            {
                "name": "Brake pads",
                "classification": "SHARED",
                "similarity_score": 0.85,  # mapped from confidence
                "reasoning": "..."
            },
            ...
        ]
        """
        
        results = []
        
        for component_name in components:
            prompt = f"""You are an expert in automotive engineering and powertrain transitions.

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
- Do NOT include explanations outside JSON."""

            response_text = ""
            try:
                response = client.responses.create(
                    model="gpt-5-mini",
                    input=prompt
                )
                response_text = response.output_text
                print(f"[CLASSIFIER] {component_name}: {response_text[:60]}...")
            except Exception as e:
                print(f"WARNING: Error classifying {component_name}: {e}")
                response_text = ""
            
            # Parse JSON from response
            classification_data = None
            try:
                # Try to find JSON object in response
                json_match = re.search(r'\{[^{}]*\}', response_text, re.DOTALL)
                if json_match:
                    classification_data = json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass
            
            # Extract values
            if classification_data and isinstance(classification_data, dict):
                classification = classification_data.get('classification', 'SHARED')
                confidence = classification_data.get('confidence', 0.75)
                reasoning = classification_data.get('reasoning', '')
            else:
                # Fallback
                classification = self._extract_classification_text(response_text)
                confidence = 0.5
                reasoning = "Fallback: Could not parse JSON response"
            
            # Clean classification (remove extra text like "ICE_ONLY | SHARED | EV_ONLY")
            classification = classification.strip().upper()
            if classification not in ['SHARED', 'ICE_ONLY', 'EV_ONLY']:
                # Try to extract valid classification
                if 'ICE_ONLY' in classification:
                    classification = 'ICE_ONLY'
                elif 'EV_ONLY' in classification:
                    classification = 'EV_ONLY'
                else:
                    classification = 'SHARED'
            
            # Validate confidence
            try:
                confidence = float(confidence)
                confidence = max(0.0, min(0.99, confidence))  # Cap at 0.99 per prompt rules
            except (ValueError, TypeError):
                confidence = 0.75
            
            results.append({
                'name': component_name,
                'classification': classification,
                'similarity_score': round(confidence, 2),  # Map confidence → similarity_score for compatibility
                'reasoning': reasoning
            })
        
        return results
    
    def _extract_classification_text(self, text: str) -> str:
        """Fallback: Extract classification from text"""
        text_upper = text.upper()
        
        if 'ICE_ONLY' in text_upper:
            return 'ICE_ONLY'
        elif 'EV_ONLY' in text_upper:
            return 'EV_ONLY'
        elif 'SHARED' in text_upper:
            return 'SHARED'
        
        return 'SHARED'


if __name__ == "__main__":
    classifier = ComponentClassifier()
    components = ["Brake pads", "Fuel injector", "Battery management system"]
    results = classifier.classify(components, "8708.30")
    print(json.dumps(results, indent=2))