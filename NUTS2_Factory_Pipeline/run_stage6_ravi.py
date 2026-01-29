"""
run_stage6_ravi.py - Calculate Regional Automotive Vulnerability Index

This script integrates with your existing Stage 3, 4, 5 pipeline:
- Reads Stage 3 outputs (components with ICE/EV/Shared classification)
- Reads Stage 4 outputs (employment estimates)
- Applies TFS and ICE dependency from category_metrics.py
- Calculates RAVI for each NUTS-2 region

Usage: python run_stage6_ravi.py
"""

import json
import os
from collections import defaultdict
from datetime import date

# Import the category metrics bridge
from category_metrics import get_plant_metrics, get_component_tfs, get_component_ice_dependency

# ============================================================
# CONFIGURATION
# ============================================================

STAGE3_FOLDER = "prompt_iterations/stage3_v2_outputs"
STAGE4_FOLDER = "prompt_iterations/stage4_v1_outputs"
OUTPUT_FOLDER = "results"

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Employment size class midpoints (same as Stage 5)
SIZE_CLASS_MIDPOINTS = {
    "Small": 250,
    "Medium": 1250,
    "Large": 3500,
    "Very Large": 7500,
    "Uncertain": 1250
}

# R&D Expenditure as % of GDP (Source: Eurostat rd_e_gerdreg)
RD_EXPENDITURE_PCT = {
    "DE11": 5.6,   # Stuttgart
    "DE12": 3.1,   # Karlsruhe
    "DE13": 2.0,   # Freiburg
    "DE14": 4.2,   # Tübingen
    "DE21": 3.4,   # Oberbayern
    "DE22": 1.5,   # Niederbayern
    "DE23": 1.8,   # Oberpfalz
    "DE24": 1.6,   # Oberfranken
    "DE25": 2.8,   # Mittelfranken
    "DE26": 1.9,   # Unterfranken
    "DE27": 2.1,   # Schwaben
    "DE30": 3.5,   # Berlin
    "DE40": 1.4,   # Brandenburg
    "DE50": 2.8,   # Bremen
    "DE60": 2.2,   # Hamburg
    "DE71": 2.9,   # Darmstadt
    "DE72": 1.5,   # Gießen
    "DE73": 1.6,   # Kassel
    "DE80": 1.3,   # Mecklenburg-Vorpommern
    "DE91": 2.8,   # Braunschweig
    "DE92": 2.2,   # Hannover
    "DE93": 1.2,   # Lüneburg
    "DE94": 1.4,   # Weser-Ems
    "DEA1": 1.8,   # Düsseldorf
    "DEA2": 2.0,   # Köln
    "DEA3": 1.3,   # Münster
    "DEA4": 1.5,   # Detmold
    "DEA5": 1.4,   # Arnsberg
    "DEB1": 1.5,   # Koblenz
    "DEB2": 1.1,   # Trier
    "DEB3": 1.6,   # Rheinhessen-Pfalz
    "DEC0": 1.2,   # Saarland
    "DED2": 2.5,   # Dresden
    "DED4": 1.8,   # Chemnitz
    "DED5": 2.4,   # Leipzig
    "DEE0": 1.4,   # Sachsen-Anhalt
    "DEF0": 1.5,   # Schleswig-Holstein
    "DEG0": 1.9,   # Thüringen
}

# Total Manufacturing Employment (Source: Eurostat nama_10r_3empers)
MANUFACTURING_EMPLOYMENT = {
    "DE11": 520000,
    "DE12": 180000,
    "DE13": 120000,
    "DE14": 130000,
    "DE21": 420000,
    "DE22": 110000,
    "DE23": 90000,
    "DE24": 85000,
    "DE25": 140000,
    "DE26": 95000,
    "DE27": 160000,
    "DE30": 110000,
    "DE40": 65000,
    "DE50": 55000,
    "DE60": 75000,
    "DE71": 280000,
    "DE72": 55000,
    "DE73": 80000,
    "DE80": 45000,
    "DE91": 200000,
    "DE92": 180000,
    "DE93": 55000,
    "DE94": 110000,
    "DEA1": 250000,
    "DEA2": 300000,
    "DEA3": 85000,
    "DEA4": 140000,
    "DEA5": 220000,
    "DEB1": 70000,
    "DEB2": 35000,
    "DEB3": 130000,
    "DEC0": 95000,
    "DED2": 120000,
    "DED4": 95000,
    "DED5": 75000,
    "DEE0": 85000,
    "DEF0": 95000,
    "DEG0": 110000,
}

