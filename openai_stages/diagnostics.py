from __future__ import annotations

import json
import os
from glob import glob
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd


# ---- adjust if your folders differ ----
STAGE3_DIR = "prompt_iterations/stage3_v2_outputs"
STAGE4_DIR = "prompt_iterations/stage4_v1_outputs"
RESULTS_DIR = "results"
OUT_XLSX = os.path.join(RESULTS_DIR, "unified_outputs.xlsx")


def read_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def latest_file(pattern: str) -> Optional[str]:
    """
    Returns the file with the latest date in the filename.
    Assumes filenames contain dates like: stage6_plants_2026-01-22.json
    """
    files = glob(pattern)
    if not files:
        return None
    # Sort by filename (which contains the date) rather than modification time
    sorted_files = sorted(files, key=lambda f: os.path.basename(f))
    print(f"   Found files matching pattern '{os.path.basename(pattern)}':")
    for f in sorted_files:
        print(f"      - {os.path.basename(f)}")
    selected = sorted_files[-1]  # max = last after sorting
    print(f"   → Selected: {os.path.basename(selected)}")
    return selected


def build_key(company: str, plant: str, nuts2: str) -> str:
    return f"{(company or '').strip()}_{(plant or '').strip()}_{(nuts2 or '').strip()}"


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def load_stage3_components() -> Dict[str, Dict[str, Any]]:
    """
    Returns dict: key -> {company, plant, nuts2_code, components, is_production_site, ...}
    """
    out: Dict[str, Dict[str, Any]] = {}
    if not os.path.isdir(STAGE3_DIR):
        print(f"⚠️  Stage 3 directory not found: {STAGE3_DIR}")
        return out

    files = glob(os.path.join(STAGE3_DIR, "*.json"))
    print(f"   Stage 3: Found {len(files)} JSON files in {STAGE3_DIR}")
    
    for fp in files:
        try:
            d = read_json(fp)
        except Exception:
            continue

        # Stage 3 filter: keep only production sites if present
        if d.get("is_production_site") is False:
            continue

        k = build_key(d.get("company", ""), d.get("plant", ""), d.get("nuts2_code", ""))
        out[k] = d
    
    print(f"   Stage 3: Loaded {len(out)} production site records")
    return out


def load_stage4_employment() -> List[Dict[str, Any]]:
    """
    Returns list of stage4 plant dicts (one per file)
    """
    plants: List[Dict[str, Any]] = []
    if not os.path.isdir(STAGE4_DIR):
        print(f"⚠️  Stage 4 directory not found: {STAGE4_DIR}")
        return plants

    files = glob(os.path.join(STAGE4_DIR, "*.json"))
    print(f"   Stage 4: Found {len(files)} JSON files in {STAGE4_DIR}")
    
    for fp in files:
        try:
            d = read_json(fp)
        except Exception:
            continue
        plants.append(d)
    
    print(f"   Stage 4: Loaded {len(plants)} plant records")
    return plants


def load_stage6_plants_latest() -> Optional[List[Dict[str, Any]]]:
    print(f"\n   Looking for Stage 6 plants in: {RESULTS_DIR}")
    fp = latest_file(os.path.join(RESULTS_DIR, "stage6_plants_*.json"))
    if not fp:
        print("   ⚠️  No Stage 6 plants file found!")
        return None
    d = read_json(fp)
    if isinstance(d, list):
        print(f"   Stage 6 plants: {len(d)} records")
        return d
    return None


def load_stage6_ravi_latest() -> Optional[List[Dict[str, Any]]]:
    print(f"\n   Looking for Stage 6 RAVI in: {RESULTS_DIR}")
    fp = latest_file(os.path.join(RESULTS_DIR, "stage6_ravi_*.json"))
    if not fp:
        print("   ⚠️  No Stage 6 RAVI file found!")
        return None
    d = read_json(fp)
    if isinstance(d, dict) and isinstance(d.get("regions"), list):
        regions = d["regions"]
        print(f"   Stage 6 RAVI: {len(regions)} regions")
        return regions
    return None


