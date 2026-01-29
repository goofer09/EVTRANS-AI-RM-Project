import os
import json
from classifier.llm_classifier_v5 import ComponentClassifierV5

INPUT_FOLDER = "prompt_iterations/v6_outputs"
OUTPUT_FOLDER = "prompt_iterations/classifier_v5_outputs"

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

classifier = ComponentClassifierV5()

for filename in os.listdir(INPUT_FOLDER):
    if not filename.endswith(".json"):
        continue

    in_path = os.path.join(INPUT_FOLDER, filename)
    out_path = os.path.join(OUTPUT_FOLDER, filename)

    with open(in_path, "r") as f:
        data = json.load(f)

    components = data.get("components", [])

    classified_components = []

    for comp in components:
        name = comp.get("name", "")
        result = classifier.classify_component(name)

        classified_components.append({
            "component": name,
            "classification": result["classification"],
            "confidence": result["confidence"],
            "reasoning": result["reasoning"]
        })

    output = {
        "version": "classifier_v5",
        "hs_code": data.get("hs_code"),
        "classified_components": classified_components
    }

    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"Classified {filename} ✅")

print("✅ Classifier v5 batch complete.")

