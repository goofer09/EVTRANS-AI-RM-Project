import pandas as pd
import os
import json

# Load Excel
df = pd.read_excel("hs_codes.xlsx", usecols=["hs_code", "hs_description"])

# Test print — optional, can be removed later
print(df.head())

# Ensure the folder exists
os.makedirs("prompt_iterations", exist_ok=True)

# Loop through each row of the Excel
for index, row in df.iterrows():
    hs_code = row["hs_code"]
    hs_desc = row["hs_description"]

    # Create v5 JSON template
    json_data = {
        "version": "v5_iteration",
        "date": "2026-01-04",
        "hs_code": hs_code,
        "hs_description": hs_desc,
        "model": "mistral:7b",
        "temperature": 0.2,
        "prompt": f"You are an automotive engineering expert.\nFor HS Code {hs_code} ({hs_desc}), identify the TOP 4 most critical **physical sub-components** of the braking system. Exclude driver interface components (pedal assembly), sensors, or any non-essential parts. Focus only on parts directly responsible for stopping the vehicle.\n\nUse **consistent component terminology** across all outputs (e.g., always 'Brake Pads', never 'Brake Pads/Shoes'). Ensure **subsystems are clearly labeled** and distinct (Wheel Brake System vs Hydraulic Brake System).\n\nExamples of critical sub-components: brake pads, brake calipers, brake master cylinder, brake booster, brake discs.\n\nReturn ONLY valid JSON (no markdown, no explanations):\n[\n  {{\"name\": \"Component 1\", \"function\": \"Primary function\", \"subsystem\": \"Subsystem\"}},\n  {{\"name\": \"Component 2\", \"function\": \"Primary function\", \"subsystem\": \"Subsystem\"}},\n  {{\"name\": \"Component 3\", \"function\": \"Primary function\", \"subsystem\": \"Subsystem\"}},\n  {{\"name\": \"Component 4\", \"function\": \"Primary function\", \"subsystem\": \"Subsystem\"}}\n]\n\nRequirements:\n- Exactly 4 components\n- Use precise engineering terms\n- Focus on **combustion-engine vehicles**\n- Avoid any parts that are not essential for brake operation\n- Functions must be concise and clear",
        "output": []
    }

    # Save JSON file
    filename = f"prompt_iterations/v5_{hs_code}.json"
    with open(filename, "w") as f:
        json.dump(json_data, f, indent=4)

    print(f"Saved {filename}")