# NUTS-2 region names
NUTS2_NAMES = {
    "DE11": "Stuttgart",
    "DE12": "Karlsruhe",
    "DE13": "Freiburg",
    "DE14": "Tübingen",
    "DE21": "Oberbayern",
    "DE22": "Niederbayern",
    "DE23": "Oberpfalz",
    "DE24": "Oberfranken",
    "DE25": "Mittelfranken",
    "DE26": "Unterfranken",
    "DE27": "Schwaben",
    "DE30": "Berlin",
    "DE40": "Brandenburg",
    "DE50": "Bremen",
    "DE60": "Hamburg",
    "DE71": "Darmstadt",
    "DE72": "Gießen",
    "DE73": "Kassel",
    "DE80": "Mecklenburg-Vorpommern",
    "DE91": "Braunschweig",
    "DE92": "Hannover",
    "DE93": "Lüneburg",
    "DE94": "Weser-Ems",
    "DEA1": "Düsseldorf",
    "DEA2": "Köln",
    "DEA3": "Münster",
    "DEA4": "Detmold",
    "DEA5": "Arnsberg",
    "DEB1": "Koblenz",
    "DEB2": "Trier",
    "DEB3": "Rheinhessen-Pfalz",
    "DEC0": "Saarland",
    "DED2": "Dresden",
    "DED4": "Chemnitz",
    "DED5": "Leipzig",
    "DEE0": "Sachsen-Anhalt",
    "DEF0": "Schleswig-Holstein",
    "DEG0": "Thüringen",
}


# ============================================================
# LOAD STAGE 3 AND STAGE 4 DATA
# ============================================================

def load_plant_data():
    """
    Load and merge Stage 3 (components) and Stage 4 (employment) data.
    
    Returns:
        List of plant dicts with components, employment, TFS, and ICE dependency
    """
    
    plants = []
    
    # Build lookup from Stage 3 (components)
    stage3_data = {}
    if os.path.exists(STAGE3_FOLDER):
        for filename in os.listdir(STAGE3_FOLDER):
            if not filename.endswith(".json"):
                continue
            
            filepath = os.path.join(STAGE3_FOLDER, filename)
            with open(filepath, "r") as f:
                data = json.load(f)
            
            # Skip non-production sites
            if not data.get("is_production_site", False):
                continue
            
            key = f"{data.get('company', '')}_{data.get('plant', '')}_{data.get('nuts2_code', '')}"
            stage3_data[key] = data
    
    # Load Stage 4 (employment) and merge
    if os.path.exists(STAGE4_FOLDER):
        for filename in os.listdir(STAGE4_FOLDER):
            if not filename.endswith(".json"):
                continue
            
            filepath = os.path.join(STAGE4_FOLDER, filename)
            with open(filepath, "r") as f:
                data = json.load(f)
            
            company = data.get("company", "")
            plant_name = data.get("plant", "")
            nuts2_code = data.get("nuts2_code", "")
            
            key = f"{company}_{plant_name}_{nuts2_code}"
            
            # Get employment
            employment_data = data.get("employment", {})
            size_class = employment_data.get("size_class", "Medium")
            
            if size_class not in SIZE_CLASS_MIDPOINTS:
                size_class = "Medium"
            
            employment = employment_data.get("estimate")
            if employment is None:
                employment = SIZE_CLASS_MIDPOINTS[size_class]
            
            # Get components from Stage 3
            stage3 = stage3_data.get(key, {})
            components = stage3.get("components", [])
            
            # Calculate plant-level TFS and ICE dependency
            metrics = get_plant_metrics(components)
            
            plants.append({
                "company": company,
                "plant": plant_name,
                "city": data.get("city", ""),
                "nuts2_code": nuts2_code,
                "nuts2_name": NUTS2_NAMES.get(nuts2_code, ""),
                "employment": employment,
                "size_class": size_class,
                "employment_confidence": employment_data.get("confidence", "medium"),
                "plant_tfs": metrics["plant_tfs"],
                "plant_ice_dependency": metrics["plant_ice_dependency"],
                "component_count": metrics["component_count"],
                "ice_count": metrics["ice_count"],
                "ev_count": metrics["ev_count"],
                "shared_count": metrics["shared_count"],
                "components": components
            })
    
    return plants


# ============================================================
# REGIONAL AGGREGATION
# ============================================================

