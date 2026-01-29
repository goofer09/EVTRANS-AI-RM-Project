"""
OVERALL PROMPT ENGINEERING TEST
Runs all three testers (enricher, classifier, scorer) end-to-end
Tests overall performance and integration
"""

import json
from datetime import datetime
from typing import Dict, List

from prompt_enricher_tester import EnricherPromptTester
from prompt_classifier_tester import ClassifierPromptTester
from prompt_scorer_tester import ScorerPromptTester


class OverallPromptTest:
    """
    Run all three prompt testers in sequence
    Measures overall performance and integration
    """
    
    def __init__(self, model="mistral:7b-q4_k_m", debug=True):
        self.model = model
        self.debug = debug
        
        self.enricher_tester = EnricherPromptTester(model=model, debug=debug)
        self.classifier_tester = ClassifierPromptTester(model=model, debug=debug)
        self.scorer_tester = ScorerPromptTester(model=model, debug=debug)
        
        self.overall_results = {
            'timestamp': datetime.now().isoformat(),
            'type': 'overall_prompt_test',
            'model': model,
            'stages': {}
        }
    
    def run_complete_test(self, test_cases: List[Dict]) -> Dict:
        """
        Run complete end-to-end test through all three stages
        
        Args:
            test_cases: List of {'hs_code': ..., 'description': ...}
        
        Returns:
            Complete test results for all stages
        """
        
        print("\n" + "="*70)
        print("OVERALL PROMPT ENGINEERING TEST")
        print("="*70)
        
        # STAGE 1: ENRICHER
        print("\n" + "-"*70)
        print("STAGE 1: ENRICHER")
        print("-"*70)
        
        enricher_results = self.enricher_tester.test_multiple(test_cases)
        self.overall_results['stages']['enricher'] = enricher_results
        self.enricher_tester.print_results(enricher_results)
        
        # Extract components from enricher output for next stage
        enricher_components_per_code = {}
        for test in enricher_results['tests']:
            if test.get('components'):
                hs_code = test['hs_code']
                enricher_components_per_code[hs_code] = test['components']
        
        # STAGE 2: CLASSIFIER
        print("\n" + "-"*70)
        print("STAGE 2: CLASSIFIER")
        print("-"*70)
        
        classifier_batch_data = []
        for hs_code, components in enricher_components_per_code.items():
            classifier_batch_data.append({
                'hs_code': hs_code,
                'components': components
            })
        
        if classifier_batch_data:
            classifier_results = self.classifier_tester.test_batch(classifier_batch_data)
            self.overall_results['stages']['classifier'] = classifier_results
            self.classifier_tester.print_results(classifier_results)
        else:
            print("[CLASSIFIER] No components to classify (enricher failed)")
            classifier_results = None
            self.overall_results['stages']['classifier'] = {'error': 'No enricher output'}
        
        # STAGE 3: SCORER
        print("\n" + "-"*70)
        print("STAGE 3: SCORER")
        print("-"*70)
        
        if classifier_batch_data:
            scorer_results = self.scorer_tester.test_batch(classifier_batch_data)
            self.overall_results['stages']['scorer'] = scorer_results
            self.scorer_tester.print_results(scorer_results)
        else:
            print("[SCORER] No components to score (enricher failed)")
            scorer_results = None
            self.overall_results['stages']['scorer'] = {'error': 'No enricher output'}
        
        # SUMMARY
        print("\n" + "="*70)
        print("OVERALL TEST SUMMARY")
        print("="*70)
        
        self._print_overall_summary(enricher_results, classifier_results, scorer_results)
        
        return self.overall_results
    
    def _print_overall_summary(self, enricher_results: Dict, 
                              classifier_results: Dict, 
                              scorer_results: Dict):
        """Print overall summary across all stages"""
        
        print("\nSTAGE RESULTS:")
        
        # Enricher summary
        if enricher_results and 'summary' in enricher_results:
            summary = enricher_results['summary']
            print(f"\n✅ ENRICHER")
            print(f"   Success: {summary.get('successful', 0)}/{summary.get('total_tests', 0)}")
            print(f"   Quality: {summary.get('quality', '0%')}")
            print(f"   Avg Time: {summary.get('avg_time', 0):.2f}s")
        
        # Classifier summary
        if classifier_results and 'overall_summary' in classifier_results:
            summary = classifier_results['overall_summary']
            print(f"\n✅ CLASSIFIER")
            print(f"   Success: {summary.get('successful', 0)}/{summary.get('total_tests', 0)}")
            print(f"   Quality: {summary.get('quality', '0%')}")
            print(f"   Avg Time: {summary.get('avg_time', 0):.2f}s")
        elif classifier_results is None:
            print(f"\n❌ CLASSIFIER")
            print(f"   Skipped (no enricher output)")
        
        # Scorer summary
        if scorer_results and 'overall_summary' in scorer_results:
            summary = scorer_results['overall_summary']
            print(f"\n✅ SCORER")
            print(f"   Success: {summary.get('successful', 0)}/{summary.get('total_tests', 0)}")
            print(f"   Quality: {summary.get('quality', '0%')}")
            print(f"   Avg Time: {summary.get('avg_time', 0):.2f}s")
        elif scorer_results is None:
            print(f"\n❌ SCORER")
            print(f"   Skipped (no enricher output)")
        
        # Overall metrics
        print("\nOVERALL METRICS:")
        
        if enricher_results and 'summary' in enricher_results:
            total_time = enricher_results['summary'].get('total_time', 0)
            if classifier_results and 'overall_summary' in classifier_results:
                total_time += classifier_results['overall_summary'].get('total_time', 0)
            if scorer_results and 'overall_summary' in scorer_results:
                total_time += scorer_results['overall_summary'].get('total_time', 0)
            
            print(f"   Total Time: {total_time:.1f}s")
            print(f"   Avg per HS Code: {total_time / max(1, len(enricher_results['tests'])):.1f}s")
        
        print("\n" + "="*70)
    
    def save_results(self, filename: str = None) -> str:
        """
        Save complete test results
        
        Args:
            filename: Output filename (auto-generated if None)
        
        Returns:
            Path to saved file
        """
        
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"prompt_test_overall_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.overall_results, f, indent=2, default=str)
        
        print(f"\nOverall results saved to: {filename}")
        return filename


# ====================================
# USAGE EXAMPLE
# ====================================

if __name__ == "__main__":
    tester = OverallPromptTest(debug=True)
    
    # Define test cases
    test_cases = [
        {'hs_code': '8708.30', 'description': 'Brake systems'},
        {'hs_code': '8708.40', 'description': 'Steering systems'},
        {'hs_code': '8708.50', 'description': 'Suspension systems'},
    ]
    
    # Run complete test
    results = tester.run_complete_test(test_cases)
    
    # Save results
    tester.save_results()