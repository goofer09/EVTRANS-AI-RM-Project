"""
run_all_stages.py - Master batch runner for complete NUTS-2 analysis pipeline

Orchestrates Stages 1-6:
  Stage 1: NUTS-2 → Companies (OpenAI GPT-5 Mini)
  Stage 2: Company → Plants (OpenAI GPT-5 Mini)
  Stage 3: Plant → Components ICE/EV/Shared (OpenAI GPT-5 Mini)
  Stage 4: Plant → Employment (OpenAI GPT-5 Mini)
  Stage 5: Regional Validation (Rule-based)
  Stage 6: RAVI Calculation (Rule-based)

Usage:
  python run_all_stages.py --test      # 3 test regions
  python run_all_stages.py --priority  # 15 priority regions
  python run_all_stages.py --all       # All 38 German NUTS-2 regions
  python run_all_stages.py --custom DE11,DE21,DE94  # Custom NUTS-2 codes
  python run_all_stages.py --from 3    # Resume from Stage 3
"""

import argparse
import os
from datetime import datetime

# Import stage runners
from run_stage1_openai import run_batch as run_stage1_batch, TEST_REGIONS, PRIORITY_REGIONS, ALL_REGIONS, REMAINING_REGIONS
from run_stage2_openai import run_stage2
from run_stage3_openai import run_stage3
from run_stage4_openai import run_stage4
from run_stage5_validation import run_stage5
from run_stage6_ravi import main as run_stage6


# ============================================================
# MASTER ORCHESTRATOR
# ============================================================

