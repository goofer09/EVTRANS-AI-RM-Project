"""
COMPREHENSIVE VALIDATOR TESTING SUITE
Tests individual stages + end-to-end pipeline validation
Tests for hallucinations, accuracy, and integration issues
"""

import json
from datetime import datetime
from typing import Dict, List
from workflow_integrator import WorkflowIntegrator


class ValidatorEnricher:
    """
    Validates ENRICHER stage only
    Tests for hallucinations and component validity
    """
    
    def __init__(self, debug=True):
        self.debug = debug
        self.tests = []
    
    def test_hallucination(self, hs_code: str, components: List[Dict],
                          known_components: List[str] = None) -> Dict:
        """
        Test if enricher is hallucinating components
        """
        
        test = {
            'timestamp': datetime.now().isoformat(),
            'stage': 'enricher',
            'test_type': 'hallucination',
            'hs_code': hs_code,
            'components_identified': [c.get('name') for c in components],
            'results': {},
            'summary': {}
        }
        
        print(f"\n[VALIDATOR-ENRICHER] Testing for Hallucinations")
        print(f"HS Code: {hs_code}")
        print(f"Components: {len(components)}")
        
        hallucinations = 0
        real_components = 0
        unsure = 0
        
        if known_components:
            print(f"\nValidating against {len(known_components)} known components...\n")
            
            for comp in components:
                comp_name = comp.get('name')
                
                print(f"'{comp_name}' - Is this real? (yes/no/unsure): ", end="")
                is_real = input().lower()
                
                in_known = comp_name in known_components
                
                result = {
                    'validation': is_real,
                    'in_known_list': in_known,
                    'cost_share': comp.get('cost_share'),
                    'description': comp.get('description', '')[:80]
                }
                
                if is_real == 'yes':
                    real_components += 1
                elif is_real == 'no':
                    hallucinations += 1
                else:
                    unsure += 1
                
                test['results'][comp_name] = result
        
        test['summary'] = {
            'total': len(components),
            'real': real_components,
            'hallucinations': hallucinations,
            'unsure': unsure,
            'hallucination_rate': f"{hallucinations}/{len(components)}"
        }
        
        self.tests.append(test)
        return test
    
    def test_completeness(self, hs_code: str, components: List[Dict]) -> Dict:
        """
        Test if enricher identified all major components
        """
        
        test = {
            'timestamp': datetime.now().isoformat(),
            'stage': 'enricher',
            'test_type': 'completeness',
            'hs_code': hs_code,
            'components': len(components),
            'issues': []
        }
        
        print(f"\n[VALIDATOR-ENRICHER] Testing Completeness")
        print(f"HS Code: {hs_code}")
        
        # Check component count
        if len(components) != 4:
            test['issues'].append({
                'type': 'count_mismatch',
                'expected': 4,
                'actual': len(components)
            })
        
        # Check cost shares sum to 1.0
        total_cost = sum(c.get('cost_share', 0) for c in components)
        if abs(total_cost - 1.0) > 0.01:
            test['issues'].append({
                'type': 'cost_share_sum',
                'expected': 1.0,
                'actual': total_cost,
                'error': abs(total_cost - 1.0)
            })
        
        # Check for required fields
        for comp in components:
            required = ['name', 'cost_share', 'description', 'subsystem']
            missing = [f for f in required if f not in comp or not comp[f]]
            if missing:
                test['issues'].append({
                    'component': comp.get('name'),
                    'type': 'missing_fields',
                    'missing': missing
                })
        
        test['valid'] = len(test['issues']) == 0
        self.tests.append(test)
        return test


