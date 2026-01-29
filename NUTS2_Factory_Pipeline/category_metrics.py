"""
category_metrics.py - Bridge between Stage 3 categories and TFS/ICE dependency scores

This module maps the component categories from Stage 3 (run_stage3_v2.py) to:
1. TFS (Transition Feasibility Score) - from your Stage 1 component analysis
2. ICE Dependency - for RAVI exposure calculation

CATEGORIES from Stage 3:
- Vehicle Assembly
- Powertrain Components
- Electric Powertrain Components
- Battery Systems
- Chassis & Suspension
- Body & Structural Parts
- Interior Systems
- Electronics & Control Units

ICE/EV TYPES from Stage 3:
- ICE = combustion-dependent
- EV = exists only due to electric drivetrain
- Shared = drivetrain-agnostic
"""

# ============================================================
# CATEGORY TO TFS/ICE DEPENDENCY MAPPING
# ============================================================

# Base TFS scores by category (derived from Stage 1 component analysis)
# Higher TFS = better transition feasibility
CATEGORY_BASE_TFS = {
    "Vehicle Assembly": 55,                    # Mixed - depends on what's assembled
    "Powertrain Components": 30,               # Mostly ICE-specific
    "Electric Powertrain Components": 88,      # EV-aligned
    "Battery Systems": 90,                     # EV-aligned
    "Chassis & Suspension": 72,                # Mostly shared
    "Body & Structural Parts": 78,             # Mostly shared
    "Interior Systems": 80,                    # Mostly shared
    "Electronics & Control Units": 75,         # Mostly shared, some ICE-specific
}

# Base ICE dependency by category (0 = fully EV-aligned, 1 = fully ICE-dependent)
CATEGORY_BASE_ICE_DEP = {
    "Vehicle Assembly": 0.40,
    "Powertrain Components": 0.90,             # High ICE dependency
    "Electric Powertrain Components": 0.00,    # No ICE dependency
    "Battery Systems": 0.00,                   # No ICE dependency
    "Chassis & Suspension": 0.25,
    "Body & Structural Parts": 0.15,
    "Interior Systems": 0.10,
    "Electronics & Control Units": 0.20,
}

# Adjustment factors based on ICE/EV type classification
ICE_EV_TFS_ADJUSTMENT = {
    "ICE": -15,      # Reduce TFS for ICE-only components
    "EV": +10,       # Increase TFS for EV components
    "Shared": 0,     # No adjustment for shared
}

ICE_EV_DEP_ADJUSTMENT = {
    "ICE": 0.30,     # Increase ICE dependency
    "EV": -0.20,     # Decrease ICE dependency (floor at 0)
    "Shared": 0,     # No adjustment
}


# ============================================================
# SCORING FUNCTIONS
# ============================================================

def get_component_tfs(category: str, ice_ev_type: str = "Shared") -> int:
    """
    Calculate TFS score for a component based on category and ICE/EV type.
    
    Args:
        category: Component category from Stage 3
        ice_ev_type: "ICE", "EV", or "Shared"
    
    Returns:
        TFS score (0-100)
    """
    base_tfs = CATEGORY_BASE_TFS.get(category, 55)  # Default to middle
    adjustment = ICE_EV_TFS_ADJUSTMENT.get(ice_ev_type, 0)
    
    # Clamp to valid range
    return max(10, min(95, base_tfs + adjustment))


def get_component_ice_dependency(category: str, ice_ev_type: str = "Shared") -> float:
    """
    Calculate ICE dependency for a component based on category and ICE/EV type.
    
    Args:
        category: Component category from Stage 3
        ice_ev_type: "ICE", "EV", or "Shared"
    
    Returns:
        ICE dependency (0.0 to 1.0)
    """
    base_dep = CATEGORY_BASE_ICE_DEP.get(category, 0.50)
    adjustment = ICE_EV_DEP_ADJUSTMENT.get(ice_ev_type, 0)
    
    # Clamp to valid range
    return max(0.0, min(1.0, base_dep + adjustment))

def get_plant_metrics(components: list) -> dict:
    """
    Calculate aggregate TFS and ICE dependency for a plant based on its components.
    
    Args:
        components: List of component dicts from Stage 3 output
                   [{"category": "...", "ice_ev_type": "...", "confidence": "..."}]
    
    Returns:
        {
            "plant_tfs": weighted average TFS,
            "plant_ice_dependency": weighted average ICE dependency,
            "component_count": number of components,
            "ice_count": number of ICE components,
            "ev_count": number of EV components,
            "shared_count": number of shared components
        }
    """
    if not components:
        return {
            "plant_tfs": 55,
            "plant_ice_dependency": 0.50,
            "component_count": 0,
            "ice_count": 0,
            "ev_count": 0,
            "shared_count": 0
        }


    # Confidence weights
    confidence_weights = {"high": 1.0, "medium": 0.7, "low": 0.4}
    
    total_weight = 0
    weighted_tfs = 0
    weighted_ice_dep = 0
    
    ice_count = 0
    ev_count = 0
    shared_count = 0
    
    for comp in components:
        category = comp.get("category", "")
        ice_ev_type = comp.get("ice_ev_type", "Shared")
        confidence = comp.get("confidence", "medium")
        
        weight = confidence_weights.get(confidence, 0.7)
        
        tfs = get_component_tfs(category, ice_ev_type)
        ice_dep = get_component_ice_dependency(category, ice_ev_type)
        
        weighted_tfs += tfs * weight
        weighted_ice_dep += ice_dep * weight
        total_weight += weight
        
        # Count by type
        if ice_ev_type == "ICE":
            ice_count += 1
        elif ice_ev_type == "EV":
            ev_count += 1
        else:
            shared_count += 1
    
    if total_weight > 0:
        avg_tfs = weighted_tfs / total_weight
        avg_ice_dep = weighted_ice_dep / total_weight
    else:
        avg_tfs = 55
        avg_ice_dep = 0.50
    
    return {
        "plant_tfs": round(avg_tfs, 1),
        "plant_ice_dependency": round(avg_ice_dep, 3),
        "component_count": len(components),
        "ice_count": ice_count,
        "ev_count": ev_count,
        "shared_count": shared_count
    }



# ============================================================
# TESTING
# ============================================================

if __name__ == "__main__":
    # Test with sample Stage 3 output
    sample_components = [
        {"category": "Vehicle Assembly", "ice_ev_type": "Shared", "confidence": "high"},
        {"category": "Powertrain Components", "ice_ev_type": "ICE", "confidence": "high"},
        {"category": "Body & Structural Parts", "ice_ev_type": "Shared", "confidence": "medium"},
    ]
    
    print("Sample plant metrics:")
    metrics = get_plant_metrics(sample_components)
    for k, v in metrics.items():
        print(f"  {k}: {v}")
    
    print("\nCategory TFS scores:")
    for cat in CATEGORY_BASE_TFS:
        print(f"  {cat}:")
        print(f"    ICE:    TFS={get_component_tfs(cat, 'ICE'):3d}, ICE_dep={get_component_ice_dependency(cat, 'ICE'):.2f}")
        print(f"    Shared: TFS={get_component_tfs(cat, 'Shared'):3d}, ICE_dep={get_component_ice_dependency(cat, 'Shared'):.2f}")
        print(f"    EV:     TFS={get_component_tfs(cat, 'EV'):3d}, ICE_dep={get_component_ice_dependency(cat, 'EV'):.2f}")