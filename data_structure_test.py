from data_structures import Component, HSCode

# Test 1: Create an HSCode object
hs = HSCode(code="8708.30", description="Brake systems")
print("Created HSCode:", hs)
print()

# Test 2: Add components (simulating LLM Call #1)
components = [
    {"name": "Brake pads", "cost_share": 0.2},
    {"name": "Brake calipers", "cost_share": 0.2},
    {"name": "Rotors", "cost_share": 0.15},
]
hs.add_components(components)
print("Added components:", len(hs.components))
for c in hs.components:
    print(f"  - {c.name} ({c.cost_share})")
print()

# Test 3: Add classifications (simulating LLM Call #2)
classifications = [
    {"name": "Brake pads", "classification": "SHARED", "similarity_score": 0.92},
    {"name": "Brake calipers", "classification": "SHARED", "similarity_score": 0.88},
    {"name": "Rotors", "classification": "SHARED", "similarity_score": 0.85},
]
hs.update_classifications(classifications)
print("Added classifications:")
for c in hs.components:
    print(f"  - {c.name}: {c.classification} ({c.similarity_score})")
print()

# Test 4: Add scores (simulating LLM Call #3)
scores = [
    {
        "name": "Brake pads",
        "tech": 85, "manufacturing": 90, "supply_chain": 88,
        "demand": 85, "value": 80, "regulatory": 92
    },
    {
        "name": "Brake calipers",
        "tech": 82, "manufacturing": 88, "supply_chain": 85,
        "demand": 83, "value": 78, "regulatory": 90
    },
    {
        "name": "Rotors",
        "tech": 80, "manufacturing": 85, "supply_chain": 83,
        "demand": 80, "value": 75, "regulatory": 88
    },
]
hs.update_scores(scores)
print("Added scores:")
for c in hs.components:
    print(f"  - {c.name}: TFS={c.tfs_score}, Timeline={c.timeline}")
print()

# Test 5: Convert to JSON
import json
result_dict = hs.to_dict()
print("Final JSON structure:")
print(json.dumps(result_dict, indent=2))