class ValidatorClassifier:
    """
    Validates CLASSIFIER stage only
    Tests for accuracy and correctness of classifications
    """
    
    def __init__(self, debug=True):
        self.debug = debug
        self.tests = []
    
    def test_accuracy(self, hs_code: str, components: List[Dict],
                     classifications: List[Dict],
                     ground_truth: Dict = None) -> Dict:
        """
        Test classifier accuracy against ground truth
        """
        
        test = {
            'timestamp': datetime.now().isoformat(),
            'stage': 'classifier',
            'test_type': 'accuracy',
            'hs_code': hs_code,
            'results': {},
            'metrics': {}
        }
        
        print(f"\n[VALIDATOR-CLASSIFIER] Testing Accuracy")
        print(f"HS Code: {hs_code}")
        
        correct = 0
        total = len(classifications)
        
        for i, (comp, classif) in enumerate(zip(components, classifications), 1):
            comp_name = comp.get('name')
            predicted = classif.get('classification')
            
            print(f"\n{i}. {comp_name}")
            print(f"   Predicted: {predicted}")
            
            if ground_truth and comp_name in ground_truth:
                actual = ground_truth[comp_name]
                print(f"   Expected: {actual}")
                
                is_correct = predicted == actual
                if is_correct:
                    correct += 1
                    print("   ✅ Correct")
                else:
                    print("   ❌ Wrong")
            else:
                print(f"   Actual (validator input): ", end="")
                actual = input()
                
                is_correct = predicted == actual
                if is_correct:
                    correct += 1
                    print("   ✅ Correct")
                else:
                    print("   ❌ Wrong")
            
            test['results'][comp_name] = {
                'predicted': predicted,
                'actual': actual,
                'correct': is_correct,
                'confidence': classif.get('similarity_score', 0)
            }
        
        accuracy = (correct / total * 100) if total > 0 else 0
        
        test['metrics'] = {
            'accuracy': f"{correct}/{total} ({accuracy:.0f}%)",
            'correct_count': correct,
            'total_count': total,
            'error_rate': f"{100-accuracy:.0f}%"
        }
        
        self.tests.append(test)
        return test
    
    def test_confidence_calibration(self, classifications: List[Dict]) -> Dict:
        """
        Test if confidence scores correlate with accuracy
        """
        
        test = {
            'timestamp': datetime.now().isoformat(),
            'stage': 'classifier',
            'test_type': 'confidence_calibration',
            'results': {}
        }
        
        print(f"\n[VALIDATOR-CLASSIFIER] Testing Confidence Calibration")
        
        high_confidence = [c for c in classifications if c.get('similarity_score', 0) >= 0.8]
        low_confidence = [c for c in classifications if c.get('similarity_score', 0) < 0.8]
        
        test['results'] = {
            'high_confidence_count': len(high_confidence),
            'low_confidence_count': len(low_confidence),
            'avg_high_confidence': sum(c.get('similarity_score', 0) for c in high_confidence) / len(high_confidence) if high_confidence else 0,
            'avg_low_confidence': sum(c.get('similarity_score', 0) for c in low_confidence) / len(low_confidence) if low_confidence else 0
        }
        
        self.tests.append(test)
        return test


