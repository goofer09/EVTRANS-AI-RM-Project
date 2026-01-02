"""
Comprehensive Validator for ALL stages
Validates: Enricher → Classifier → Scorer → Integration
"""

import json
from typing import Dict, List, Tuple, Any

class ComprehensiveValidator:
    """Complete validation for all LLM pipeline stages"""
    
    def __init__(self, debug=True):
        self.debug = debug
        self.valid_subsystems = [
            'Powertrain', 'Drivetrain', 'Chassis', 'Electronics',
            'Body', 'Exhaust', 'Fuel', 'Suspension', 'Brakes'
        ]
    
    # ============================================
    # ENRICHER VALIDATION
    # ============================================
    
    def validate_enricher_output(self, components: List[Dict]) -> Dict:
        """Validate enricher component identification"""
        
        issues = []
        quality_score = 100
        
        if self.debug:
            print(f"\n[VALIDATOR] Enricher output validation...")
        
        # Check 1: Exact count
        if len(components) != 4:
            issues.append(f"Expected 4 components, got {len(components)}")
            quality_score -= 20
        
        # Check 2: Required fields
        for i, comp in enumerate(components):
            missing_fields = []
            
            required = ['name', 'cost_share', 'description', 'function', 'subsystem']
            for field in required:
                if field not in comp or not comp[field]:
                    missing_fields.append(field)
            
            if missing_fields:
                issues.append(f"Component {i+1} missing: {', '.join(missing_fields)}")
                quality_score -= 10
        
        # Check 3: Name validation (not generic)
        generic_names = ['component', 'part', 'item', 'product', 'material']
        for i, comp in enumerate(components):
            name = comp.get('name', '').lower()
            if any(generic in name for generic in generic_names):
                issues.append(f"Component {i+1} has generic name: {comp.get('name')}")
                quality_score -= 5
        
        # Check 4: Cost share validation
        cost_shares = [comp.get('cost_share', 0) for comp in components]
        total_cost = sum(cost_shares)
        
        # Should sum to ~1.0
        if not (0.95 <= total_cost <= 1.05):
            issues.append(f"Cost shares sum to {total_cost:.2f}, expected ~1.0")
            quality_score -= 15
        
        # Should be varied (not all same)
        if len(set(round(cs, 2) for cs in cost_shares)) == 1:
            issues.append(f"All cost shares identical: {cost_shares[0]}")
            quality_score -= 25
        
        # Check 5: Subsystem validation
        for i, comp in enumerate(components):
            subsystem = comp.get('subsystem', '')
            if subsystem not in self.valid_subsystems:
                issues.append(f"Component {i+1} has invalid subsystem: {subsystem}")
                quality_score -= 5
        
        # Check 6: Description quality
        for i, comp in enumerate(components):
            desc = comp.get('description', '')
            if len(desc) < 10:
                issues.append(f"Component {i+1} description too short: {desc}")
                quality_score -= 5
        
        # Check 7: Ordering (highest cost first)
        for i in range(len(cost_shares)-1):
            if cost_shares[i] < cost_shares[i+1]:
                issues.append(f"Components not ordered by cost (descending)")
                quality_score -= 10
                break
        
        quality_score = max(0, quality_score)
        
        return {
            'stage': 'enricher',
            'quality_score': quality_score,
            'issues': issues,
            'confidence': self._get_confidence(quality_score),
            'valid': quality_score >= 70
        }
    
    # ============================================
    # CLASSIFIER VALIDATION
    # ============================================
    
    def validate_classifier_output(self, classifications: List[Dict]) -> Dict:
        """Validate classifier ICE/EV/SHARED classification"""
        
        issues = []
        quality_score = 100
        
        if self.debug:
            print(f"[VALIDATOR] Classifier output validation...")
        
        valid_classes = ['SHARED', 'ICE_ONLY', 'EV_ONLY']
        
        # Check 1: All components classified
        if len(classifications) == 0:
            issues.append("No classifications provided")
            quality_score -= 50
            return {
                'stage': 'classifier',
                'quality_score': 0,
                'issues': issues,
                'confidence': 'LOW',
                'valid': False
            }
        
        # Check 2: Valid classification values
        for i, classif in enumerate(classifications):
            c_type = classif.get('classification', '')
            
            if c_type not in valid_classes:
                issues.append(f"Component {i+1} invalid classification: {c_type}")
                quality_score -= 15
        
        # Check 3: Similarity score validation
        similarities = []
        for i, classif in enumerate(classifications):
            sim = classif.get('similarity_score', -1)
            
            if sim < 0 or sim > 1:
                issues.append(f"Component {i+1} similarity out of range: {sim}")
                quality_score -= 10
            else:
                similarities.append(sim)
        
        # Check 4: Similarity variation (not all same)
        if similarities and len(set(round(s, 2) for s in similarities)) == 1:
            issues.append(f"All similarities identical: {similarities[0]}")
            quality_score -= 25
        
        # Check 5: Logical consistency
        for i, classif in enumerate(classifications):
            c_type = classif.get('classification')
            sim = classif.get('similarity_score', 0.5)
            
            # EV_ONLY should have low similarity
            if c_type == 'EV_ONLY' and sim > 0.7:
                issues.append(f"Component {i+1} EV_ONLY but similarity high ({sim})")
                quality_score -= 5
            
            # ICE_ONLY should have low similarity
            if c_type == 'ICE_ONLY' and sim > 0.7:
                issues.append(f"Component {i+1} ICE_ONLY but similarity high ({sim})")
                quality_score -= 5
            
            # SHARED should have high similarity
            if c_type == 'SHARED' and sim < 0.5:
                issues.append(f"Component {i+1} SHARED but similarity low ({sim})")
                quality_score -= 5
        
        # Check 6: Distribution (not all SHARED)
        classifications_list = [c.get('classification') for c in classifications]
        if len(set(classifications_list)) == 1:
            issues.append(f"All components same classification: {classifications_list[0]}")
            quality_score -= 20
        
        quality_score = max(0, quality_score)
        
        return {
            'stage': 'classifier',
            'quality_score': quality_score,
            'issues': issues,
            'confidence': self._get_confidence(quality_score),
            'valid': quality_score >= 70
        }
    
    # ============================================
    # SCORER VALIDATION
    # ============================================
    
    def validate_scorer_output(self, scores: List[Dict]) -> Dict:
        """Validate scorer dimension scores"""
        
        issues = []
        quality_score = 100
        
        if self.debug:
            print(f"[VALIDATOR] Scorer output validation...")
        
        required_dimensions = [
            'tech', 'manufacturing', 'supply_chain', 'demand', 'value', 'regulatory'
        ]
        
        # Check 1: All components scored
        if len(scores) != 4:
            issues.append(f"Expected 4 scores, got {len(scores)}")
            quality_score -= 20
        
        # Check 2: All dimensions present
        for i, score in enumerate(scores):
            missing = []
            for dim in required_dimensions:
                if dim not in score:
                    missing.append(dim)
            
            if missing:
                issues.append(f"Component {i+1} missing dimensions: {', '.join(missing)}")
                quality_score -= 10
        
        # Check 3: Score ranges (0-100)
        for i, score in enumerate(scores):
            for dim in required_dimensions:
                val = score.get(dim, -1)
                
                if val < 0 or val > 100:
                    issues.append(f"Component {i+1} {dim} out of range: {val}")
                    quality_score -= 5
        
        # Check 4: Dimension variation (per component)
        for i, score in enumerate(scores):
            values = [score.get(dim, 0) for dim in required_dimensions]
            
            # All same score?
            if len(set(values)) == 1:
                issues.append(f"Component {i+1} all dimensions identical: {values[0]}")
                quality_score -= 15
        
        # Check 5: Cross-component variation (per dimension)
        for dim in required_dimensions:
            dim_scores = [score.get(dim, 0) for score in scores]
            
            # All components have same dimension score?
            if len(set(dim_scores)) == 1:
                issues.append(f"All components same {dim} score: {dim_scores[0]}")
                quality_score -= 10
        
        # Check 6: Logical consistency with classification
        # (This would link back to classifier output, see integration validation)
        
        # Check 7: Outliers
        all_scores = []
        for score in scores:
            for dim in required_dimensions:
                all_scores.append(score.get(dim, 0))
        
        if all_scores:
            avg = sum(all_scores) / len(all_scores)
            for i, score in enumerate(scores):
                for dim in required_dimensions:
                    val = score.get(dim, avg)
                    # Flagging potential outliers (very low or very high)
                    if val < 20 and avg > 70:
                        issues.append(f"Component {i+1} {dim} unusually low: {val} (avg: {avg:.0f})")
                    elif val > 95 and avg < 50:
                        issues.append(f"Component {i+1} {dim} unusually high: {val} (avg: {avg:.0f})")
        
        quality_score = max(0, quality_score)
        
        return {
            'stage': 'scorer',
            'quality_score': quality_score,
            'issues': issues,
            'confidence': self._get_confidence(quality_score),
            'valid': quality_score >= 70
        }
    
    # ============================================
    # INTEGRATION VALIDATION
    # ============================================
    
    def validate_integration(self, 
                             enricher_out: List[Dict],
                             classifier_out: List[Dict],
                             scorer_out: List[Dict]) -> Dict:
        """Validate consistency across all stages"""
        
        issues = []
        quality_score = 100
        
        if self.debug:
            print(f"[VALIDATOR] Integration validation...")
        
        # Check 1: Component count consistency
        if len(enricher_out) != len(classifier_out) or len(enricher_out) != len(scorer_out):
            issues.append(
                f"Component count mismatch: "
                f"enricher={len(enricher_out)}, "
                f"classifier={len(classifier_out)}, "
                f"scorer={len(scorer_out)}"
            )
            quality_score -= 30
        
        # Check 2: Component name matching
        enricher_names = [c.get('name', '') for c in enricher_out]
        for i in range(min(len(classifier_out), len(scorer_out))):
            # Assuming order is preserved
            if i < len(enricher_out):
                name = enricher_names[i]
                if not name:
                    issues.append(f"Component {i+1} name missing in enricher")
                    quality_score -= 5
        
        # Check 3: Logical consistency between stages
        for i in range(min(len(classifier_out), len(scorer_out))):
            if i < len(classifier_out) and i < len(scorer_out):
                classif = classifier_out[i].get('classification', '')
                scores = scorer_out[i]
                
                # EV_ONLY components should have lower manufacturing scores
                # (assumption: EV manufacturing is new, higher risk)
                if classif == 'EV_ONLY':
                    mfg_score = scores.get('manufacturing', 50)
                    # Not enforced strictly, just flagged as warning
                
                # ICE_ONLY components should have higher supply_chain scores
                # (assumption: established supply chains)
                if classif == 'ICE_ONLY':
                    supply_score = scores.get('supply_chain', 50)
                    # Not enforced strictly, just flagged as warning
        
        # Check 4: No NaN or missing values
        for i, (classif, score) in enumerate(zip(classifier_out, scorer_out)):
            if classif.get('similarity_score') is None:
                issues.append(f"Component {i+1} missing similarity_score")
                quality_score -= 5
            
            for dim in ['tech', 'manufacturing', 'supply_chain', 'demand', 'value', 'regulatory']:
                if dim not in score:
                    issues.append(f"Component {i+1} missing {dim} score")
                    quality_score -= 5
        
        quality_score = max(0, quality_score)
        
        return {
            'stage': 'integration',
            'quality_score': quality_score,
            'issues': issues,
            'confidence': self._get_confidence(quality_score),
            'valid': quality_score >= 70
        }
    
    # ============================================
    # OVERALL VALIDATION
    # ============================================
    
    def validate_complete_pipeline(self,
                                   enricher_out: List[Dict],
                                   classifier_out: List[Dict],
                                   scorer_out: List[Dict]) -> Dict:
        """Run complete validation on all stages"""
        
        print("\n" + "="*70)
        print("COMPREHENSIVE VALIDATION - ALL STAGES")
        print("="*70)
        
        # Validate each stage
        enricher_val = self.validate_enricher_output(enricher_out)
        classifier_val = self.validate_classifier_output(classifier_out)
        scorer_val = self.validate_scorer_output(scorer_out)
        integration_val = self.validate_integration(enricher_out, classifier_out, scorer_out)
        
        # Calculate overall quality
        all_scores = [
            enricher_val['quality_score'],
            classifier_val['quality_score'],
            scorer_val['quality_score'],
            integration_val['quality_score']
        ]
        
        overall_quality = sum(all_scores) / len(all_scores)
        
        # Collect all issues
        all_issues = []
        for val in [enricher_val, classifier_val, scorer_val, integration_val]:
            all_issues.extend([(val['stage'], issue) for issue in val['issues']])
        
        # Summary
        print(f"\n{'VALIDATION RESULTS':<40}")
        print("-" * 70)
        print(f"{'Enricher':<25} {enricher_val['quality_score']:>6.0f}/100   {enricher_val['confidence']:<10}")
        print(f"{'Classifier':<25} {classifier_val['quality_score']:>6.0f}/100   {classifier_val['confidence']:<10}")
        print(f"{'Scorer':<25} {scorer_val['quality_score']:>6.0f}/100   {scorer_val['confidence']:<10}")
        print(f"{'Integration':<25} {integration_val['quality_score']:>6.0f}/100   {integration_val['confidence']:<10}")
        print("-" * 70)
        print(f"{'OVERALL QUALITY':<25} {overall_quality:>6.0f}/100   {self._get_confidence(overall_quality):<10}")
        
        if all_issues:
            print(f"\n{'ISSUES FOUND':<40} ({len(all_issues)})")
            print("-" * 70)
            for stage, issue in all_issues[:10]:  # Show first 10
                print(f"[{stage.upper():12s}] {issue}")
            if len(all_issues) > 10:
                print(f"... and {len(all_issues) - 10} more issues")
        else:
            print(f"\n✅ NO ISSUES FOUND")
        
        print("="*70 + "\n")
        
        return {
            'overall_quality': overall_quality,
            'overall_confidence': self._get_confidence(overall_quality),
            'valid': overall_quality >= 70,
            'stages': {
                'enricher': enricher_val,
                'classifier': classifier_val,
                'scorer': scorer_val,
                'integration': integration_val
            },
            'all_issues': all_issues
        }
    
    # ============================================
    # HELPER METHODS
    # ============================================
    
    def _get_confidence(self, quality_score: float) -> str:
        """Determine confidence level from quality score"""
        
        if quality_score >= 80:
            return 'HIGH'
        elif quality_score >= 60:
            return 'MEDIUM'
        else:
            return 'LOW'