def normalize_plants_unified(
    stage3_map: Dict[str, Dict[str, Any]],
    stage4_list: List[Dict[str, Any]],
    stage6_plants: Optional[List[Dict[str, Any]]],
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Produces:
      - plants_unified df (1 row per plant)
      - components_long df (1 row per component per plant)
    """
    rows: List[Dict[str, Any]] = []
    components_long: List[Dict[str, Any]] = []

    # Create lookup from Stage 6 plant file
    stage6_lookup: Dict[str, Dict[str, Any]] = {}
    if stage6_plants:
        for p in stage6_plants:
            k = build_key(p.get("company", ""), p.get("plant", ""), p.get("nuts2_code", ""))
            stage6_lookup[k] = p

    for p4 in stage4_list:
        company = p4.get("company", "")
        plant = p4.get("plant", "")
        nuts2 = p4.get("nuts2_code", "")
        city = p4.get("city", "")

        k = build_key(company, plant, nuts2)

        # Stage 4 employment fields
        emp = None
        size_class = None
        confidence = None
        emp_obj = p4.get("employment") or {}
        if isinstance(emp_obj, dict):
            emp = emp_obj.get("estimate")
            size_class = emp_obj.get("size_class")
            confidence = emp_obj.get("confidence")

        # Stage 3 components + classification
        p3 = stage3_map.get(k, {})
        components = p3.get("components", []) if isinstance(p3, dict) else []
        is_production_site = p3.get("is_production_site") if isinstance(p3, dict) else None

        # Stage 6 computed plant metrics (if available)
        p6 = stage6_lookup.get(k, {})
        plant_tfs = p6.get("plant_tfs")
        plant_ice_dependency = p6.get("plant_ice_dependency")
        component_count = p6.get("component_count")
        ice_count = p6.get("ice_count")
        ev_count = p6.get("ev_count")
        shared_count = p6.get("shared_count")

        row = {
            "key": k,
            "company": company,
            "plant": plant,
            "city": city,
            "nuts2_code": nuts2,
            "employment_estimate": emp,
            "employment_size_class": size_class,
            "employment_confidence": confidence,
            "is_production_site": is_production_site,
            "component_count": component_count if component_count is not None else (len(components) if isinstance(components, list) else 0),
            "ice_count": ice_count,
            "ev_count": ev_count,
            "shared_count": shared_count,
            "plant_tfs": plant_tfs,
            "plant_ice_dependency": plant_ice_dependency,
        }
        rows.append(row)

        # components_long table
        if isinstance(components, list):
            for idx, comp in enumerate(components, start=1):
                if isinstance(comp, dict):
                    c_row = {"key": k, "component_idx": idx}
                    c_row.update(comp)
                else:
                    c_row = {"key": k, "component_idx": idx, "component": str(comp)}
                components_long.append(c_row)

    plants_df = pd.DataFrame(rows)

    # De-duplicate
    if not plants_df.empty:
        plants_df = plants_df.drop_duplicates(subset=["key"], keep="last")

    components_df = pd.DataFrame(components_long)
    return plants_df, components_df


def main():
    ensure_dir(RESULTS_DIR)

    print("=" * 60)
    print("DIAGNOSTIC: Loading data sources")
    print("=" * 60)
    
    print(f"\n📁 Working directory: {os.getcwd()}")
    print(f"📁 Results directory: {os.path.abspath(RESULTS_DIR)}")
    
    # List all files in results directory
    if os.path.isdir(RESULTS_DIR):
        all_results = os.listdir(RESULTS_DIR)
        print(f"\n📋 All files in results/:")
        for f in sorted(all_results):
            print(f"   {f}")
    
    print("\n" + "-" * 60)
    print("Loading Stage 3 (components)...")
    stage3_map = load_stage3_components()
    
    print("\n" + "-" * 60)
    print("Loading Stage 4 (employment)...")
    stage4_list = load_stage4_employment()
    
    print("\n" + "-" * 60)
    print("Loading Stage 6 (computed metrics)...")
    stage6_plants = load_stage6_plants_latest()
    ravi_regions = load_stage6_ravi_latest()

    print("\n" + "=" * 60)

    if not stage4_list:
        raise SystemExit(
            f"No Stage 4 JSON files found in {STAGE4_DIR}. "
            "This unified exporter uses Stage 4 as the plant master list."
        )

    plants_df, components_df = normalize_plants_unified(stage3_map, stage4_list, stage6_plants)

    # Regions/RAVI table
    ravi_df = pd.DataFrame(ravi_regions) if ravi_regions else pd.DataFrame()

    # Join region data onto plants
    if not ravi_df.empty and "nuts2_code" in plants_df.columns and "nuts2_code" in ravi_df.columns:
        ravi_cols = [c for c in [
            "nuts2_code", "nuts2_name", "ravi_score", "vulnerability_rank", "vulnerability_category",
            "weighted_tfs", "weighted_ice_dependency", "total_employment", "auto_employment_share", "exposure",
            "adaptive_capacity"
        ] if c in ravi_df.columns]
        plants_df = plants_df.merge(ravi_df[ravi_cols], on="nuts2_code", how="left", suffixes=("", "_region"))

    # Write Excel
    with pd.ExcelWriter(OUT_XLSX, engine="openpyxl") as writer:
        plants_df.to_excel(writer, sheet_name="plants_unified", index=False)
        if not components_df.empty:
            components_df.to_excel(writer, sheet_name="components_long", index=False)
        if not ravi_df.empty:
            ravi_df.to_excel(writer, sheet_name="regions_ravi", index=False)

    print(f"\n✅ Unified Excel written: {OUT_XLSX}")
    print(f"   plants_unified rows: {len(plants_df):,}")
    print(f"   components_long rows: {len(components_df):,}")
    print(f"   regions_ravi rows: {len(ravi_df):,}")


if __name__ == "__main__":
    main()