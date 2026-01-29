import os
import json
from scorer.llm_scorer import ComponentScorer

# ===== CONFIG =====
INPUT_FOLDER = "prompt_iterations/classifier_v4_outputs"
OUTPUT_FOLDER = "prompt_iterations/scorer_v3_outputs"
VERSION_LABEL = "scorer_v3_final"
# ==================

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

scorer = ComponentScorer()

for filename in os.listdir(INPUT_FOLDER):
    if not filename.endswith(".json"):
        continue

    input_path = os.path.join(INPUT_FOLDER, filename)

    with open(input_path, "r") as f:
        data = json.load(f)

    components = data.get("classified_components", [])
    hs_code = data.get("hs_code")

    scored_components = scorer.score_components(components, hs_code)

    output_data = {
        "version": VERSION_LABEL,
        "hs_code": hs_code,
        "scored_components": scored_components
    }

    output_path = os.path.join(OUTPUT_FOLDER, filename)
    with open(output_path, "w") as f:
        json.dump(output_data, f, indent=2)

    print(f"Scored {filename} ✅")

print("✅ Scorer v3 batch complete.")