def run_pipeline(regions: dict, start_from: int = 1):
    """
    Run the complete pipeline from Stage 1 (or specified stage) to Stage 6.
    """
    
    print("\n" + "=" * 70)
    print("   NUTS-2 REGIONAL AUTOMOTIVE VULNERABILITY PIPELINE")
    print("   OpenAI GPT-5 Mini")
    print("=" * 70)
    print(f"\nRegions selected: {len(regions)}")
    print(f"Starting from: Stage {start_from}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    stage_times = {}
    
    # ========================================
    # STAGE 1: NUTS-2 → Companies
    # ========================================
    if start_from <= 1:
        print("\n" + "▶" * 35)
        print("▶ STAGE 1: Identifying companies in NUTS-2 regions")
        print("▶" * 35)
        
        start = datetime.now()
        run_stage1_batch(regions)
        stage_times["Stage 1"] = datetime.now() - start
        print(f"\n⏱ Stage 1 completed in {stage_times['Stage 1']}")
    else:
        print("\n⏭ Skipping Stage 1 (--from > 1)")
    
    # ========================================
    # STAGE 2: Company → Plants
    # ========================================
    if start_from <= 2:
        print("\n" + "▶" * 35)
        print("▶ STAGE 2: Identifying plants for each company")
        print("▶" * 35)
        
        start = datetime.now()
        run_stage2(regions_filter=set(regions.keys()))
        stage_times["Stage 2"] = datetime.now() - start
        print(f"\n⏱ Stage 2 completed in {stage_times['Stage 2']}")
    else:
        print("\n⏭ Skipping Stage 2 (--from > 2)")
    
    # ========================================
    # STAGE 3: Plant → Components (ICE/EV/Shared)
    # ========================================
    if start_from <= 3:
        print("\n" + "▶" * 35)
        print("▶ STAGE 3: Classifying plant components (ICE/EV/Shared)")
        print("▶" * 35)
        
        start = datetime.now()
        run_stage3(regions_filter=set(regions.keys()))
        stage_times["Stage 3"] = datetime.now() - start
        print(f"\n⏱ Stage 3 completed in {stage_times['Stage 3']}")
    else:
        print("\n⏭ Skipping Stage 3 (--from > 3)")
    
    # ========================================
    # STAGE 4: Plant → Employment
    # ========================================
    if start_from <= 4:
        print("\n" + "▶" * 35)
        print("▶ STAGE 4: Estimating plant employment")
        print("▶" * 35)
        
        start = datetime.now()
        run_stage4(regions_filter=set(regions.keys()))
        stage_times["Stage 4"] = datetime.now() - start
        print(f"\n⏱ Stage 4 completed in {stage_times['Stage 4']}")
    else:
        print("\n⏭ Skipping Stage 4 (--from > 4)")
    
    # ========================================
    # STAGE 5: Regional Validation
    # ========================================
    if start_from <= 5:
        print("\n" + "▶" * 35)
        print("▶ STAGE 5: Regional aggregation & Eurostat validation")
        print("▶" * 35)
        
        start = datetime.now()
        run_stage5()
        stage_times["Stage 5"] = datetime.now() - start
        print(f"\n⏱ Stage 5 completed in {stage_times['Stage 5']}")
    else:
        print("\n⏭ Skipping Stage 5 (--from > 5)")
    
    # ========================================
    # STAGE 6: RAVI Calculation
    # ========================================
    if start_from <= 6:
        print("\n" + "▶" * 35)
        print("▶ STAGE 6: Calculating Regional Automotive Vulnerability Index (RAVI)")
        print("▶" * 35)
        
        start = datetime.now()
        run_stage6()
        stage_times["Stage 6"] = datetime.now() - start
        print(f"\n⏱ Stage 6 completed in {stage_times['Stage 6']}")
    
    # ========================================
    # SUMMARY
    # ========================================
    total_time = sum(stage_times.values(), datetime.now() - datetime.now())
    for t in stage_times.values():
        total_time += t
    
    print("\n" + "=" * 70)
    print("   PIPELINE COMPLETE")
    print("=" * 70)
    print(f"\nFinished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\nStage Timing:")
    for stage, time in stage_times.items():
        print(f"  {stage}: {time}")
    print(f"\nTotal Time: {sum((t.total_seconds() for t in stage_times.values()))/60:.1f} minutes")
    
    print(f"\nOutput Files:")
    print("  prompt_iterations/stage1_v1_outputs/  - Companies per region")
    print("  prompt_iterations/stage2_v1_outputs/  - Plants per company")
    print("  prompt_iterations/stage3_v2_outputs/  - Components per plant")
    print("  prompt_iterations/stage4_v1_outputs/  - Employment per plant")
    print("  results/stage5_validation_*.json      - Eurostat validation")
    print("  results/stage6_ravi_*.json            - RAVI scores")
    print("  results/stage6_plants_*.json          - Plant-level aggregated data")
    
    print("\n" + "=" * 70 + "\n")


# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Run complete NUTS-2 regional analysis pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_all_stages.py --test           # Quick test with 3 regions
  python run_all_stages.py --priority       # 15 automotive-heavy regions
  python run_all_stages.py --all            # All 38 German NUTS-2 regions
  python run_all_stages.py --custom DE11,DE21,DE94  # Custom NUTS-2 codes
  python run_all_stages.py --from 3         # Resume from Stage 3
  python run_all_stages.py --from 5         # Just run validation & RAVI
        """
    )

    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        '--test',
        action='store_true',
        help='Test with 3 regions (Stuttgart, Oberbayern, Braunschweig)',
    )
    group.add_argument(
        '--priority',
        action='store_true',
        help='Priority automotive regions (15 regions)',
    )
    group.add_argument(
        '--all',
        action='store_true',
        help='All 38 German NUTS-2 regions',
    )
    group.add_argument(
        '--remaining',
        action='store_true',
        help='Remaining unprocessed regions (23 regions)',
    )
    group.add_argument(
        '--custom',
        type=str,
        help='Comma-separated NUTS-2 codes (e.g., DE11,DE21,DE94)',
    )

    parser.add_argument(
        '--from',
        dest='start_from',
        type=int,
        default=1,
        help='Start from stage N (1-6). Use to resume failed runs.',
    )

    args = parser.parse_args()

    # Select regions
    if args.custom:
        custom_codes = [code.strip().upper() for code in args.custom.split(",") if code.strip()]
        regions = {code: ALL_REGIONS[code] for code in custom_codes if code in ALL_REGIONS}
        missing = sorted(set(custom_codes) - set(regions.keys()))
        if missing:
            print(f"WARNING: Unknown region codes ignored: {', '.join(missing)}")
    elif args.all:
        regions = ALL_REGIONS


    
    # Create output directories
    os.makedirs("prompt_iterations/stage1_v1_outputs", exist_ok=True)
    os.makedirs("prompt_iterations/stage2_v1_outputs", exist_ok=True)
    os.makedirs("prompt_iterations/stage3_v2_outputs", exist_ok=True)
    os.makedirs("prompt_iterations/stage4_v1_outputs", exist_ok=True)
    os.makedirs("results", exist_ok=True)
    
    # Run pipeline
    run_pipeline(regions, start_from=args.start_from)