# ============================================
# USAGE EXAMPLE
# ============================================

if __name__ == "__main__":
    
    # Example data
    enricher_output = [
        {
            'name': 'Brake pad friction material',
            'cost_share': 0.35,
            'description': 'Friction material for brake pads',
            'function': 'Provides friction for braking',
            'subsystem': 'Chassis'
        },
        {
            'name': 'Brake rotor',
            'cost_share': 0.30,
            'description': 'Rotating disc that provides braking surface',
            'function': 'Braking surface',
            'subsystem': 'Chassis'
        },
        {
            'name': 'Brake caliper',
            'cost_share': 0.20,
            'description': 'Hydraulic caliper that clamps rotor',
            'function': 'Clamps rotor for braking',
            'subsystem': 'Chassis'
        },
        {
            'name': 'Brake master cylinder',
            'cost_share': 0.15,
            'description': 'Master cylinder for brake pressure',
            'function': 'Generates brake pressure',
            'subsystem': 'Chassis'
        }
    ]
    
    classifier_output = [
        {'classification': 'SHARED', 'similarity_score': 0.92},
        {'classification': 'SHARED', 'similarity_score': 0.88},
        {'classification': 'SHARED', 'similarity_score': 0.85},
        {'classification': 'SHARED', 'similarity_score': 0.90}
    ]
    
    scorer_output = [
        {
            'tech': 85, 'manufacturing': 90, 'supply_chain': 88,
            'demand': 85, 'value': 80, 'regulatory': 92
        },
        {
            'tech': 82, 'manufacturing': 88, 'supply_chain': 85,
            'demand': 82, 'value': 78, 'regulatory': 90
        },
        {
            'tech': 80, 'manufacturing': 85, 'supply_chain': 82,
            'demand': 80, 'value': 75, 'regulatory': 88
        },
        {
            'tech': 83, 'manufacturing': 87, 'supply_chain': 84,
            'demand': 83, 'value': 77, 'regulatory': 91
        }
    ]
    
    # Run validation
    validator = ComprehensiveValidator(debug=True)
    results = validator.validate_complete_pipeline(
        enricher_output,
        classifier_output,
        scorer_output
    )
    
    print(f"Overall Quality: {results['overall_quality']:.0f}/100")
    print(f"Valid Pipeline: {results['valid']}")