import json
import os
from collections import defaultdict

# ============================================================
# CONFIGURATION
# ============================================================

STAGE4_FOLDER = "prompt_iterations/stage4_v1_outputs"
OUTPUT_FILE = "results/stage5_validation_summary.json"

# Conservative employment midpoints
SIZE_CLASS_MIDPOINTS = {
    "Small": 250,
    "Medium": 1250,
    "Large": 3500,
    "Very Large": 7500,
    "Uncertain": 1250  # safe fallback
}

# Eurostat baseline (placeholder – replace later)
EUROSTAT_EMPLOYMENT = {
    "DE11": 185000,  # Stuttgart
    "DE71": 95000,   # Darmstadt
    "DE30": 80000    # Berlin
}

# ============================================================
# MAIN FUNCTION
# ============================================================

def main():
    region_employment = defaultdict(list)
    uncertain_counts = defaultdict(int)

    # -----------------------------
    # Load Stage 4 outputs
    # -----------------------------

    for filename in os.listdir(STAGE4_FOLDER):
        if not filename.endswith(".json"):
            continue

        filepath = os.path.join(STAGE4_FOLDER, filename)
        with open(filepath, "r") as f:
            data = json.load(f)

        nuts2 = data.get("nuts2_code")
        employment = data.get("employment", {})
        size_class = employment.get("size_class", "Uncertain")

        if size_class not in SIZE_CLASS_MIDPOINTS:
            size_class = "Uncertain"

        if size_class == "Uncertain":
            uncertain_counts[nuts2] += 1

        estimate = employment.get("estimate")
        if estimate is None:
            estimate = SIZE_CLASS_MIDPOINTS[size_class]

        region_employment[nuts2].append(estimate)

    # -----------------------------
    # Aggregate & validate
    # -----------------------------

    summary = {
        "version": "stage5_v1",
        "regions": []
    }

    for nuts2, estimates in region_employment.items():
        llm_sum = sum(estimates)
        eurostat = EUROSTAT_EMPLOYMENT.get(nuts2)

        if eurostat is None:
            deviation = None
            status = "NO_BASELINE"
        else:
            deviation = abs(llm_sum - eurostat) / eurostat
            status = "PASS" if deviation <= 0.30 else "FLAG"

        summary["regions"].append({
            "nuts2_code": nuts2,
            "llm_employment_sum": llm_sum,
            "eurostat_employment": eurostat,
            "deviation": deviation,
            "validation_status": status,
            "uncertain_plants": uncertain_counts.get(nuts2, 0)
        })

    # -----------------------------
    # Save results
    # -----------------------------

    os.makedirs("results", exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"✅ Stage 5 summary saved to {OUTPUT_FILE}")

# ============================================================

if __name__ == "__main__":
    main()

