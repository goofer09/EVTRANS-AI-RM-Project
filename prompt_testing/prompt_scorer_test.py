"""
SCORER PROMPT TESTING
Test and optimize scorer prompts for 6-dimension risk scoring
Individual testing for speed and quality optimization
"""

import json
import time
from datetime import datetime
from typing import Dict, List
from prompt_benchmark_common import PromptBenchmark


class ScorerPromptTester(PromptBenchmark):
    """
    Test harness for scorer prompt optimization
    """
    
    def __init__(self, model="mistral:7b-q4_k_m", debug=True):
        super().__init__(model, debug)
        self.test_results = []
    
    def test_prompt(self, component_name: str, hs_code: str,
                   custom_prompt: str = None) -> Dict:
        """
        Test scorer prompt on single component
        
        Args:
            component_name: Component to score
            hs_code: HS code context
            custom_prompt: Optional custom prompt to test
        
        Returns:
            Test result with quality and performance metrics
        """
        
        if self.debug:
            print(f"[SCORER] {component_name}...", end=" ")
        
        # Default prompt
        if not custom_prompt:
            custom_prompt = f"""Score vulnerability risk for {component_name} in {hs_code} on 6 dimensions (0-100).

Dimensions:
1. tech: Technology disruption risk
2. manufacturing: Manufacturing capability gap
3. supply_chain: Supply chain vulnerability
4. demand: Market demand risk
5. value: Value proposition risk
6. regulatory: Regulatory risk

Each score 0-100. Return JSON: {{"tech": X, "manufacturing": X, "supply_chain": X, "demand": X, "value": X, "regulatory": X}}"""
        
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
                scores = json.loads(json_str)
                
                # Validate
                required_dims = ['tech', 'manufacturing', 'supply_chain', 'demand', 'value', 'regulatory']
                is_valid = all(dim in scores for dim in required_dims)
                
                # Check ranges
                all_in_range = all(0 <= scores.get(dim, 0) <= 100 for dim in required_dims)
                
                avg_score = sum(scores.values()) / len(required_dims) if is_valid else 0
                
                if self.debug:
                    status = "✅" if (is_valid and all_in_range) else "❌"
                    print(f"{status} avg {avg_score:.0f}, {api_result['time']:.1f}s")
                
                test_result = {
                    'component': component_name,
                    'hs_code': hs_code,
                    'success': True,
                    'valid': is_valid and all_in_range,
                    'scores': scores,
                    'avg_score': avg_score,
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
        Test scorer on multiple components
        
        Args:
            components: List of {'name': ...}
            hs_code: HS code context
        
        Returns:
            Benchmark results
        """
        
        print(f"\n[SCORER] Running benchmark on {len(components)} components")
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'type': 'scorer',
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
        Test scorer on batch of (components, hs_code) pairs
        
        Args:
            batch_data: List of {'hs_code': ..., 'components': [...]}
        
        Returns:
            Aggregated benchmark results
        """
        
        print(f"\n[SCORER] Running batch test on {len(batch_data)} HS codes")
        
        all_results = {
            'timestamp': datetime.now().isoformat(),
            'type': 'scorer_batch',
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
        print("SCORER PROMPT TEST RESULTS")
        print("="*70)
        
        if 'batches' in results:
            # Batch results
            summary = results.get('overall_summary', {})
            self.print_summary("Scorer (Overall)", summary)
            
            for i, batch in enumerate(results['batches'], 1):
                batch_summary = batch.get('summary', {})
                print(f"\nBatch {i} ({batch['hs_code']}):")
                self.print_summary("  ", batch_summary)
        else:
            # Single batch results
            summary = results.get('summary', {})
            self.print_summary("Scorer", summary)
        
        print("\n" + "="*70)


# ====================================
# USAGE EXAMPLE
# ====================================

if __name__ == "__main__":
    tester = ScorerPromptTester(debug=True)
    
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