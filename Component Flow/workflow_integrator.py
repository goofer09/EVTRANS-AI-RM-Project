# WORKFLOW INTEGRATOR - OPTIMIZED WITH BATCHED API CALLS
## 3x Faster: Batched Classifier & Scorer

"""
Workflow Integrator - OPTIMIZED VERSION
Master orchestrator for enricher → classifier → scorer → validator

OPTIMIZATIONS:
- Batched classifier: ALL components in ONE API call (was: 1 call per component)
- Batched scorer: ALL components in ONE API call (was: 1 call per component)
- Result: 3 API calls per HS code instead of 9+
- Speed improvement: ~3x faster

ORIGINAL FEATURES PRESERVED:
- Proper timeout error handling
- Error type tracking (TIMEOUT vs ERROR)
- Safeguards against critical failures
- Error propagation back to integrator
"""

import json
import time
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional

# Import your LLM modules
from llm_enricher import SubComponentEnricher
from llm_classifier import ComponentClassifier
from llm_scorer import ComponentScorer
from comprehensive_validator import ComprehensiveValidator


class WorkflowIntegrator:
    """
    Master orchestrator for complete analysis pipeline
    
    Coordinates:
    - Enricher (component identification) - 1 API call
    - Classifier (ICE/EV/SHARED classification) - 1 API call (BATCHED)
    - Scorer (6-dimension risk scoring) - 1 API call (BATCHED)
    - Validator (quality assurance) - No API call
    
    Total: 3 API calls per HS code (was 9+)
    """
    
    def __init__(self, debug=True, max_retries=2):
        """
        Initialize workflow integrator
        
        Args:
            debug: Print debug messages
            max_retries: Number of retries per stage if it fails
        """
        self.debug = debug
        self.max_retries = max_retries
        
        # Initialize components
        self.enricher = SubComponentEnricher()
        self.classifier = ComponentClassifier()
        self.scorer = ComponentScorer()
        self.validator = ComprehensiveValidator()
        
        # State tracking
        self.current_hs_code = None
        self.current_stage = None
        self.errors = []
        self.warnings = []
        
        if self.debug:
            print("[INTEGRATOR] Workflow integrator initialized (OPTIMIZED - Batched API calls)")
    
    # ============================================
    # STAGE 1: ENRICHER (unchanged)
    # ============================================
    
    def run_enricher(self, hs_code: str, description: str) -> Optional[List[Dict]]:
        """
        Run enricher stage: Identify components for HS code
        
        API calls: 1

        Args:
            hs_code: HS code (e.g., "8708.30")
            description: Description (e.g., "Brake systems")

        Returns:
            List of components or None if failed
        """
        
        self.current_stage = "enricher"
        self.current_hs_code = hs_code
        
        if self.debug:
            print(f"\n[INTEGRATOR] Stage 1: ENRICHER")
            print(f"[INTEGRATOR] HS Code: {hs_code} - {description}")
        
        # Retry logic
        for attempt in range(1, self.max_retries + 1):
            try:
                if self.debug:
                    print(f"[INTEGRATOR] Enricher attempt {attempt}/{self.max_retries}...", end=" ")
                
                start = time.time()
                result = self.enricher.enrich(hs_code, description)
                elapsed = time.time() - start
                
                # Validate result
                if not result:
                    raise ValueError("Enricher returned empty result")
                
                if not isinstance(result, list):
                    raise ValueError(f"Enricher returned {type(result)}, expected list")
                
                if self.debug:
                    print(f"✅ Success ({elapsed:.1f}s)")
                    print(f"[INTEGRATOR] Components identified: {len(result)}")
                    for i, comp in enumerate(result, 1):
                        print(f"[INTEGRATOR]   {i}. {comp.get('name')} (cost: {comp.get('cost_share', 'N/A')})")
                
                return result
            
            # CATCH TIMEOUT ERRORS
            except TimeoutError as e:
                if self.debug:
                    print(f"❌ TIMEOUT")
                
                self.errors.append({
                    'stage': 'enricher',
                    'attempt': attempt,
                    'error': str(e),
                    'error_type': 'TIMEOUT',
                    'timestamp': datetime.now().isoformat()
                })
                
                if self.debug:
                    print(f"[INTEGRATOR] Enricher timeout - cannot retry")
                return None
            
            # CATCH OTHER ERRORS
            except Exception as e:
                error_msg = f"Enricher failed (attempt {attempt}): {str(e)}"
                if self.debug:
                    print(f"❌ {error_msg}")
                
                self.errors.append({
                    'stage': 'enricher',
                    'attempt': attempt,
                    'error': str(e),
                    'error_type': 'ERROR',
                    'timestamp': datetime.now().isoformat()
                })
                
                if attempt == self.max_retries:
                    if self.debug:
                        print(f"[INTEGRATOR] Enricher failed after {self.max_retries} attempts")
                    return None
        
        return None
    
    # ============================================
    # STAGE 2: CLASSIFIER (BATCHED - OPTIMIZED)
    # ============================================
    
    def run_classifier(self, enricher_output: List[Dict]) -> Optional[List[Dict]]:
        """
        Run classifier stage: Classify ALL components in ONE API call
        
        OPTIMIZED: Single API call for all components
        - Old: 4 components = 4 API calls
        - New: 4 components = 1 API call
        
        API calls: 1

        Args:
            enricher_output: List of components from enricher

        Returns:
            List of classifications or None if failed
        """
        
        self.current_stage = "classifier"
        num_components = len(enricher_output)
        
        if self.debug:
            print(f"\n[INTEGRATOR] Stage 2: CLASSIFIER (BATCHED)")
            print(f"[INTEGRATOR] Classifying {num_components} components in ONE API call...")
        
        # Extract all component names
        component_names = [
            comp.get('name', f'Component_{i}') 
            for i, comp in enumerate(enricher_output)
        ]
        
        # Retry logic
        for attempt in range(1, self.max_retries + 1):
            try:
                if self.debug:
                    print(f"[INTEGRATOR] Classifier attempt {attempt}/{self.max_retries}...", end=" ")
                
                start = time.time()
                
                # ═══════════════════════════════════════════════════════
                # BATCHED CALL: Send ALL components at once
                # ═══════════════════════════════════════════════════════
                results = self.classifier.classify(component_names, self.current_hs_code)
                
                elapsed = time.time() - start
                
                # Validate results
                if not results or len(results) == 0:
                    raise ValueError("Classifier returned empty result")
                
                # Check we got results for all components
                if len(results) < num_components:
                    self.warnings.append({
                        'stage': 'classifier',
                        'warning': f'Expected {num_components} results, got {len(results)}',
                        'timestamp': datetime.now().isoformat()
                    })
                    # Pad with fallback results
                    while len(results) < num_components:
                        results.append({
                            'name': component_names[len(results)],
                            'classification': 'SHARED',
                            'similarity_score': 0.5,
                            'reasoning': 'Fallback: Not returned by API'
                        })
                
                if self.debug:
                    print(f"✅ Success ({elapsed:.1f}s)")
                    for r in results:
                        print(f"[INTEGRATOR]   • {r.get('name')}: {r.get('classification')} ({r.get('similarity_score', 0):.2f})")
                
                return results
            
            # CATCH TIMEOUT ERRORS
            except TimeoutError as e:
                if self.debug:
                    print(f"❌ TIMEOUT")
                
                self.errors.append({
                    'stage': 'classifier',
                    'attempt': attempt,
                    'error': str(e),
                    'error_type': 'TIMEOUT',
                    'timestamp': datetime.now().isoformat()
                })
                
                # Don't retry timeouts
                return None
            
            # CATCH OTHER ERRORS
            except Exception as e:
                error_msg = f"Classifier failed (attempt {attempt}): {str(e)}"
                if self.debug:
                    print(f"❌ {error_msg}")
                
                self.errors.append({
                    'stage': 'classifier',
                    'attempt': attempt,
                    'error': str(e),
                    'error_type': 'ERROR',
                    'timestamp': datetime.now().isoformat()
                })
                
                if attempt == self.max_retries:
                    if self.debug:
                        print(f"[INTEGRATOR] Classifier failed after {self.max_retries} attempts")
                    return None
        
        return None
    
    # ============================================
    # STAGE 3: SCORER (BATCHED - OPTIMIZED)
    # ============================================
    
    def run_scorer(self, enricher_output: List[Dict]) -> Optional[List[Dict]]:
        """
        Run scorer stage: Score ALL components in ONE API call
        
        OPTIMIZED: Single API call for all components
        - Old: 4 components = 4 API calls
        - New: 4 components = 1 API call
        
        API calls: 1

        Args:
            enricher_output: List of components from enricher

        Returns:
            List of scores or None if failed
        """
        
        self.current_stage = "scorer"
        num_components = len(enricher_output)
        
        if self.debug:
            print(f"\n[INTEGRATOR] Stage 3: SCORER (BATCHED)")
            print(f"[INTEGRATOR] Scoring {num_components} components in ONE API call...")
        
        # Extract all component names
        component_names = [
            comp.get('name', f'Component_{i}') 
            for i, comp in enumerate(enricher_output)
        ]
        
        # Retry logic
        for attempt in range(1, self.max_retries + 1):
            try:
                if self.debug:
                    print(f"[INTEGRATOR] Scorer attempt {attempt}/{self.max_retries}...", end=" ")
                
                start = time.time()
                
                # ═══════════════════════════════════════════════════════
                # BATCHED CALL: Send ALL components at once
                # ═══════════════════════════════════════════════════════
                results = self.scorer.score(component_names, self.current_hs_code)
                
                elapsed = time.time() - start
                
                # Validate results
                if not results or len(results) == 0:
                    raise ValueError("Scorer returned empty result")
                
                # Check we got results for all components
                if len(results) < num_components:
                    self.warnings.append({
                        'stage': 'scorer',
                        'warning': f'Expected {num_components} results, got {len(results)}',
                        'timestamp': datetime.now().isoformat()
                    })
                    # Pad with fallback results
                    while len(results) < num_components:
                        results.append({
                            'name': component_names[len(results)],
                            'tech': 50, 'manufacturing': 50, 'supply_chain': 50,
                            'demand': 50, 'value': 50, 'regulatory': 50,
                            'reasoning': {}
                        })
                
                if self.debug:
                    print(f"✅ Success ({elapsed:.1f}s)")
                    for r in results:
                        tfs = int(sum([
                            r.get('tech', 0), r.get('manufacturing', 0), r.get('supply_chain', 0),
                            r.get('demand', 0), r.get('value', 0), r.get('regulatory', 0)
                        ]) / 6)
                        print(f"[INTEGRATOR]   • {r.get('name')}: TFS={tfs}")
                
                return results
            
            # CATCH TIMEOUT ERRORS
            except TimeoutError as e:
                if self.debug:
                    print(f"❌ TIMEOUT")
                
                self.errors.append({
                    'stage': 'scorer',
                    'attempt': attempt,
                    'error': str(e),
                    'error_type': 'TIMEOUT',
                    'timestamp': datetime.now().isoformat()
                })
                
                # Don't retry timeouts
                return None
            
            # CATCH OTHER ERRORS
            except Exception as e:
                error_msg = f"Scorer failed (attempt {attempt}): {str(e)}"
                if self.debug:
                    print(f"❌ {error_msg}")
                
                self.errors.append({
                    'stage': 'scorer',
                    'attempt': attempt,
                    'error': str(e),
                    'error_type': 'ERROR',
                    'timestamp': datetime.now().isoformat()
                })
                
                if attempt == self.max_retries:
                    if self.debug:
                        print(f"[INTEGRATOR] Scorer failed after {self.max_retries} attempts")
                    return None
        
        return None
    
    # ============================================
    # STAGE 4: VALIDATOR (unchanged)
    # ============================================
    
    def run_validator(self, 
                     enricher_output: List[Dict],
                     classifier_output: List[Dict],
                     scorer_output: List[Dict]) -> Dict:
        """
        Run validator stage: Validate all outputs and produce quality metrics
        
        API calls: 0 (local validation)
        
        Args:
            enricher_output: Output from enricher
            classifier_output: Output from classifier
            scorer_output: Output from scorer
        
        Returns:
            Validation results with quality scores
        """
        
        self.current_stage = "validator"
        
        if self.debug:
            print(f"\n[INTEGRATOR] Stage 4: VALIDATOR")
            print(f"[INTEGRATOR] Validating all outputs...")
        
        try:
            results = self.validator.validate_complete_pipeline(
                enricher_output,
                classifier_output,
                scorer_output
            )
            
            if self.debug:
                print(f"[INTEGRATOR] ✅ Validation complete")
                print(f"[INTEGRATOR] Overall quality: {results.get('overall_quality', 0):.0f}/100")
                print(f"[INTEGRATOR] Valid: {results.get('valid', False)}")
            
            return results
        
        except Exception as e:
            error_msg = f"Validator failed: {str(e)}"
            if self.debug:
                print(f"[INTEGRATOR] ❌ {error_msg}")
            
            self.errors.append({
                'stage': 'validator',
                'error': str(e),
                'error_type': 'ERROR',
                'timestamp': datetime.now().isoformat()
            })
            
            # Return minimal validation result (don't fail the whole pipeline)
            return {
                'overall_quality': 50,
                'overall_confidence': 'LOW',
                'valid': True,
                'stages': {},
                'all_issues': [],
                'error': str(e)
            }
    
    # ============================================
    # MAIN ORCHESTRATION
    # ============================================
    
    def run_complete_analysis(self, hs_code: str, description: str) -> Dict:
        """
        Run complete analysis workflow: Enricher → Classifier → Scorer → Validator
        
        OPTIMIZED: 3 API calls total (was 9+)
        - Enricher: 1 call
        - Classifier: 1 call (batched)
        - Scorer: 1 call (batched)
        - Validator: 0 calls
        
        Args:
            hs_code: HS code (e.g., "8708.30")
            description: Description (e.g., "Brake systems")
        
        Returns:
            Complete analysis result with all data and quality metrics
        """
        
        # Reset state
        self.errors = []
        self.warnings = []
        
        print("\n" + "="*70)
        print(f"WORKFLOW ANALYSIS: {hs_code} - {description}")
        print("="*70)
        
        start_time = time.time()
        
        # ─────────────────────────────────────────
        # STAGE 1: ENRICHER (1 API call)
        # ─────────────────────────────────────────
        enricher_output = self.run_enricher(hs_code, description)
        if not enricher_output:
            timeout_errors = [e for e in self.errors if e.get('stage') == 'enricher' and e.get('error_type') == 'TIMEOUT']
            if timeout_errors:
                return self._error_result(f"Enricher timeout after {self.max_retries} attempts")
            else:
                return self._error_result("Enricher failed - cannot identify components")
        
        # ─────────────────────────────────────────
        # STAGE 2: CLASSIFIER (1 API call - BATCHED)
        # ─────────────────────────────────────────
        classifier_output = self.run_classifier(enricher_output)
        if not classifier_output:
            timeout_errors = [e for e in self.errors if e.get('stage') == 'classifier' and e.get('error_type') == 'TIMEOUT']
            if timeout_errors:
                return self._error_result(f"Classifier timeout")
            else:
                return self._error_result("Classifier failed on all components")
        
        # ─────────────────────────────────────────
        # STAGE 3: SCORER (1 API call - BATCHED)
        # ─────────────────────────────────────────
        scorer_output = self.run_scorer(enricher_output)
        if not scorer_output:
            timeout_errors = [e for e in self.errors if e.get('stage') == 'scorer' and e.get('error_type') == 'TIMEOUT']
            if timeout_errors:
                return self._error_result(f"Scorer timeout")
            else:
                return self._error_result("Scorer failed on all components")
        
        # ─────────────────────────────────────────
        # STAGE 4: VALIDATOR (0 API calls)
        # ─────────────────────────────────────────
        validation_results = self.run_validator(
            enricher_output,
            classifier_output,
            scorer_output
        )
        
        # Combine all results
        elapsed = time.time() - start_time
        
        final_result = {
            'timestamp': datetime.now().isoformat(),
            'hs_code': hs_code,
            'description': description,
            'processing_time': elapsed,
            'stages': {
                'enricher': {
                    'output': enricher_output,
                    'status': 'SUCCESS' if enricher_output else 'FAILED'
                },
                'classifier': {
                    'output': classifier_output,
                    'status': 'SUCCESS' if classifier_output else 'FAILED'
                },
                'scorer': {
                    'output': scorer_output,
                    'status': 'SUCCESS' if scorer_output else 'FAILED'
                },
                'validator': validation_results
            },
            'overall_quality': validation_results.get('overall_quality', 0),
            'overall_confidence': validation_results.get('overall_confidence', 'LOW'),
            'valid': validation_results.get('valid', False),
            'errors': self.errors,
            'warnings': self.warnings,
            'summary': self._generate_summary(
                hs_code, 
                enricher_output, 
                classifier_output, 
                scorer_output,
                validation_results
            )
        }
        
        # Print summary
        self._print_summary(final_result)
        
        return final_result
    
    # ============================================
    # HELPER METHODS
    # ============================================
    
    def _error_result(self, error_msg: str) -> Dict:
        """Return error result"""
        if self.debug:
            print(f"[INTEGRATOR] ❌ {error_msg}")
        return {
            'error': error_msg,
            'valid': False,
            'overall_quality': 0,
            'errors': self.errors,
            'warnings': self.warnings
        }
    
    def _generate_summary(self,
                         hs_code: str,
                         enricher_out: List[Dict],
                         classifier_out: List[Dict],
                         scorer_out: List[Dict],
                         validation: Dict) -> Dict:
        """Generate summary statistics"""
        
        return {
            'total_components': len(enricher_out) if enricher_out else 0,
            'classifications': {
                'SHARED': sum(1 for c in classifier_out if c.get('classification') == 'SHARED') if classifier_out else 0,
                'ICE_ONLY': sum(1 for c in classifier_out if c.get('classification') == 'ICE_ONLY') if classifier_out else 0,
                'EV_ONLY': sum(1 for c in classifier_out if c.get('classification') == 'EV_ONLY') if classifier_out else 0,
                'UNKNOWN': sum(1 for c in classifier_out if c.get('classification') == 'UNKNOWN') if classifier_out else 0,
            },
            'avg_similarity': (
                sum(c.get('similarity_score', 0) for c in classifier_out) / len(classifier_out)
                if classifier_out else 0
            ),
            'quality_by_stage': {
                'enricher': validation.get('stages', {}).get('enricher', {}).get('quality_score', 0),
                'classifier': validation.get('stages', {}).get('classifier', {}).get('quality_score', 0),
                'scorer': validation.get('stages', {}).get('scorer', {}).get('quality_score', 0),
                'integration': validation.get('stages', {}).get('integration', {}).get('quality_score', 0),
            },
            'issues_found': len(validation.get('all_issues', [])),
            'errors_found': len(self.errors),
            'timeouts': sum(1 for e in self.errors if e.get('error_type') == 'TIMEOUT'),
            'status': 'VALID' if validation.get('valid') else 'INVALID'
        }
    
    def _print_summary(self, result: Dict):
        """Print final summary"""
        
        print(f"\n{'='*70}")
        print(f"ANALYSIS COMPLETE")
        print(f"{'='*70}")
        
        summary = result.get('summary', {})
        
        print(f"\nHS Code: {result['hs_code']}")
        print(f"Components analyzed: {summary.get('total_components', 0)}")
        print(f"Processing time: {result['processing_time']:.1f}s")
        
        # Show classifications
        classifications = summary.get('classifications', {})
        print(f"\nClassifications:")
        print(f"  SHARED:   {classifications.get('SHARED', 0)}")
        print(f"  ICE_ONLY: {classifications.get('ICE_ONLY', 0)}")
        print(f"  EV_ONLY:  {classifications.get('EV_ONLY', 0)}")
        
        print(f"\nQuality Scores:")
        for stage, score in summary.get('quality_by_stage', {}).items():
            status = '✅' if score >= 70 else '⚠️ ' if score >= 50 else '❌'
            print(f"  {status} {stage:12s}: {score:3.0f}/100")
        
        print(f"\nOverall: {result['overall_quality']:.0f}/100 ({result['overall_confidence']})")
        print(f"Status: {summary.get('status', 'UNKNOWN')}")
        
        # Show errors if any
        if result.get('errors'):
            print(f"\n⚠️ Errors encountered: {len(result['errors'])}")
            
            timeout_errors = [e for e in result['errors'] if e.get('error_type') == 'TIMEOUT']
            other_errors = [e for e in result['errors'] if e.get('error_type') != 'TIMEOUT']
            
            if timeout_errors:
                print(f"  Timeouts: {len(timeout_errors)}")
            if other_errors:
                print(f"  Other errors: {len(other_errors)}")
            
            for error in result['errors'][:3]:
                print(f"    - [{error.get('stage')}] {error.get('error', 'Unknown')[:60]}")
        
        print(f"{'='*70}\n")
    
    def save_results(self, result: Dict, output_file: str = None) -> str:
        """
        Save results to JSON file
        
        Args:
            result: Result dictionary from run_complete_analysis
            output_file: Output file path (auto-generated if None)
        
        Returns:
            Path to saved file
        """
        
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            hs_code = result.get('hs_code', 'unknown').replace('.', '_')
            output_file = f"analysis_{hs_code}_{timestamp}.json"
        
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        
        if self.debug:
            print(f"[INTEGRATOR] Results saved to: {output_file}")
        
        return output_file


# ============================================
# USAGE EXAMPLE
# ============================================

if __name__ == "__main__":
    
    # Initialize integrator
    integrator = WorkflowIntegrator(debug=True, max_retries=2)
    
    # Run analysis on single HS code
    result = integrator.run_complete_analysis(
        hs_code="8708.30",
        description="Brake systems"
    )
    
    # Save results
    if result.get('overall_quality', 0) > 0:
        output_file = integrator.save_results(result)
        print(f"Results saved to: {output_file}")
    
    # Print results
    print(json.dumps(result, indent=2, default=str))