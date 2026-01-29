"""
ENRICHER PROMPT TESTING
Test and optimize enricher prompts for identifying components
Individual testing for speed and quality optimization
"""

import json
import time
from datetime import datetime
from typing import Dict, List
from prompt_benchmark_test import PromptBenchmark


class EnricherPromptTester(PromptBenchmark):
    """
    Test harness for enricher prompt optimization
    """
    
    def __init__(self, model="mistral:7b-q4_k_m", debug=True):
        super().__init__(model, debug)
        self.test_results = []
    
    def test_prompt(self, hs_code: str, description: str, 
                   custom_prompt: str = None) -> Dict:
        """
        Test enricher prompt on single HS code
        
        Args:
            hs_code: HS code to test
            description: Product description
            custom_prompt: Optional custom prompt to test
        
        Returns:
            Test result with quality and performance metrics
        """
        
        if self.debug:
            print(f"\n[ENRICHER] Testing {hs_code}...", end=" ")
        
        # Default prompt
        if not custom_prompt:
            custom_prompt = f"""Identify exactly 4 main components of {description} for HS code {hs_code}.

For each component provide:
1. Component name (specific, not generic)
2. Cost share (0.0-1.0, sum to 1.0)
3. Function description (brief)
4. Subsystem (Powertrain/Chassis/Electronics/Suspension/Braking)

Format as JSON array with 4 objects."""
        
        # Call API
        api_result = self.call_api(custom_prompt)
        
        if not api_result['success']:
            if self.debug:
                print(f"❌ {api_result['error']}")
            
            test_result = {
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
                json_str = response_text[response_text.find('['):response_text.rfind(']')+1]
                components = json.loads(json_str)
                
                # Validate
                is_valid = len(components) == 4
                
                if self.debug:
                    print(f"✅ {len(components)} components, {api_result['time']:.1f}s")
                
                test_result = {
                    'hs_code': hs_code,
                    'success': True,
                    'valid': is_valid,
                    'components': components,
                    'component_count': len(components),
                    'time': api_result['time'],
                    'tokens': api_result.get('tokens', 0),
                    'tokens_per_sec': api_result.get('tokens_per_sec', 0)
                }
            
            except json.JSONDecodeError:
                if self.debug:
                    print(f"❌ JSON parse error")
                
                test_result = {
                    'hs_code': hs_code,
                    'success': True,
                    'valid': False,
                    'error': 'JSON parse error',
                    'time': api_result['time'],
                    'tokens': api_result.get('tokens', 0)
                }
        
        self.test_results.append(test_result)
        return test_result
    
    def test_multiple(self, test_cases: List[Dict]) -> Dict:
        """
        Test enricher on multiple HS codes
        
        Args:
            test_cases: List of {'hs_code': ..., 'description': ...}
        
        Returns:
            Benchmark results
        """
        
        print(f"\n[ENRICHER] Running benchmark on {len(test_cases)} test cases")
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'type': 'enricher',
            'model': self.model,
            'test_cases': len(test_cases),
            'tests': []
        }
        
        for test_case in test_cases:
            test_result = self.test_prompt(
                test_case['hs_code'],
                test_case['description']
            )
            results['tests'].append(test_result)
        
        # Calculate summary
        results['summary'] = self.calculate_summary(results['tests'])
        
        return results
    
    def print_results(self, results: Dict):
        """Print formatted results"""
        
        print("\n" + "="*70)
        print("ENRICHER PROMPT TEST RESULTS")
        print("="*70)
        
        summary = results.get('summary', {})
        self.print_summary("Enricher", summary)
        
        print("\n" + "="*70)


# ====================================
# USAGE EXAMPLE
# ====================================

if __name__ == "__main__":
    tester = EnricherPromptTester(debug=True)
    
    # Define test cases
    test_cases = [
        {'hs_code': '8708.30', 'description': 'Brake systems'},
        {'hs_code': '8708.40', 'description': 'Steering systems'},
        {'hs_code': '8708.50', 'description': 'Suspension systems'},
        {'hs_code': '8501.52', 'description': 'Electric motors'},
    ]
    
    # Run benchmark
    results = tester.test_multiple(test_cases)
    
    # Print results
    tester.print_results(results)
    
    # Save results
    tester.save_results(results)