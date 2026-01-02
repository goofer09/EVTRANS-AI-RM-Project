import requests
import json
import re

class ComponentClassifier:
    """
    LLM Call #2: Classify each component - OPTIMIZED FOR SPEED
    """
    
    def classify(self, components: list, hs_code: str) -> list:
        """
        Classify each component as SHARED, ICE_ONLY, or EV_ONLY
        """
        
        results = []
        
        for component_name in components:
            # OPTIMIZED: Minimal prompt, direct questions
            prompt = f"""For {component_name} in HS {hs_code}:
Is it in ICE only, EV only, or both (SHARED)?
Rate similarity 0-1 (0=different, 1=identical).

Return JSON: {{"classification":"?","similarity":?}}
Use SHARED, ICE_ONLY, or EV_ONLY."""

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
                    timeout=300  # Reduced from 180
                )
                response_text = response.json()['response']
            
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                print(f"WARNING: LLM timeout for {component_name}")
                response_text = ""
            except Exception as e:
                print(f"WARNING: Error classifying {component_name}")
                response_text = ""
            
            # Parse JSON from response
            classification_data = None
            try:
                # Find JSON object
                json_match = re.search(r'\{[^{}]*"classification"[^{}]*"similarity"[^{}]*\}', response_text)
                if json_match:
                    classification_data = json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass
            
            # Extract values
            if classification_data and isinstance(classification_data, dict):
                classification = classification_data.get('classification', 'SHARED')
                similarity = classification_data.get('similarity', 0.75)
            else:
                # Fallback to text parsing
                classification = self._extract_classification_text(response_text)
                similarity = self._extract_similarity_text(response_text)
            
            # Validate classification
            if classification not in ['SHARED', 'ICE_ONLY', 'EV_ONLY']:
                classification = 'SHARED'
            
            # Validate similarity
            try:
                similarity = float(similarity)
                similarity = max(0.0, min(1.0, similarity))
            except (ValueError, TypeError):
                similarity = 0.75
            
            results.append({
                'name': component_name,
                'classification': classification,
                'similarity_score': round(similarity, 2)
            })
        
        return results
    
    def _extract_classification_text(self, text: str) -> str:
        """Extract classification from text"""
        text_upper = text.upper()
        
        if 'SHARED' in text_upper:
            return 'SHARED'
        elif 'ICE' in text_upper and 'ONLY' in text_upper:
            return 'ICE_ONLY'
        elif 'EV' in text_upper and 'ONLY' in text_upper:
            return 'EV_ONLY'
        
        return 'SHARED'
    
    def _extract_similarity_text(self, text: str) -> float:
        """Extract similarity score from text"""
        
        # Look for 0.XX pattern
        matches = re.findall(r'0\.\d{1,2}', text)
        if matches:
            try:
                return float(matches[0])
            except:
                pass
        
        # Look for percentages
        matches = re.findall(r'(\d+)%', text)
        if matches:
            try:
                return int(matches[0]) / 100.0
            except:
                pass
        
        return 0.75


if __name__ == "__main__":
    classifier = ComponentClassifier()
    components = ["Brake pads", "Brake calipers", "Rotors"]
    results = classifier.classify(components, "8708.30")
    print(json.dumps(results, indent=2))