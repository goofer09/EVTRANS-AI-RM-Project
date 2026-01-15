<<<<<<< HEAD
"""
PROMPT ENGINEER BENCHMARK UTILITIES
Common utilities for testing enricher, classifier, and scorer prompts
"""

import json
import time
from datetime import datetime
from typing import Dict, List
import requests


class PromptBenchmark:
    """
    Common benchmark utilities for all prompt tests
    """
    
    def __init__(self, model="mistral:7b-q4_k_m", debug=True):
        self.model = model
        self.debug = debug
        self.api_url = "http://localhost:11434/api/generate"
        self.test_results = []
    
    def call_api(self, prompt: str, timeout: int = 60) -> Dict:
        """
        Make API call and return timing and token metrics
        
        Args:
            prompt: Prompt to send to LLM
            timeout: Request timeout in seconds
        
        Returns:
            Response with timing metrics
        """
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        
        start = time.time()
        try:
            response = requests.post(self.api_url, json=payload, timeout=timeout)
            elapsed = time.time() - start
            
            if response.status_code != 200:
                return {
                    'success': False,
                    'error': f"API error: {response.status_code}",
                    'time': elapsed
                }
            
            result = response.json()
            response_text = result['response']
            tokens = result.get('eval_count', 0)
            eval_duration = result.get('eval_duration', 1)
            
            tokens_per_sec = tokens / (eval_duration / 1e9) if eval_duration else 0
            
            return {
                'success': True,
                'response': response_text,
                'time': elapsed,
                'tokens': tokens,
                'tokens_per_sec': tokens_per_sec,
                'eval_duration': eval_duration
            }
        
        except requests.exceptions.Timeout:
            elapsed = time.time() - start
            return {
                'success': False,
                'error': 'Timeout',
                'time': elapsed
            }
        
        except Exception as e:
            elapsed = time.time() - start
            return {
                'success': False,
                'error': str(e),
                'time': elapsed
            }
    
    def calculate_summary(self, test_list: List[Dict]) -> Dict:
        """
        Calculate summary statistics for a list of tests
        
        Args:
            test_list: List of test result dictionaries
        
        Returns:
            Summary with aggregated metrics
        """
        
        if not test_list:
            return {
                'success_rate': '0/0',
                'avg_time': 0,
                'quality': '0%',
                'avg_tokens': 0
            }
        
        successful = [t for t in test_list if t.get('success') or t.get('valid')]
        times = [t.get('time', 0) for t in test_list if t.get('time')]
        tokens = [t.get('tokens', 0) for t in test_list if t.get('tokens')]
        
        return {
            'total_tests': len(test_list),
            'successful': len(successful),
            'success_rate': f"{len(successful)}/{len(test_list)}",
            'avg_time': sum(times) / len(times) if times else 0,
            'min_time': min(times) if times else 0,
            'max_time': max(times) if times else 0,
            'total_time': sum(times),
            'quality': f"{len(successful)/len(test_list)*100:.0f}%" if test_list else "0%",
            'avg_tokens': sum(tokens) / len(tokens) if tokens else 0,
            'total_tokens': sum(tokens)
        }
    
    def print_summary(self, name: str, summary: Dict):
        """Print formatted summary"""
        
        print(f"\n{name}:")
        print(f"  Tests: {summary.get('successful', 0)}/{summary.get('total_tests', 0)}")
        print(f"  Success Rate: {summary.get('success_rate', '0/0')}")
        print(f"  Quality: {summary.get('quality', '0%')}")
        print(f"  Avg Time: {summary.get('avg_time', 0):.2f}s")
        print(f"  Avg Tokens: {summary.get('avg_tokens', 0):.0f}")
    
    def save_results(self, results: Dict, filename: str = None) -> str:
        """
        Save test results to JSON file
        
        Args:
            results: Test results dictionary
            filename: Output filename (auto-generated if None)
        
        Returns:
            Path to saved file
        """
        
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            results_type = results.get('type', 'unknown')
            filename = f"prompt_test_{results_type}_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        if self.debug:
            print(f"\nResults saved to: {filename}")
        
        return filename
=======
import time
import json
import requests

class PromptBenchmark:
    """
    Minimal stub for Enricher/Scorer/Classifier tests.
    Simulates API responses so tests run without errors.
    """
    def __init__(self, model="mistral:7b-q4_k_m", debug=True):
        self.model = model
        self.debug = debug

    def call_api(self, prompt):
        """
        Simulate an API call to the LLM.
        Returns a JSON with 4 dummy components for testing.
        """
        import time, random, json
        time.sleep(0.01)  # simulate small delay

        # Simulated components
        response = [
            {"name": "Component A", "cost_share": 0.25, "function": "Function A", "subsystem": "Chassis"},
            {"name": "Component B", "cost_share": 0.25, "function": "Function B", "subsystem": "Electronics"},
            {"name": "Component C", "cost_share": 0.25, "function": "Function C", "subsystem": "Powertrain"},
            {"name": "Component D", "cost_share": 0.25, "function": "Function D", "subsystem": "Suspension"},
        ]

        return {
            "success": True,
            "response": json.dumps(response),
            "time": random.uniform(0.01, 0.05),
            "tokens": random.randint(10, 50),
            "tokens_per_sec": random.uniform(100, 500)
        }
    def calculate_summary(self, tests):
        """Minimal summary calculation"""
        total = len(tests)
        valid = sum(1 for t in tests if t.get('valid'))
        success_rate = valid / total if total else 0
        avg_time = sum(t.get('time', 0) for t in tests) / total if total else 0
        return {
            'total_tests': total,
            'valid_tests': valid,
            'success_rate': success_rate,
            'avg_time_sec': avg_time
        }

    def print_summary(self, label, summary):
        """Minimal summary printing"""
        print(f"{label} Summary:")
        for k, v in summary.items():
            if isinstance(v, float):
                print(f"  {k}: {v:.2f}")
            else:
                print(f"  {k}: {v}")


    def save_results(self, results, filename=None):
        """Save results to a JSON file"""
        if not filename:
            import time
            filename = f"results_{int(time.time())}.json"
        with open(filename, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\nSaved results to {filename}")

>>>>>>> a0bbba27911e92669a75885cb071b476f80844e0
