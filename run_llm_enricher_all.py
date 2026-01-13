#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
from llm_enricher import SubComponentEnricher

# -----------------------------
# Configuration
# -----------------------------
output_folder = "prompt_iterations/v6_outputs"
os.makedirs(output_folder, exist_ok=True)

# List all HS code JSON files from previous v5 batch
input_folder = "prompt_iterations"
hs_files = [
    f for f in os.listdir(input_folder)
    if f.startswith("v5_") and f.endswith(".json")
]

enricher = SubComponentEnricher()

# -----------------------------
# Batch processing
# -----------------------------
for filename in sorted(hs_files):
    try:
        # Read input JSON to get HS code and description
        with open(os.path.join(input_folder, filename), "r") as f:
            data = json.load(f)

        hs_code = data.get("hs_code") or data.get("hs_code", "")
        description = data.get("hs_description") or data.get("hs_description", "")

        if not hs_code or not description:
            print(f"Skipping {filename} – missing HS code or description")
            continue

        # Enrich components using v6 prompt
        components = enricher.enrich(hs_code, description)

        # Save to v6 folder
        output_path = os.path.join(output_folder, filename)
        with open(output_path, "w") as f:
            json.dump({
                "version": "v6_iteration",
                "date": "2026-01-05",
                "hs_code": hs_code,
                "hs_description": description,
                "components": components
            }, f, indent=2)

        print(f"Processed {filename} ✅ Saved to {output_path}")

    except Exception as e:
        print(f"ERROR processing {filename}: {e}")

print("\n✅ Batch processing complete. All outputs in:", output_folder)