class ValidatorScorer:
    """
    Validates SCORER stage only
    Tests for reasonableness and consistency of scores
    """
    
    def __init__(self, debug=True):
        self.debug = debug
        self.tests = []
    
    def test_reasonableness(self, hs_code: str, components: List[Dict],
                           scores: List[Dict],
                           acceptable_ranges: Dict = None) -> Dict:
        """
        Test if scores are within reasonable ranges
        """
        
        if not acceptable_ranges:
            acceptable_ranges = {
                'tech': (20, 95),
                'manufacturing': (10, 95),
                'supply_chain': (30, 100),
                'demand': (5, 90),
                'value': (15, 95),
                'regulatory': (0, 100)
            }
        
        test = {
            'timestamp': datetime.now().isoformat(),
            'stage': 'scorer',
            'test_type': 'reasonableness',
            'hs_code': hs_code,
            'results': {},
            'out_of_range': [],
            'summary': {}
        }
        
        print(f"\n[VALIDATOR-SCORER] Testing Score Reasonableness")
        print(f"HS Code: {hs_code}")
        
        out_of_range_count = 0
        dimensions = ['tech', 'manufacturing', 'supply_chain', 'demand', 'value', 'regulatory']
        
        for i, (comp, score) in enumerate(zip(components, scores), 1):
            comp_name = comp.get('name')
            print(f"\n{i}. {comp_name}")
            
            comp_results = {}
            
            for dim in dimensions:
                score_val = score.get(dim, 0)
                min_val, max_val = acceptable_ranges[dim]
                in_range = min_val <= score_val <= max_val
                
                print(f"   {dim:15s}: {score_val:3.0f} ", end="")
                
                if in_range:
                    print("✅")
                else:
                    print(f"❌ (expected {min_val}-{max_val})")
                    out_of_range_count += 1
                    test['out_of_range'].append({
                        'component': comp_name,
                        'dimension': dim,
                        'value': score_val,
                        'range': (min_val, max_val)
                    })
                
                comp_results[dim] = {
                    'value': score_val,
                    'in_range': in_range,
                    'range': (min_val, max_val)
                }
            
            test['results'][comp_name] = comp_results
        
        test['summary'] = {
            'total_scores': len(components) * len(dimensions),
            'out_of_range': out_of_range_count,
            'valid_rate': f"{len(components) * len(dimensions) - out_of_range_count}/{len(components) * len(dimensions)}"
        }
        
        self.tests.append(test)
        return test
    
    def test_consistency(self, scores: List[Dict]) -> Dict:
        """
        Test if scores are consistent across components
        """
        
        test = {
            'timestamp': datetime.now().isoformat(),
            'stage': 'scorer',
            'test_type': 'consistency',
            'results': {},
            'issues': []
        }
        
        print(f"\n[VALIDATOR-SCORER] Testing Score Consistency")
        
        dimensions = ['tech', 'manufacturing', 'supply_chain', 'demand', 'value', 'regulatory']
        
        for dim in dimensions:
            dim_scores = [s.get(dim, 0) for s in scores]
            avg = sum(dim_scores) / len(dim_scores) if dim_scores else 0
            std_dev = (sum((x - avg) ** 2 for x in dim_scores) / len(dim_scores)) ** 0.5 if dim_scores else 0
            
            # If std dev is very high, might indicate inconsistency
            if std_dev > 30:
                test['issues'].append({
                    'dimension': dim,
                    'avg': avg,
                    'std_dev': std_dev,
                    'issue': 'High variance - inconsistent scoring'
                })
            
            test['results'][dim] = {
                'avg': avg,
                'min': min(dim_scores) if dim_scores else 0,
                'max': max(dim_scores) if dim_scores else 0,
                'std_dev': std_dev
            }
        
        self.tests.append(test)
        return test


