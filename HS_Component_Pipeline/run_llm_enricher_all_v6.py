import os
import json
from llm_enricher import enrich_prompt  # this is your existing enricher function
# Folder where all v5 JSONs are saved
folder = "prompt_iterations"

# Loop over all files in the folder
for filename in os.listdir(folder):
    if filename.startswith("v5_") and filename.endswith(".json"):
        filepath = os.path.join(folder, filename)
        print(f"Processing {filename}...")

        # Open the JSON
        with open(filepath, "r") as f:
            data = json.load(f)

        # Run the enricher on the prompt
        enriched_output = enrich_prompt(data["prompt"])

        # Put the result into the "output" field
        data["output"] = enriched_output

        # Save the JSON back
        with open(filepath, "w") as f:
            json.dump(data, f, indent=4)

        print(f"Saved {filename} ✅")

