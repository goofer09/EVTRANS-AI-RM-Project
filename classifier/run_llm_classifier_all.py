import json
import os
from classifier.llm_classifier import ComponentClassifier

INPUT_DIR = "prompt_iterations/v6_outputs"
OUTPUT_DIR = "prompt_iterations/classifier_v4_outputs"

os.makedirs(OUTPUT_DIR, exist_ok=True)

classifier = ComponentClassifier()

for filename in os.listdir(INPUT_DIR):
    if not filename.endswith(".json"):
        continue

    input_path = os.path.join(INPUT_DIR, filename)
    output_path = os.path.join(OUTPUT_DIR, filename)

    with open(input_path, "r") as f:
        data = json.load(f)

    hs_code = data.get("hs_code")
    components = data.get("components", [])

    classified = classifier.classify_components(components, hs_code)

    output = {
        "version": "classifier_v4",
        "hs_code": hs_code,
        "classified_components": classified
    }

    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"Processed {filename} ✅")

print("✅ Classifier v4 batch complete.")