def aggregate_to_regions(plants: list) -> dict:
    """
    Aggregate plant-level data to NUTS-2 regions.
    
    Returns:
        Dict of nuts2_code -> regional metrics
    """
    
    regions = defaultdict(lambda: {
        "plants": [],
        "total_employment": 0,
        "weighted_tfs_sum": 0,
        "weighted_ice_dep_sum": 0,
        "ice_plants": 0,
        "ev_plants": 0,
        "mixed_plants": 0
    })
    
    for plant in plants:
        nuts2 = plant["nuts2_code"]
        emp = plant["employment"]
        
        regions[nuts2]["plants"].append(plant)
        regions[nuts2]["total_employment"] += emp
        regions[nuts2]["weighted_tfs_sum"] += plant["plant_tfs"] * emp
        regions[nuts2]["weighted_ice_dep_sum"] += plant["plant_ice_dependency"] * emp
        
        # Categorize plant by dominant type
        if plant["ice_count"] > plant["ev_count"] + plant["shared_count"]:
            regions[nuts2]["ice_plants"] += 1
        elif plant["ev_count"] > plant["ice_count"] + plant["shared_count"]:
            regions[nuts2]["ev_plants"] += 1
        else:
            regions[nuts2]["mixed_plants"] += 1
    
    # Calculate weighted averages
    result = {}
    for nuts2, data in regions.items():
        total_emp = data["total_employment"]
        
        if total_emp > 0:
            weighted_tfs = data["weighted_tfs_sum"] / total_emp
            weighted_ice_dep = data["weighted_ice_dep_sum"] / total_emp
        else:
            weighted_tfs = 55
            weighted_ice_dep = 0.5
        
        result[nuts2] = {
            "nuts2_code": nuts2,
            "nuts2_name": NUTS2_NAMES.get(nuts2, ""),
            "plant_count": len(data["plants"]),
            "total_employment": total_emp,
            "weighted_tfs": round(weighted_tfs, 1),
            "weighted_ice_dependency": round(weighted_ice_dep, 3),
            "ice_plants": data["ice_plants"],
            "ev_plants": data["ev_plants"],
            "mixed_plants": data["mixed_plants"]
        }
    
    return result


# ============================================================
# RAVI CALCULATION
# ============================================================

def calculate_ravi(regional_data: dict) -> list:
    """
    Calculate RAVI for each region.
    
    RAVI = Exposure × (1 - Adaptive_Capacity)
    
    Returns:
        List of region dicts with RAVI scores
    """
    
    results = []
    
    for nuts2, data in regional_data.items():
        # Get external data
        rd_pct = RD_EXPENDITURE_PCT.get(nuts2, 2.0)
        mfg_employment = MANUFACTURING_EMPLOYMENT.get(nuts2, 150000)
        
        # ============================================
        # EXPOSURE
        # ============================================
        
        # Auto employment share of manufacturing (capped at 60%)
        auto_share = min(data["total_employment"] / mfg_employment, 0.6)
        
        # Exposure = share × ICE dependency
        exposure = auto_share * data["weighted_ice_dependency"]
        
        # ============================================
        # ADAPTIVE CAPACITY
        # ============================================
        
        # Innovation Potential (R&D vs EU 3% target)
        innovation_potential = min(rd_pct / 3.0, 1.0)
        
        # Industrial Future Assets (inverse of ICE dependency)
        future_assets = 1 - data["weighted_ice_dependency"]
        
        # Transition Score (TFS normalized to 0-1)
        transition_score = data["weighted_tfs"] / 100
        
        # Industrial Readiness = 0.6 × Future Assets + 0.4 × Transition Score
        industrial_readiness = 0.6 * future_assets + 0.4 * transition_score
        
        # Adaptive Capacity = 0.5 × Innovation + 0.5 × Readiness
        adaptive_capacity = 0.5 * innovation_potential + 0.5 * industrial_readiness
        
        # ============================================
        # RAVI
        # ============================================
        
        ravi_raw = exposure * (1 - adaptive_capacity)
        
        results.append({
            "nuts2_code": nuts2,
            "nuts2_name": data["nuts2_name"],
            "plant_count": data["plant_count"],
            "total_employment": data["total_employment"],
            "weighted_tfs": data["weighted_tfs"],
            "weighted_ice_dependency": data["weighted_ice_dependency"],
            "ice_plants": data["ice_plants"],
            "ev_plants": data["ev_plants"],
            "mixed_plants": data["mixed_plants"],
            "auto_employment_share": round(auto_share, 3),
            "exposure": round(exposure, 4),
            "rd_expenditure_pct": rd_pct,
            "innovation_potential": round(innovation_potential, 3),
            "future_assets": round(future_assets, 3),
            "transition_score": round(transition_score, 3),
            "industrial_readiness": round(industrial_readiness, 3),
            "adaptive_capacity": round(adaptive_capacity, 3),
            "ravi_raw": round(ravi_raw, 4)
        })
    
    # Normalize RAVI to 0-100 scale
    if results:
        ravi_values = [r["ravi_raw"] for r in results]
        min_ravi = min(ravi_values)
        max_ravi = max(ravi_values)
        
        if max_ravi > min_ravi:
            for r in results:
                r["ravi_score"] = round((r["ravi_raw"] - min_ravi) / (max_ravi - min_ravi) * 100, 1)
        else:
            for r in results:
                r["ravi_score"] = 50.0
        
        # Add rank (1 = most vulnerable)
        results.sort(key=lambda x: x["ravi_score"], reverse=True)
        for i, r in enumerate(results, 1):
            r["vulnerability_rank"] = i
            
            # Add category
            if r["ravi_score"] >= 66:
                r["vulnerability_category"] = "High"
            elif r["ravi_score"] >= 33:
                r["vulnerability_category"] = "Medium"
            else:
                r["vulnerability_category"] = "Low"
    
    return results