class ValidatorPipeline:
    """
    Validates END-TO-END pipeline
    Tests all stages together and integration points
    """
    
    def __init__(self, debug=True):
        self.debug = debug
        self.validator_enricher = ValidatorEnricher(debug=debug)
        self.validator_classifier = ValidatorClassifier(debug=debug)
        self.validator_scorer = ValidatorScorer(debug=debug)
        self.pipeline_tests = []
    
    def validate_complete_analysis(self, hs_code: str, description: str,
                                  enricher_output: List[Dict],
                                  classifier_output: List[Dict],
                                  scorer_output: List[Dict],
                                  ground_truth: Dict = None) -> Dict:
        """
        Validate complete end-to-end analysis
        """
        
        print(f"\n{'='*70}")
        print(f"COMPLETE PIPELINE VALIDATION")
        print(f"{'='*70}")
        
        pipeline_test = {
            'timestamp': datetime.now().isoformat(),
            'hs_code': hs_code,
            'description': description,
            'stages': {}
        }
        
        # STAGE 1: ENRICHER
        print(f"\n{'='*70}")
        print("STAGE 1: ENRICHER VALIDATION")
        print(f"{'='*70}")
        
        known_components = ['Brake pads', 'Brake rotor', 'Brake caliper', 'Master cylinder']  # Example
        enricher_hall = self.validator_enricher.test_hallucination(hs_code, enricher_output, known_components)
        enricher_complete = self.validator_enricher.test_completeness(hs_code, enricher_output)
        
        pipeline_test['stages']['enricher'] = {
            'hallucination_test': enricher_hall,
            'completeness_test': enricher_complete,
            'status': 'PASS' if enricher_hall['summary']['hallucinations'] == 0 and enricher_complete['valid'] else 'FAIL'
        }
        
        # STAGE 2: CLASSIFIER
        print(f"\n{'='*70}")
        print("STAGE 2: CLASSIFIER VALIDATION")
        print(f"{'='*70}")
        
        classifier_accuracy = self.validator_classifier.test_accuracy(
            hs_code, enricher_output, classifier_output, ground_truth
        )
        classifier_confidence = self.validator_classifier.test_confidence_calibration(classifier_output)
        
        pipeline_test['stages']['classifier'] = {
            'accuracy_test': classifier_accuracy,
            'confidence_test': classifier_confidence,
            'status': 'PASS' if int(classifier_accuracy['metrics']['correct_count']) > 0 else 'FAIL'
        }
        
        # STAGE 3: SCORER
        print(f"\n{'='*70}")
        print("STAGE 3: SCORER VALIDATION")
        print(f"{'='*70}")
        
        scorer_reasonable = self.validator_scorer.test_reasonableness(hs_code, enricher_output, scorer_output)
        scorer_consistent = self.validator_scorer.test_consistency(scorer_output)
        
        pipeline_test['stages']['scorer'] = {
            'reasonableness_test': scorer_reasonable,
            'consistency_test': scorer_consistent,
            'status': 'PASS' if len(scorer_reasonable['out_of_range']) == 0 else 'FAIL'
        }
        
        # INTEGRATION CHECKS
        print(f"\n{'='*70}")
        print("INTEGRATION CHECKS")
        print(f"{'='*70}")
        
        integration = self._test_integration(enricher_output, classifier_output, scorer_output)
        pipeline_test['integration'] = integration
        
        # OVERALL STATUS
        all_stages_pass = all(
            pipeline_test['stages'][stage].get('status') == 'PASS' 
            for stage in ['enricher', 'classifier', 'scorer']
        )
        
        pipeline_test['overall_status'] = 'PASS' if (all_stages_pass and integration['valid']) else 'FAIL'
        
        self.pipeline_tests.append(pipeline_test)
        
        self._print_pipeline_summary(pipeline_test)
        
        return pipeline_test
    
    def _test_integration(self, enricher_output: List[Dict],
                         classifier_output: List[Dict],
                         scorer_output: List[Dict]) -> Dict:
        """
        Test integration between stages
        """
        
        print(f"\n[VALIDATOR-PIPELINE] Testing Integration")
        
        integration = {
            'timestamp': datetime.now().isoformat(),
            'checks': {},
            'issues': [],
            'valid': True
        }
        
        # Check 1: Component count consistency
        enricher_count = len(enricher_output)
        classifier_count = len(classifier_output)
        scorer_count = len(scorer_output)
        
        if enricher_count == classifier_count == scorer_count:
            integration['checks']['component_count'] = 'PASS'
        else:
            integration['checks']['component_count'] = 'FAIL'
            integration['issues'].append({
                'type': 'component_count_mismatch',
                'enricher': enricher_count,
                'classifier': classifier_count,
                'scorer': scorer_count
            })
            integration['valid'] = False
        
        # Check 2: Component order consistency
        enricher_names = [c.get('name') for c in enricher_output]
        classifier_names = [c.get('component') for c in classifier_output]
        
        if enricher_names == classifier_names or enricher_names == classifier_names:
            integration['checks']['component_order'] = 'PASS'
        else:
            integration['checks']['component_order'] = 'WARN'
            integration['issues'].append({
                'type': 'component_order_mismatch',
                'note': 'Components may be in different order'
            })
        
        # Check 3: All components scored
        if scorer_count == enricher_count:
            integration['checks']['all_scored'] = 'PASS'
        else:
            integration['checks']['all_scored'] = 'FAIL'
            integration['issues'].append({
                'type': 'missing_scores',
                'expected': enricher_count,
                'actual': scorer_count
            })
            integration['valid'] = False
        
        return integration
    
    def _print_pipeline_summary(self, pipeline_test: Dict):
        """Print pipeline validation summary"""
        
        print(f"\n{'='*70}")
        print("VALIDATION SUMMARY")
        print(f"{'='*70}")
        
        for stage in ['enricher', 'classifier', 'scorer']:
            if stage in pipeline_test['stages']:
                status = pipeline_test['stages'][stage]['status']
                symbol = "✅" if status == "PASS" else "❌"
                print(f"\n{symbol} {stage.upper()}: {status}")
        
        # Integration
        integration = pipeline_test.get('integration', {})
        print(f"\nIntegration: {len(integration.get('issues', []))} issues")
        for issue in integration.get('issues', [])[:3]:
            print(f"  - {issue.get('type')}")
        
        # Overall
        overall = pipeline_test['overall_status']
        symbol = "✅" if overall == "PASS" else "❌"
        print(f"\n{symbol} OVERALL: {overall}")
        print(f"\n{'='*70}\n")
    
    def save_validation_results(self, filename: str = None) -> str:
        """Save complete validation results"""
        
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"validator_complete_{timestamp}.json"
        
        output = {
            'timestamp': datetime.now().isoformat(),
            'pipeline_tests': self.pipeline_tests,
            'summary': {
                'total_tests': len(self.pipeline_tests),
                'passed': sum(1 for t in self.pipeline_tests if t['overall_status'] == 'PASS'),
                'failed': sum(1 for t in self.pipeline_tests if t['overall_status'] == 'FAIL')
            }
        }
        
        with open(filename, 'w') as f:
            json.dump(output, f, indent=2, default=str)
        
        print(f"\nValidation results saved to: {filename}")
        return filename


