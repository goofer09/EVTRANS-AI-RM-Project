# WORKFLOW INTEGRATOR - FIXED WITH TIMEOUT ERROR SAFEGUARDS
## Complete Implementation with Proper Error Propagation

"""
Workflow Integrator - FIXED VERSION
Master orchestrator for enricher → classifier → scorer → validator

FIXES INCLUDED:
- Proper timeout error handling
- Error type tracking (TIMEOUT vs ERROR)
- Safeguards against critical failures
- Error propagation back to integrator
- Integrator stops on total failure (doesn't hang)
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
    
    FIXED: Proper timeout error handling and safeguards
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
            print("[INTEGRATOR] Workflow integrator initialized")
    
    # ============================================
    # STAGE 1: ENRICHER
    # ============================================
    
    def run_enricher(self, hs_code: str, description: str) -> Optional[List[Dict]]:
        """
        Run enricher stage: Identify 2 components

        Args:
            hs_code: HS code (e.g., "8708.30")
            description: Description (e.g., "Brake systems")

        Returns:
            List of 2 components or None if failed
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
                        print(f"[INTEGRATOR]   {i}. {comp.get('name')} (cost: {comp.get('cost_share')})")
                
                return result
            
            # ✅ CATCH TIMEOUT ERRORS
            except TimeoutError as e:
                error_msg = f"Enricher TIMEOUT (attempt {attempt}): {str(e)}"
                if self.debug:
                    print(f"❌ TIMEOUT")
                
                self.errors.append({
                    'stage': 'enricher',
                    'attempt': attempt,
                    'error': str(e),
                    'error_type': 'TIMEOUT',
                    'timestamp': datetime.now().isoformat()
                })
                
                # Don't retry timeout for enricher - just fail
                if self.debug:
                    print(f"[INTEGRATOR] Enricher timeout - cannot retry")
                return None
            
            # ✅ CATCH OTHER ERRORS
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
    # STAGE 2: CLASSIFIER (FIXED)
    # ============================================
    
    def run_classifier(self, enricher_output: List[Dict]) -> Optional[List[Dict]]:
        """
        Run classifier stage: Classify each component (ICE/EV/SHARED)

        FIXED: Proper error handling and safeguards

        Args:
            enricher_output: List of 2 components from enricher

        Returns:
            List of 2 classifications or None if all failed
        """
        
        self.current_stage = "classifier"
        
        if self.debug:
            print(f"\n[INTEGRATOR] Stage 2: CLASSIFIER")
            print(f"[INTEGRATOR] Classifying {len(enricher_output)} components...")
        
        classifications = []
        failed_components = []
        timeout_count = 0
        
        # Classify each component
        for i, component in enumerate(enricher_output, 1):
            comp_name = component.get('name', f'Component {i}')
            
            for attempt in range(1, self.max_retries + 1):
                try:
                    if self.debug:
                        print(f"[INTEGRATOR] Classifying {i}/2: {comp_name} (attempt {attempt})...", end=" ")
                    
                    start = time.time()
                    results = self.classifier.classify(
                        [comp_name],  # Pass as list with single item
                        self.current_hs_code
                    )
                    elapsed = time.time() - start

                    if not results or len(results) == 0:
                        raise ValueError("Classifier returned empty result")

                    result = results[0]  # Get first (and only) result

                    if 'classification' not in result:
                        raise ValueError("Classifier missing 'classification' field")

                    if 'similarity_score' not in result:
                        raise ValueError("Classifier missing 'similarity_score' field")

                    classifications.append(result)
                    
                    if self.debug:
                        print(f"✅ {result['classification']} (similarity: {result['similarity_score']:.2f})")
                    
                    break  # Success, move to next component
                
                # ✅ CATCH TIMEOUT ERRORS SPECIFICALLY
                except TimeoutError as e:
                    error_msg = f"Classifier TIMEOUT for {comp_name} (attempt {attempt}): {str(e)}"
                    if self.debug:
                        print(f"❌ TIMEOUT")
                    
                    timeout_count += 1
                    
                    self.errors.append({
                        'stage': 'classifier',
                        'component': comp_name,
                        'attempt': attempt,
                        'error': str(e),
                        'error_type': 'TIMEOUT',  # ← Mark as timeout
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    # ✅ DON'T RETRY TIMEOUTS (they won't get faster)
                    # Use default and move to next component
                    if attempt == 1:
                        classifications.append({
                            'classification': 'UNKNOWN',
                            'similarity_score': 0.0,
                            'error': 'TIMEOUT'
                        })
                        failed_components.append(comp_name)
                        break
                
                # ✅ CATCH OTHER ERRORS
                except Exception as e:
                    error_msg = f"Classifier failed for {comp_name} (attempt {attempt}): {str(e)}"
                    if self.debug:
                        print(f"❌ ERROR")
                    
                    self.errors.append({
                        'stage': 'classifier',
                        'component': comp_name,
                        'attempt': attempt,
                        'error': str(e),
                        'error_type': 'ERROR',
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    if attempt == self.max_retries:
                        # Used all retries
                        classifications.append({
                            'classification': 'UNKNOWN',
                            'similarity_score': 0.0,
                            'error': str(e)
                        })
                        failed_components.append(comp_name)
                        break
                    
                    # Otherwise retry (for non-timeout errors)
        
        # ✅ VALIDATION: Check if counts match
        if len(classifications) != len(enricher_output):
            error_msg = f"Classifier returned {len(classifications)} results for {len(enricher_output)} components"
            if self.debug:
                print(f"[INTEGRATOR] ⚠️ Warning: {error_msg}")
            self.warnings.append(error_msg)
        
        # ✅ SAFEGUARD: Check if ALL components failed
        if len(failed_components) == len(enricher_output):
            error_msg = f"Classifier CRITICAL FAILURE - all {len(enricher_output)} components failed"
            if self.debug:
                print(f"[INTEGRATOR] ❌ {error_msg}")
                if timeout_count > 0:
                    print(f"[INTEGRATOR]    ({timeout_count} timeouts)")
            
            self.errors.append({
                'stage': 'classifier',
                'error': error_msg,
                'error_type': 'CRITICAL_FAILURE',
                'timeout_count': timeout_count,
                'timestamp': datetime.now().isoformat()
            })
            
            # ✅ RETURN NONE - SIGNAL FAILURE TO INTEGRATOR
            return None
        
        # ✅ Return results (even if partial)
        if classifications:
            return classifications
        else:
            return None
    
    # ============================================
    # STAGE 3: SCORER (FIXED)
    # ============================================
    
    def run_scorer(self, enricher_output: List[Dict]) -> Optional[List[Dict]]:
        """
        Run scorer stage: Score each component on 6 dimensions

        FIXED: Proper error handling and safeguards

        Args:
            enricher_output: List of 2 components from enricher

        Returns:
            List of 2 score sets or None if all failed
        """
        
        self.current_stage = "scorer"
        
        if self.debug:
            print(f"\n[INTEGRATOR] Stage 3: SCORER")
            print(f"[INTEGRATOR] Scoring {len(enricher_output)} components...")
        
        scores = []
        failed_components = []
        timeout_count = 0
        
        # Score each component
        for i, component in enumerate(enricher_output, 1):
            comp_name = component.get('name', f'Component {i}')
            
            for attempt in range(1, self.max_retries + 1):
                try:
                    if self.debug:
                        print(f"[INTEGRATOR] Scoring {i}/2: {comp_name} (attempt {attempt})...", end=" ")

                    start = time.time()
                    results = self.scorer.score(
                        [comp_name],  # Pass as list with single item
                        self.current_hs_code
                    )
                    elapsed = time.time() - start

                    if not results or len(results) == 0:
                        raise ValueError("Scorer returned empty result")

                    result = results[0]  # Get first (and only) result

                    required_dims = ['tech', 'manufacturing', 'supply_chain', 'demand', 'value', 'regulatory']
                    for dim in required_dims:
                        if dim not in result:
                            raise ValueError(f"Scorer missing '{dim}' field")

                    scores.append(result)
                    
                    if self.debug:
                        print(f"✅ Scores assigned ({elapsed:.1f}s)")
                    
                    break  # Success
                
                # ✅ CATCH TIMEOUT ERRORS SPECIFICALLY
                except TimeoutError as e:
                    error_msg = f"Scorer TIMEOUT for {comp_name} (attempt {attempt})"
                    if self.debug:
                        print(f"❌ TIMEOUT")
                    
                    timeout_count += 1
                    
                    self.errors.append({
                        'stage': 'scorer',
                        'component': comp_name,
                        'attempt': attempt,
                        'error': str(e),
                        'error_type': 'TIMEOUT',  # ← Mark as timeout
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    # ✅ DON'T RETRY TIMEOUTS
                    if attempt == 1:
                        scores.append({
                            'tech': 50, 'manufacturing': 50, 'supply_chain': 50,
                            'demand': 50, 'value': 50, 'regulatory': 50,
                            'error': 'TIMEOUT'
                        })
                        failed_components.append(comp_name)
                        break
                
                # ✅ CATCH OTHER ERRORS
                except Exception as e:
                    error_msg = f"Scorer failed for {comp_name} (attempt {attempt})"
                    if self.debug:
                        print(f"❌ ERROR")
                    
                    self.errors.append({
                        'stage': 'scorer',
                        'component': comp_name,
                        'attempt': attempt,
                        'error': str(e),
                        'error_type': 'ERROR',
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    if attempt == self.max_retries:
                        scores.append({
                            'tech': 50, 'manufacturing': 50, 'supply_chain': 50,
                            'demand': 50, 'value': 50, 'regulatory': 50,
                            'error': str(e)
                        })
                        failed_components.append(comp_name)
                        break
        
        # ✅ VALIDATION: Check if counts match
        if len(scores) != len(enricher_output):
            warning = f"Scorer returned {len(scores)} results for {len(enricher_output)} components"
            if self.debug:
                print(f"[INTEGRATOR] ⚠️ Warning: {warning}")
            self.warnings.append(warning)
        
        # ✅ SAFEGUARD: Check if ALL components failed
        if len(failed_components) == len(enricher_output):
            error_msg = f"Scorer CRITICAL FAILURE - all {len(enricher_output)} components failed"
            if self.debug:
                print(f"[INTEGRATOR] ❌ {error_msg}")
                if timeout_count > 0:
                    print(f"[INTEGRATOR]    ({timeout_count} timeouts)")
            
            self.errors.append({
                'stage': 'scorer',
                'error': error_msg,
                'error_type': 'CRITICAL_FAILURE',
                'timeout_count': timeout_count,
                'timestamp': datetime.now().isoformat()
            })
            
            # ✅ RETURN NONE - SIGNAL FAILURE TO INTEGRATOR
            return None
        
        # ✅ Return results (even if partial)
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
        
        # ✅ CATCH VALIDATION ERRORS
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
            
            # Return minimal validation result
            return {
                'overall_quality': 0,
                'overall_confidence': 'LOW',
                'valid': False,
                'error': str(e)
            }
    
    # ============================================
    # MAIN ORCHESTRATION (FIXED)
    # ============================================
    
    def run_complete_analysis(self, hs_code: str, description: str) -> Dict:
        """
        Run complete analysis workflow: Enricher → Classifier → Scorer → Validator
        
        FIXED: Proper error checking at each stage
        
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
            # ✅ CHECK FOR ERRORS
            timeout_errors = [e for e in self.errors if e.get('stage') == 'enricher' and e.get('error_type') == 'TIMEOUT']
            if timeout_errors:
                return self._error_result(f"Enricher timeout after {self.max_retries} attempts")
            else:
                return self._error_result("Enricher failed - cannot identify components")
        
        # STAGE 2: CLASSIFIER
        classifier_output = self.run_classifier(enricher_output)
        if not classifier_output:
            # ✅ CHECK FOR ERRORS
            timeout_errors = [e for e in self.errors if e.get('stage') == 'classifier' and e.get('error_type') == 'TIMEOUT']
            if timeout_errors:
                return self._error_result(f"Classifier timeout on all components - {len(timeout_errors)} timeouts")
            else:
                return self._error_result("Classifier failed on all components")
        
        # STAGE 3: SCORER
        scorer_output = self.run_scorer(enricher_output)
        if not scorer_output:
            # ✅ CHECK FOR ERRORS
            timeout_errors = [e for e in self.errors if e.get('stage') == 'scorer' and e.get('error_type') == 'TIMEOUT']
            if timeout_errors:
                return self._error_result(f"Scorer timeout on all components - {len(timeout_errors)} timeouts")
            else:
                return self._error_result("Scorer failed on all components")
        
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
            'errors': self.errors,  # ✅ ALL ERRORS TRACKED
            'warnings': self.warnings,  # ✅ ALL WARNINGS TRACKED
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
        
        print(f"\nQuality Scores:")
        for stage, score in summary.get('quality_by_stage', {}).items():
            status = '✅' if score >= 70 else '⚠️ ' if score >= 50 else '❌'
            print(f"  {status} {stage:12s}: {score:3.0f}/100")
        
        print(f"\nOverall: {result['overall_quality']:.0f}/100 ({result['overall_confidence']})")
        print(f"Status: {summary.get('status', 'UNKNOWN')}")
        
        # Show errors if any
        if result.get('errors'):
            print(f"\n⚠️ Errors encountered: {len(result['errors'])}")
            
            # Group by error type
            timeout_errors = [e for e in result['errors'] if e.get('error_type') == 'TIMEOUT']
            other_errors = [e for e in result['errors'] if e.get('error_type') != 'TIMEOUT']
            
            if timeout_errors:
                print(f"  Timeouts: {len(timeout_errors)}")
            if other_errors:
                print(f"  Other errors: {len(other_errors)}")
            
            # Show first few errors
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