# ============================================================
# MAIN EXECUTION
# ============================================================

def main():
    print("=" * 60)
    print("STAGE 6: RAVI CALCULATION")
    print("=" * 60)
    
    # Load plant data from Stage 3 and 4
    print("\n[1] Loading plant data from Stage 3 and 4...")
    plants = load_plant_data()
    print(f"    Loaded {len(plants)} production plants")
    
    if not plants:
        print("\n⚠️  No plant data found!")
        print("    Make sure Stage 3 and 4 have been run first.")
        print("    Expected folders:")
        print(f"    - {STAGE3_FOLDER}")
        print(f"    - {STAGE4_FOLDER}")
        return
    
    # Aggregate to regions
    print("\n[2] Aggregating to NUTS-2 regions...")
    regional_data = aggregate_to_regions(plants)
    print(f"    Found data for {len(regional_data)} regions")
    
    # Calculate RAVI
    print("\n[3] Calculating RAVI...")
    ravi_results = calculate_ravi(regional_data)
    
    # Save plant-level results
    plants_file = os.path.join(OUTPUT_FOLDER, f"stage6_plants_{date.today()}.json")
    with open(plants_file, "w") as f:
        json.dump(plants, f, indent=2)
    print(f"\n[4] Saved plant-level data: {plants_file}")
    
    # Save RAVI results
    ravi_file = os.path.join(OUTPUT_FOLDER, f"stage6_ravi_{date.today()}.json")
    output = {
        "version": "stage6_ravi_v1",
        "date": str(date.today()),
        "methodology": {
            "ravi_formula": "RAVI = Exposure × (1 - Adaptive_Capacity)",
            "exposure": "(Auto_Employment / Mfg_Employment) × ICE_Dependency",
            "adaptive_capacity": "0.5 × Innovation_Potential + 0.5 × Industrial_Readiness",
            "innovation_potential": "min(R&D_pct / 3.0, 1.0)",
            "industrial_readiness": "0.6 × Future_Assets + 0.4 × Transition_Score"
        },
        "summary": {
            "regions_analyzed": len(ravi_results),
            "total_plants": len(plants),
            "total_employment": sum(r["total_employment"] for r in ravi_results)
        },
        "regions": ravi_results
    }
    
    with open(ravi_file, "w") as f:
        json.dump(output, f, indent=2)
    print(f"    Saved RAVI results: {ravi_file}")
    
    # ============================================================
    # DISPLAY RESULTS
    # ============================================================
    
    print("\n" + "=" * 60)
    print("RAVI RESULTS (Ranked by Vulnerability)")
    print("=" * 60)
    
    print(f"\n{'Rank':<5} {'Region':<22} {'Emp':>8} {'ICE_Dep':>8} {'TFS':>5} {'RAVI':>6} {'Cat':<8}")
    print("-" * 75)
    
    for r in ravi_results:
        print(f"{r['vulnerability_rank']:<5} "
              f"{r['nuts2_name'][:20]:<22} "
              f"{r['total_employment']:>8,} "
              f"{r['weighted_ice_dependency']:>8.2f} "
              f"{r['weighted_tfs']:>5.1f} "
              f"{r['ravi_score']:>6.1f} "
              f"{r['vulnerability_category']:<8}")
    
    # Summary statistics
    print("\n" + "-" * 60)
    print("SUMMARY")
    print("-" * 60)
    
    high_count = sum(1 for r in ravi_results if r["vulnerability_category"] == "High")
    med_count = sum(1 for r in ravi_results if r["vulnerability_category"] == "Medium")
    low_count = sum(1 for r in ravi_results if r["vulnerability_category"] == "Low")
    
    print(f"Vulnerability Distribution: High={high_count}, Medium={med_count}, Low={low_count}")
    
    print("\nMost Vulnerable (Top 3):")
    for r in ravi_results[:3]:
        print(f"  {r['vulnerability_rank']}. {r['nuts2_name']}: RAVI={r['ravi_score']:.1f}")
    
    print("\nLeast Vulnerable (Bottom 3):")
    for r in ravi_results[-3:]:
        print(f"  {r['vulnerability_rank']}. {r['nuts2_name']}: RAVI={r['ravi_score']:.1f}")
    
    print("\n" + "=" * 60)
    print("STAGE 6 COMPLETE")
    print("=" * 60 + "\n")
    
    return ravi_results


if __name__ == "__main__":
    main()