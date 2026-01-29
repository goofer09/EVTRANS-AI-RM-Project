"""
run_stage5_validation.py - Regional Aggregation and Validation
Rule-based (no LLM calls) - validates against Eurostat benchmarks

Usage: python run_stage5_validation.py
"""

import json
import os
from collections import defaultdict
from datetime import date

# ============================================================
# CONFIGURATION
# ============================================================

STAGE4_INPUT_DIR = "prompt_iterations/stage4_v1_outputs"
OUTPUT_DIR = "results"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Employment size class midpoints
SIZE_CLASS_MIDPOINTS = {
    "Small": 250,
    "Medium": 1250,
    "Large": 3500,
    "Very Large": 7500,
    "Uncertain": 1250
}

# Eurostat automotive employment benchmarks (approximate)
# Source: Eurostat nama_10r_3empers, NACE C29
EUROSTAT_AUTO_EMPLOYMENT = {
    "DE11": 185000,  # Stuttgart
    "DE12": 45000,   # Karlsruhe
    "DE14": 35000,   # Tübingen
    "DE21": 120000,  # Oberbayern
    "DE22": 45000,   # Niederbayern
    "DE27": 50000,   # Schwaben
    "DE30": 15000,   # Berlin
    "DE71": 65000,   # Darmstadt
    "DE91": 95000,   # Braunschweig
    "DE92": 55000,   # Hannover
    "DEA1": 35000,   # Düsseldorf
    "DEA2": 50000,   # Köln
    "DEA5": 40000,   # Arnsberg
    "DEC0": 25000,   # Saarland
    "DED2": 20000,   # Dresden
}

# NUTS-2 region names
NUTS2_NAMES = {
    "DE11": "Stuttgart", "DE12": "Karlsruhe", "DE13": "Freiburg", "DE14": "Tübingen",
    "DE21": "Oberbayern", "DE22": "Niederbayern", "DE23": "Oberpfalz", "DE24": "Oberfranken",
    "DE25": "Mittelfranken", "DE26": "Unterfranken", "DE27": "Schwaben",
    "DE30": "Berlin", "DE40": "Brandenburg", "DE50": "Bremen", "DE60": "Hamburg",
    "DE71": "Darmstadt", "DE72": "Gießen", "DE73": "Kassel",
    "DE80": "Mecklenburg-Vorpommern",
    "DE91": "Braunschweig", "DE92": "Hannover", "DE93": "Lüneburg", "DE94": "Weser-Ems",
    "DEA1": "Düsseldorf", "DEA2": "Köln", "DEA3": "Münster", "DEA4": "Detmold", "DEA5": "Arnsberg",
    "DEB1": "Koblenz", "DEB2": "Trier", "DEB3": "Rheinhessen-Pfalz",
    "DEC0": "Saarland",
    "DED2": "Dresden", "DED4": "Chemnitz", "DED5": "Leipzig",
    "DEE0": "Sachsen-Anhalt", "DEF0": "Schleswig-Holstein", "DEG0": "Thüringen",
}


# ============================================================
# MAIN FUNCTION
# ============================================================

def run_stage5():
    """
    Aggregate employment estimates and validate against Eurostat.
    """
    
    print("=" * 60)
    print("STAGE 5: Regional Aggregation & Validation")
    print(f"Input: {STAGE4_INPUT_DIR}")
    print("=" * 60)
    
    if not os.path.exists(STAGE4_INPUT_DIR):
        print(f"ERROR: Stage 4 output directory not found: {STAGE4_INPUT_DIR}")
        print("Run Stage 4 first: python run_stage4_openai.py")
        return None
    
    # Aggregate by region
    region_data = defaultdict(lambda: {
        "plants": [],
        "employment_sum": 0,
        "uncertain_count": 0
    })
    
    for filename in os.listdir(STAGE4_INPUT_DIR):
        if not filename.endswith(".json"):
            continue
        
        filepath = os.path.join(STAGE4_INPUT_DIR, filename)
        with open(filepath, "r") as f:
            data = json.load(f)
        
        nuts2 = data.get("nuts2_code", "")
        employment = data.get("employment", {})
        size_class = employment.get("size_class", "Medium")
        
        # Get employment estimate
        estimate = employment.get("estimate")
        if estimate is None:
            if size_class in SIZE_CLASS_MIDPOINTS:
                estimate = SIZE_CLASS_MIDPOINTS[size_class]
            else:
                estimate = SIZE_CLASS_MIDPOINTS["Medium"]
                region_data[nuts2]["uncertain_count"] += 1
        
        region_data[nuts2]["plants"].append({
            "company": data.get("company"),
            "plant": data.get("plant"),
            "employment": estimate,
            "size_class": size_class
        })
        region_data[nuts2]["employment_sum"] += estimate
    
    # Build validation summary
    results = []
    
    for nuts2, data in region_data.items():
        llm_sum = data["employment_sum"]
        eurostat = EUROSTAT_AUTO_EMPLOYMENT.get(nuts2)
        
        if eurostat is None:
            deviation = None
            status = "NO_BASELINE"
        else:
            deviation = (llm_sum - eurostat) / eurostat
            if abs(deviation) <= 0.30:
                status = "PASS"
            elif abs(deviation) <= 0.50:
                status = "WARNING"
            else:
                status = "FLAG"
        
        results.append({
            "nuts2_code": nuts2,
            "nuts2_name": NUTS2_NAMES.get(nuts2, ""),
            "plant_count": len(data["plants"]),
            "llm_employment_sum": llm_sum,
            "eurostat_employment": eurostat,
            "deviation": round(deviation, 3) if deviation else None,
            "deviation_pct": f"{deviation*100:.1f}%" if deviation else "N/A",
            "validation_status": status,
            "uncertain_plants": data["uncertain_count"]
        })
    
    # Sort by employment
    results.sort(key=lambda x: x["llm_employment_sum"], reverse=True)
    
    # Save results
    output = {
        "version": "stage5_v1_openai",
        "date": str(date.today()),
        "summary": {
            "regions_analyzed": len(results),
            "total_plants": sum(r["plant_count"] for r in results),
            "total_llm_employment": sum(r["llm_employment_sum"] for r in results),
            "pass_count": sum(1 for r in results if r["validation_status"] == "PASS"),
            "warning_count": sum(1 for r in results if r["validation_status"] == "WARNING"),
            "flag_count": sum(1 for r in results if r["validation_status"] == "FLAG"),
            "no_baseline_count": sum(1 for r in results if r["validation_status"] == "NO_BASELINE")
        },
        "regions": results
    }
    
    out_file = os.path.join(OUTPUT_DIR, f"stage5_validation_{date.today()}.json")
    with open(out_file, "w") as f:
        json.dump(output, f, indent=2)
    
    # Display results
    print(f"\n{'Region':<25} {'Plants':>6} {'LLM Emp':>10} {'Eurostat':>10} {'Dev':>8} {'Status':<10}")
    print("-" * 75)
    
    for r in results:
        eurostat_str = f"{r['eurostat_employment']:,}" if r['eurostat_employment'] else "N/A"
        print(f"{r['nuts2_name'][:24]:<25} {r['plant_count']:>6} {r['llm_employment_sum']:>10,} "
              f"{eurostat_str:>10} {r['deviation_pct']:>8} {r['validation_status']:<10}")
    
    print("\n" + "=" * 60)
    print("STAGE 5 COMPLETE")
    print(f"Output: {out_file}")
    print("=" * 60 + "\n")
    
    return output


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    run_stage5()