# ====================================
# USAGE EXAMPLE
# ====================================

if __name__ == "__main__":
    validator = ValidatorPipeline(debug=True)
    
    # Example data
    enricher_output = [
        {'name': 'Brake pads', 'cost_share': 0.35, 'description': '...', 'subsystem': 'Braking'},
        {'name': 'Brake rotor', 'cost_share': 0.30, 'description': '...', 'subsystem': 'Braking'},
        {'name': 'Brake caliper', 'cost_share': 0.20, 'description': '...', 'subsystem': 'Braking'},
        {'name': 'Master cylinder', 'cost_share': 0.15, 'description': '...', 'subsystem': 'Braking'},
    ]
    
    classifier_output = [
        {'classification': 'SHARED', 'similarity_score': 0.92},
        {'classification': 'SHARED', 'similarity_score': 0.88},
        {'classification': 'ICE_ONLY', 'similarity_score': 0.75},
        {'classification': 'SHARED', 'similarity_score': 0.80},
    ]
    
    scorer_output = [
        {'tech': 70, 'manufacturing': 75, 'supply_chain': 80, 'demand': 65, 'value': 70, 'regulatory': 60},
        {'tech': 75, 'manufacturing': 70, 'supply_chain': 85, 'demand': 70, 'value': 75, 'regulatory': 65},
        {'tech': 80, 'manufacturing': 80, 'supply_chain': 90, 'demand': 75, 'value': 80, 'regulatory': 70},
        {'tech': 65, 'manufacturing': 70, 'supply_chain': 75, 'demand': 60, 'value': 65, 'regulatory': 55},
    ]
    
    ground_truth = {
        'Brake pads': 'SHARED',
        'Brake rotor': 'SHARED',
        'Brake caliper': 'ICE_ONLY',
        'Master cylinder': 'SHARED'
    }
    
    # Run validation
    results = validator.validate_complete_analysis(
        '8708.30',
        'Brake systems',
        enricher_output,
        classifier_output,
        scorer_output,
        ground_truth
    )
    
    # Save results
    validator.save_validation_results()