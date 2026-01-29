"""
CLASSIFIER PROMPT TESTING
Test and optimize classifier prompts for ICE/EV/SHARED classification
Individual testing for speed and quality optimization
"""

import json
import time
from datetime import datetime
from typing import Dict, List
from prompt_benchmark_common import PromptBenchmark


class ClassifierPromptTester(PromptBenchmark):
    """
    Test harness for classifier prompt optimization
    """
    
    def __init__(self, model="mistral:7b-q4_k_m", debug=True):
        super().__init__(model, debug)
        self.test_results = []
    
    def test_prompt(self, component_name: str, hs_code: str,
                   custom_prompt: str = None) -> Dict:
        """
        Test classifier prompt on single component
        
        Args:
            component_name: Component to classify
            hs_code: HS code context
            custom_prompt: Optional custom prompt to test
        
        Returns:
            Test result with quality and performance metrics
        """
        
        if self.debug:
            print(f"[CLASSIFIER] {component_name}...", end=" ")
        
        # Default prompt
        if not custom_prompt:
            custom_prompt = f"""Classify this automotive component for {hs_code}:

Component: {component_name}

Classify as:
- ICE_ONLY: Used only in internal combustion engines
- EV_ONLY: Used only in electric vehicles
- SHARED: Used in both ICE and EV

Provide classification and similarity score (0.0-1.0) indicating confidence.

Return JSON: {{"classification": "...", "similarity_score": 0.X}}"""
        
        # Call API
        api_result = self.call_api(custom_prompt)
        
        if not api_result['success']:
            if self.debug:
                print(f"❌ {api_result['error']}")
            
            test_result = {
                'component': component_name,
                'hs_code': hs_code,
                'success': False,
                'error': api_result['error'],
                'time': api_result.get('time', 0),
                'valid': False
            }
        else:
            response_text = api_result['response']
            
            # Parse JSON
            try:
                json_str = response_text[response_text.find('{'):response_text.rfind('}')+1]
                classification = json.loads(json_str)
                
                # Validate
                is_valid = classification.get('classification') in ['ICE_ONLY', 'EV_ONLY', 'SHARED']
                has_score = 0 <= classification.get('similarity_score', 0) <= 1
                
                if self.debug:
                    status = "✅" if is_valid else "❌"
                    print(f"{status} {classification.get('classification')}, {api_result['time']:.1f}s")
                
                test_result = {
                    'component': component_name,
                    'hs_code': hs_code,
                    'success': True,
                    'valid': is_valid and has_score,
                    'classification': classification.get('classification'),
                    'similarity_score': classification.get('similarity_score', 0),
                    'time': api_result['time'],
                    'tokens': api_result.get('tokens', 0),
                    'tokens_per_sec': api_result.get('tokens_per_sec', 0)
                }
            
            except json.JSONDecodeError:
                if self.debug:
                    print(f"❌ JSON parse error")
                
                test_result = {
                    'component': component_name,
                    'hs_code': hs_code,
                    'success': True,
                    'valid': False,
                    'error': 'JSON parse error',
                    'time': api_result['time'],
                    'tokens': api_result.get('tokens', 0)
                }
        
        self.test_results.append(test_result)
        return test_result
    
    def test_multiple(self, components: List[Dict], hs_code: str) -> Dict:
        """
        Test classifier on multiple components
        
        Args:
            components: List of {'name': ...}
            hs_code: HS code context
        
        Returns:
            Benchmark results
        """
        
        print(f"\n[CLASSIFIER] Running benchmark on {len(components)} components")
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'type': 'classifier',
            'model': self.model,
            'hs_code': hs_code,
            'test_count': len(components),
            'tests': []
        }
        
        for component in components:
            comp_name = component.get('name') if isinstance(component, dict) else component
            test_result = self.test_prompt(comp_name, hs_code)
            results['tests'].append(test_result)
        
        # Calculate summary
        results['summary'] = self.calculate_summary(results['tests'])
        
        return results
    
    def test_batch(self, batch_data: List[Dict]) -> Dict:
        """
        Test classifier on batch of (components, hs_code) pairs
        
        Args:
            batch_data: List of {'hs_code': ..., 'components': [...]}
        
        Returns:
            Aggregated benchmark results
        """
        
        print(f"\n[CLASSIFIER] Running batch test on {len(batch_data)} HS codes")
        
        all_results = {
            'timestamp': datetime.now().isoformat(),
            'type': 'classifier_batch',
            'model': self.model,
            'batch_count': len(batch_data),
            'batches': []
        }
        
        for batch in batch_data:
            hs_code = batch['hs_code']
            components = batch['components']
            
            batch_result = self.test_multiple(components, hs_code)
            all_results['batches'].append(batch_result)
        
        # Aggregate summary across all batches
        all_tests = []
        for batch in all_results['batches']:
            all_tests.extend(batch.get('tests', []))
        
        all_results['overall_summary'] = self.calculate_summary(all_tests)
        
        return all_results
    
    def print_results(self, results: Dict):
        """Print formatted results"""
        
        print("\n" + "="*70)
        print("CLASSIFIER PROMPT TEST RESULTS")
        print("="*70)
        
        if 'batches' in results:
            # Batch results
            summary = results.get('overall_summary', {})
            self.print_summary("Classifier (Overall)", summary)
            
            for i, batch in enumerate(results['batches'], 1):
                batch_summary = batch.get('summary', {})
                print(f"\nBatch {i} ({batch['hs_code']}):")
                self.print_summary("  ", batch_summary)
        else:
            # Single batch results
            summary = results.get('summary', {})
            self.print_summary("Classifier", summary)
        
        print("\n" + "="*70)


# ====================================
# USAGE EXAMPLE
# ====================================

if __name__ == "__main__":
    tester = ClassifierPromptTester(debug=True)
    
    # Example 1: Test single HS code
    components = [
        {'name': 'Brake pads'},
        {'name': 'Brake rotor'},
        {'name': 'Brake caliper'},
        {'name': 'Master cylinder'}
    ]
    
    results = tester.test_multiple(components, '8708.30')
    tester.print_results(results)
    tester.save_results(results)
    
    # Example 2: Test batch (multiple HS codes)
    batch_data = [
        {
            'hs_code': '8708.30',
            'components': [
                {'name': 'Brake pads'},
                {'name': 'Brake rotor'},
                {'name': 'Brake caliper'}
            ]
        },
        {
            'hs_code': '8708.40',
            'components': [
                {'name': 'Steering column'},
                {'name': 'Steering rack'},
                {'name': 'Tie rod'}
            ]
        }
    ]
    
    # batch_results = tester.test_batch(batch_data)
    # tester.print_results(batch_results)
    # tester.save_results(batch_results)