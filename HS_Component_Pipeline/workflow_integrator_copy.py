"""
Workflow Integrator
Master orchestrator for enricher → classifier → scorer → validator

Flow:
1. Enricher:   HS Code → Components (4 items)
2. Classifier: Components → Classifications (4 items)
3. Scorer:     Components → Scores (4 items)
4. Validator:  All 3 → Quality validation
5. Output:     Complete analysis with quality metrics
"""

import json
import time
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional

# Assuming you have these files
from llm_enricher import SubComponentEnricher
from llm_classifier import ComponentClassifier
from llm_scorer import ComponentScorer
from comprehensive_validator import ComprehensiveValidator


class WorkflowIntegrator:
    """
    Master orchestrator for complete analysis pipeline
    
    Coordinates:
    - Enricher (component identification)
    - Classifier (ICE/EV/SHARED classification)
    - Scorer (6-dimension risk scoring)
    - Validator (quality assurance)
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
        # TODO: Add debug support to each class separately
        self.enricher = SubComponentEnricher()  # debug=debug
        self.classifier = ComponentClassifier()  # debug=debug
        self.scorer = ComponentScorer()  # debug=debug
        self.validator = ComprehensiveValidator()  # debug=debug
        
        # State tracking
        self.current_hs_code = None
        self.current_stage = None
        self.errors = []
        self.warnings = []
        
        if self.debug:
            print("[INTEGRATOR] Workflow integrator initialized")
    
    # ============================================
    # STAGE 1: ENRICHER
    # ============================================
    
    def run_enricher(self, hs_code: str, description: str) -> Optional[List[Dict]]:
        """
        Run enricher stage: Identify 4 components
        
        Args:
            hs_code: HS code (e.g., "8708.30")
            description: Description (e.g., "Brake systems")
        
        Returns:
            List of 4 components or None if failed
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
                
                if len(result) != 4:
                    raise ValueError(f"Enricher returned {len(result)} components, expected 4")
                
                if self.debug:
                    print(f"✅ Success ({elapsed:.1f}s)")
                    print(f"[INTEGRATOR] Components identified: {len(result)}")
                    for i, comp in enumerate(result, 1):
                        print(f"[INTEGRATOR]   {i}. {comp.get('name')} (cost: {comp.get('cost_share')})")
                
                return result
            
            except Exception as e:
                error_msg = f"Enricher failed (attempt {attempt}): {str(e)}"
                if self.debug:
                    print(f"❌ {error_msg}")
                
                self.errors.append({
                    'stage': 'enricher',
                    'attempt': attempt,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
                
                if attempt == self.max_retries:
                    if self.debug:
                        print(f"[INTEGRATOR] Enricher failed after {self.max_retries} attempts")
                    return None
        
        return None
    
    # ============================================
    # STAGE 2: CLASSIFIER
    # ============================================
    
    def run_classifier(self, enricher_output: List[Dict]) -> Optional[List[Dict]]:
        """
        Run classifier stage: Classify each component (ICE/EV/SHARED)
        
        Args:
            enricher_output: List of 4 components from enricher
        
        Returns:
            List of 4 classifications or None if failed
        """
        
        self.current_stage = "classifier"
        
        if self.debug:
            print(f"\n[INTEGRATOR] Stage 2: CLASSIFIER")
            print(f"[INTEGRATOR] Classifying {len(enricher_output)} components...")
        
        classifications = []
        
        # Classify each component
        for i, component in enumerate(enricher_output, 1):
            comp_name = component.get('name', f'Component {i}')
            
            for attempt in range(1, self.max_retries + 1):
                try:
                    if self.debug:
                        print(f"[INTEGRATOR] Classifying {i}/4: {comp_name} (attempt {attempt})...", end=" ")
                    
                    start = time.time()
                    result = self.classifier.classify(
                        comp_name,
                        self.current_hs_code
                    )
                    elapsed = time.time() - start
                    
                    if not result:
                        raise ValueError("Classifier returned empty result")
                    
                    if 'classification' not in result:
                        raise ValueError("Classifier missing 'classification' field")
                    
                    if 'similarity_score' not in result:
                        raise ValueError("Classifier missing 'similarity_score' field")
                    
                    classifications.append(result)
                    
                    if self.debug:
                        print(f"✅ {result['classification']} (similarity: {result['similarity_score']:.2f})")
                    
                    break
                
                except Exception as e:
                    error_msg = f"Classifier failed for {comp_name} (attempt {attempt}): {str(e)}"
                    if self.debug:
                        print(f"❌ {error_msg}")
                    
                    self.errors.append({
                        'stage': 'classifier',
                        'component': comp_name,
                        'attempt': attempt,
                        'error': str(e),
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    if attempt == self.max_retries:
                        if self.debug:
                            print(f"[INTEGRATOR] Classifier failed for {comp_name} after {self.max_retries} attempts")
                        # Don't return None - allow partial results
                        classifications.append({
                            'classification': 'UNKNOWN',
                            'similarity_score': 0.0,
                            'error': str(e)
                        })
                        break
        
        if len(classifications) != len(enricher_output):
            if self.debug:
                print(f"[INTEGRATOR] ⚠️ Warning: Got {len(classifications)} classifications for {len(enricher_output)} components")
            self.warnings.append(f"Classifier returned {len(classifications)} results, expected {len(enricher_output)}")
        
        return classifications if classifications else None
    
    # ============================================
    # STAGE 3: SCORER
    # ============================================
    
    def run_scorer(self, enricher_output: List[Dict]) -> Optional[List[Dict]]:
        """
        Run scorer stage: Score each component on 6 dimensions
        
        Args:
            enricher_output: List of 4 components from enricher
        
        Returns:
            List of 4 score sets or None if failed
        """
        
        self.current_stage = "scorer"
        
        if self.debug:
            print(f"\n[INTEGRATOR] Stage 3: SCORER")
            print(f"[INTEGRATOR] Scoring {len(enricher_output)} components...")
        
        scores = []
        
        # Score each component
        for i, component in enumerate(enricher_output, 1):
            comp_name = component.get('name', f'Component {i}')
            
            for attempt in range(1, self.max_retries + 1):
                try:
                    if self.debug:
                        print(f"[INTEGRATOR] Scoring {i}/4: {comp_name} (attempt {attempt})...", end=" ")
                    
                    start = time.time()
                    result = self.scorer.score(
                        comp_name,
                        self.current_hs_code
                    )
                    elapsed = time.time() - start
                    
                    if not result:
                        raise ValueError("Scorer returned empty result")
                    
                    required_dims = ['tech', 'manufacturing', 'supply_chain', 'demand', 'value', 'regulatory']
                    for dim in required_dims:
                        if dim not in result:
                            raise ValueError(f"Scorer missing '{dim}' field")
                    
                    scores.append(result)
                    
                    if self.debug:
                        print(f"✅ Scores assigned ({elapsed:.1f}s)")
                    
                    break
                
                except Exception as e:
                    error_msg = f"Scorer failed for {comp_name} (attempt {attempt}): {str(e)}"
                    if self.debug:
                        print(f"❌ {error_msg}")
                    
                    self.errors.append({
                        'stage': 'scorer',
                        'component': comp_name,
                        'attempt': attempt,
                        'error': str(e),
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    if attempt == self.max_retries:
                        if self.debug:
                            print(f"[INTEGRATOR] Scorer failed for {comp_name} after {self.max_retries} attempts")
                        # Return default scores
                        scores.append({
                            'tech': 50, 'manufacturing': 50, 'supply_chain': 50,
                            'demand': 50, 'value': 50, 'regulatory': 50,
                            'error': str(e)
                        })
                        break
        
        if len(scores) != len(enricher_output):
            if self.debug:
                print(f"[INTEGRATOR] ⚠️ Warning: Got {len(scores)} score sets for {len(enricher_output)} components")
            self.warnings.append(f"Scorer returned {len(scores)} results, expected {len(enricher_output)}")
        
        return scores if scores else None
    
    # ============================================
    # STAGE 4: VALIDATOR
    # ============================================
    
    def run_validator(self, 
                     enricher_output: List[Dict],
                     classifier_output: List[Dict],
                     scorer_output: List[Dict]) -> Dict:
        """
        Run validator stage: Validate all outputs and produce quality metrics
        
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
                print(f"[INTEGRATOR] Overall quality: {results['overall_quality']:.0f}/100")
                print(f"[INTEGRATOR] Valid: {results['valid']}")
            
            return results
        
        except Exception as e:
            error_msg = f"Validator failed: {str(e)}"
            if self.debug:
                print(f"[INTEGRATOR] ❌ {error_msg}")
            
            self.errors.append({
                'stage': 'validator',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
            
            # Return minimal validation result
            return {
                'overall_quality': 0,
                'overall_confidence': 'LOW',
                'valid': False,
                'error': str(e)
            }
    
    # ============================================
    # MAIN ORCHESTRATION
    # ============================================
    
    def run_complete_analysis(self, hs_code: str, description: str) -> Dict:
        """
        Run complete analysis workflow: Enricher → Classifier → Scorer → Validator
        
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
        
        # STAGE 1: ENRICHER
        enricher_output = self.run_enricher(hs_code, description)
        if not enricher_output:
            return self._error_result("Enricher failed, cannot continue")
        
        # STAGE 2: CLASSIFIER
        classifier_output = self.run_classifier(enricher_output)
        if not classifier_output:
            return self._error_result("Classifier failed, cannot continue")
        
        # STAGE 3: SCORER
        scorer_output = self.run_scorer(enricher_output)
        if not scorer_output:
            return self._error_result("Scorer failed, cannot continue")
        
        # STAGE 4: VALIDATOR
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
            'overall_quality': 0
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
        
        print(f"\nQuality Scores:")
        for stage, score in summary.get('quality_by_stage', {}).items():
            status = '✅' if score >= 70 else '⚠️ ' if score >= 50 else '❌'
            print(f"  {status} {stage:12s}: {score:3.0f}/100")
        
        print(f"\nOverall: {result['overall_quality']:.0f}/100 ({result['overall_confidence']})")
        print(f"Status: {summary.get('status', 'UNKNOWN')}")
        
        if result.get('errors'):
            print(f"\nErrors: {len(result['errors'])}")
            for error in result['errors'][:3]:
                print(f"  - [{error['stage']}] {error['error'][:50]}")
        
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
            json.dump(result, f, indent=2)
        
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