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