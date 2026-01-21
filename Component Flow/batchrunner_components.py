"""
batch_runner.py - Process HS codes from Excel, output results to Excel
Usage: python batch_runner.py --input input/hs_codes.xlsx --draw 1
"""

import pandas as pd
import argparse
from datetime import datetime
from workflow_integrator import WorkflowIntegrator


def get_timeline(tfs_score):
    """Calculate timeline from TFS score"""
    if tfs_score is None or tfs_score == 0:
        return "Unknown"
    if tfs_score >= 75:
        return "1-2 years"
    elif tfs_score >= 60:
        return "2-3 years"
    elif tfs_score >= 40:
        return "3-5 years"
    else:
        return "5+ years"


def run_batch(input_file: str, draw_number: int):
    """Run full pipeline on all HS codes in Excel"""
    
    print(f"\n{'='*60}")
    print(f"BATCH RUNNER - Draw #{draw_number}")
    print(f"Model: GPT-5 Mini")
    print(f"{'='*60}")
    
    # Read input
    df = pd.read_excel(input_file)
    print(f"[BATCH] Loaded {len(df)} HS codes from {input_file}")
    
    # Initialize
    integrator = WorkflowIntegrator(debug=True, max_retries=2)
    
    # Track timing
    start_time = datetime.now()
    
    # Process each row
    all_results = []
    
    for idx, row in df.iterrows():
        hs_code = str(row['hs_code_6d']).strip()
        description = str(row['full_description']).strip()
        
        print(f"\n{'─'*60}")
        print(f"[BATCH] Processing {idx+1}/{len(df)}: {hs_code} - {description}")
        print(f"{'─'*60}")
        
        # Reset integrator state
        integrator.errors = []
        integrator.warnings = []
        
        try:
            result = integrator.run_complete_analysis(hs_code, description)
            
            if 'stages' in result:
                enricher_out = result['stages']['enricher'].get('output', [])
                classifier_out = result['stages']['classifier'].get('output', [])
                scorer_out = result['stages']['scorer'].get('output', [])
                
                if not enricher_out:
                    raise ValueError("No components extracted")
                
                for i, comp in enumerate(enricher_out):
                    class_data = classifier_out[i] if i < len(classifier_out) else {}
                    score_data = scorer_out[i] if i < len(scorer_out) else {}
                    
                    scores = [
                        score_data.get('tech', 0),
                        score_data.get('manufacturing', 0),
                        score_data.get('supply_chain', 0),
                        score_data.get('demand', 0),
                        score_data.get('value', 0),
                        score_data.get('regulatory', 0)
                    ]
                    tfs = int(sum(scores) / 6) if all(s > 0 for s in scores) else 0
                    
                    all_results.append({
                        'HS_Code': hs_code,
                        'Description': description,
                        'Component': comp.get('name', ''),
                        'Function': comp.get('function', ''),
                        'Subsystem': comp.get('subsystem', ''),
                        'Classification': class_data.get('classification', ''),
                        'Similarity': class_data.get('similarity_score', 0),
                        'Tech': score_data.get('tech', 0),
                        'Manufacturing': score_data.get('manufacturing', 0),
                        'Supply_Chain': score_data.get('supply_chain', 0),
                        'Demand': score_data.get('demand', 0),
                        'Value': score_data.get('value', 0),
                        'Regulatory': score_data.get('regulatory', 0),
                        'TFS_Score': tfs,
                        'Timeline': get_timeline(tfs),
                        'Status': 'SUCCESS'
                    })
                    print(f"    ✓ {comp.get('name')}: {class_data.get('classification', '?')} | TFS={tfs}")
            else:
                raise ValueError(result.get('error', 'Unknown error'))
                
        except Exception as e:
            print(f"    ✗ Error: {e}")
            all_results.append({
                'HS_Code': hs_code,
                'Description': description,
                'Component': 'ERROR',
                'Function': '',
                'Subsystem': '',
                'Classification': '',
                'Similarity': 0,
                'Tech': 0,
                'Manufacturing': 0,
                'Supply_Chain': 0,
                'Demand': 0,
                'Value': 0,
                'Regulatory': 0,
                'TFS_Score': 0,
                'Timeline': '',
                'Status': 'FAILED',
                'Error': str(e)
            })
    
    # Calculate elapsed time
    elapsed = datetime.now() - start_time
    
    # Save to Excel
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"output/results_draw_{draw_number:02d}_{timestamp}.xlsx"
    
    pd.DataFrame(all_results).to_excel(output_file, index=False)
    
    # Summary
    success = len([r for r in all_results if r.get('Status') == 'SUCCESS'])
    failed = len([r for r in all_results if r.get('Status') != 'SUCCESS'])
    
    print(f"\n{'='*60}")
    print(f"BATCH COMPLETE")
    print(f"{'='*60}")
    print(f"Output file: {output_file}")
    print(f"Total components: {len(all_results)}")
    print(f"Success: {success} | Failed: {failed}")
    print(f"Time elapsed: {elapsed}")
    print(f"{'='*60}\n")
    
    return output_file


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run ICE-EV analysis batch')
    parser.add_argument('--input', required=True, help='Input Excel file path')
    parser.add_argument('--draw', type=int, default=1, help='Draw number (1, 2, 3...)')
    args = parser.parse_args()
    
    run_batch(args.input, args.draw)