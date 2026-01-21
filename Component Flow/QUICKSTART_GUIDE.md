# ⚡ Quick Start Guide

**Get up and running with the RM Project in 5 minutes**

---

## 🎯 What You Need

1. Python 3.8+
2. Ollama running locally
3. Mistral 7B model

---

## 🚀 Installation (2 minutes)

### Step 1: Install Ollama
```bash
# Linux/WSL
curl -fsSL https://ollama.com/install.sh | sh

# macOS
brew install ollama
```

### Step 2: Download Model
```bash
ollama pull mistral:7b
```

### Step 3: Start Ollama Server
```bash
# In a separate terminal, keep this running
ollama serve
```

### Step 4: Install Python Dependencies
```bash
cd /home/goofe/RM
pip install -r requirements.txt
```

---

## ⚙️ How to Run (3 minutes)

### Option 1: Complete Pipeline (RECOMMENDED)
**Use the Workflow Integrator to run all three components automatically**

```python
from workflow_integrator import WorkflowIntegrator

# Initialize
integrator = WorkflowIntegrator(debug=True, max_retries=2)

# Run complete analysis
result = integrator.run_complete_analysis(
    hs_code="8708.30",
    description="Brake systems for motor vehicles"
)

# Check results
print(f"✅ Quality Score: {result['overall_quality']}/100")
print(f"✅ Valid: {result['valid']}")
print(f"✅ Confidence: {result['overall_confidence']}")

# Save to JSON
output_file = integrator.save_results(result)
print(f"📁 Saved to: {output_file}")
```

**What happens:**
1. Enricher identifies 4 sub-components
2. Classifier classifies each as ICE/EV/SHARED
3. Scorer scores each on 6 dimensions
4. Validator checks quality and generates overall score
5. Results saved to `results/analysis_*.json`

---

### Option 2: Individual Components
**Run just one component at a time**

#### Run Enricher Only
```python
from llm_enricher import SubComponentEnricher

enricher = SubComponentEnricher()
components = enricher.enrich("8708.30", "Brake systems")

print(f"Found {len(components)} components:")
for comp in components:
    print(f"  - {comp['name']}: {comp['function']}")
```

**Output:**
```
Found 4 components:
  - Brake Rotor: Friction surface for braking
  - Brake Caliper: Houses brake pads and pistons
  - Brake Pads: Creates friction against rotor
  - Brake Master Cylinder: Converts pedal force to hydraulic pressure
```

#### Run Classifier Only
```python
from llm_classifier import ComponentClassifier

classifier = ComponentClassifier()
components = ["Brake Rotor", "Brake Caliper", "Brake Pads"]

classifications = classifier.classify(components, "8708.30")

for c in classifications:
    print(f"{c['name']}: {c['classification']} (confidence: {c['similarity_score']:.2f})")
```

**Output:**
```
Brake Rotor: SHARED (confidence: 0.95)
Brake Caliper: SHARED (confidence: 0.92)
Brake Pads: SHARED (confidence: 0.88)
```

#### Run Scorer Only
```python
from llm_scorer import ComponentScorer

scorer = ComponentScorer()
components = ["Brake Rotor", "Brake Caliper"]

scores = scorer.score(components, "8708.30")

for s in scores:
    print(f"{s['name']}:")
    print(f"  Tech: {s['tech']}, Mfg: {s['manufacturing']}, Supply: {s['supply_chain']}")
    print(f"  Demand: {s['demand']}, Value: {s['value']}, Reg: {s['regulatory']}")
```

**Output:**
```
Brake Rotor:
  Tech: 85, Mfg: 90, Supply: 88
  Demand: 85, Value: 80, Reg: 92
Brake Caliper:
  Tech: 82, Mfg: 88, Supply: 85
  Demand: 83, Value: 78, Reg: 90
```

---

### Option 3: Run Test Suite
**Test all components with predefined test cases**

```bash
cd prompt_testing
python3 prompt_test_integrator.py
```

**What happens:**
- Runs multiple test cases through complete pipeline
- Saves results to `prompt_iterations/`
- Prints summary statistics
- Shows success rates and timings

---

## 📊 Understanding the Output

### Workflow Integrator Output Structure
```python
{
    "timestamp": "2026-01-16T10:30:00",
    "hs_code": "8708.30",
    "description": "Brake systems",
    "processing_time": 45.2,  # seconds

    "stages": {
        "enricher": {
            "success": true,
            "output": [
                {
                    "name": "Brake Rotor",
                    "function": "Friction surface",
                    "subsystem": "Braking System"
                },
                # ... 3 more components
            ]
        },
        "classifier": {
            "success": true,
            "output": [
                {
                    "name": "Brake Rotor",
                    "classification": "SHARED",
                    "similarity_score": 0.95
                },
                # ... more
            ]
        },
        "scorer": {
            "success": true,
            "output": [
                {
                    "name": "Brake Rotor",
                    "tech": 85,
                    "manufacturing": 90,
                    "supply_chain": 88,
                    "demand": 85,
                    "value": 80,
                    "regulatory": 92
                },
                # ... more
            ]
        },
        "validator": {
            "quality_score": 85,
            "valid": true,
            "confidence": "HIGH",
            "issues": []
        }
    },

    "overall_quality": 85,      # 0-100
    "overall_confidence": "HIGH",  # LOW/MEDIUM/HIGH
    "valid": true,
    "errors": [],
    "warnings": [],
    "summary": "Analysis completed successfully with high confidence."
}
```

---

## 🎯 Common Use Cases

### Use Case 1: Analyze Single HS Code
```python
from workflow_integrator import WorkflowIntegrator

integrator = WorkflowIntegrator(debug=False)  # Set to False for less output
result = integrator.run_complete_analysis("8708.40", "Gearboxes")

if result['valid']:
    print(f"✅ Success! Quality: {result['overall_quality']}/100")
else:
    print(f"❌ Failed: {result['errors']}")
```

### Use Case 2: Batch Process Multiple HS Codes
```python
from workflow_integrator import WorkflowIntegrator

hs_codes = [
    ("8708.30", "Brake systems"),
    ("8708.40", "Gearboxes"),
    ("8708.94", "Steering wheels"),
    ("8708.99", "Other parts"),
]

integrator = WorkflowIntegrator()

for code, desc in hs_codes:
    print(f"\nProcessing {code}: {desc}")
    result = integrator.run_complete_analysis(code, desc)
    integrator.save_results(result)
    print(f"  Quality: {result['overall_quality']}/100 | Valid: {result['valid']}")
```

### Use Case 3: Just Get Component Names
```python
from llm_enricher import SubComponentEnricher

enricher = SubComponentEnricher()
components = enricher.enrich("8708.30", "Brake systems")
component_names = [c['name'] for c in components]

print(component_names)
# Output: ['Brake Rotor', 'Brake Caliper', 'Brake Pads', 'Brake Master Cylinder']
```

---

## 🔧 Troubleshooting

### Problem 1: "Connection refused"
**Solution:**
```bash
# Make sure Ollama is running
ollama serve
```

### Problem 2: "Model not found"
**Solution:**
```bash
# Download the model
ollama pull mistral:7b

# Verify it's installed
ollama list
```

### Problem 3: Timeout Errors
**Possible causes:**
- System too slow
- Model taking too long
- Heavy CPU load

**Solutions:**
1. Increase timeout in component files
2. Reduce concurrent processes
3. Use a faster machine
4. Check CPU/RAM usage with `top` or `htop`

### Problem 4: Import Errors
**Solution:**
```bash
# Reinstall dependencies
pip install -r requirements.txt --upgrade

# Or install individually
pip install requests pandas pytest
```

### Problem 5: Results Not Saving
**Solution:**
```bash
# Create results directory
mkdir -p results

# Check write permissions
ls -la results/
```

---

## 📈 What to Expect

### Performance Metrics
- **Enricher**: 15-30 seconds
- **Classifier**: 30-60 seconds (4 components)
- **Scorer**: 30-60 seconds (4 components)
- **Total Pipeline**: 2-3 minutes

### Quality Metrics
- **Enricher Accuracy**: ~70%
- **Classifier Accuracy**: ~75%
- **Scorer Consistency**: ~60%
- **Overall Success Rate**: ~65-70%

### Retry Rates
- Most runs complete on first try
- ~8% require retry
- Timeouts handled gracefully

---

## 🎓 Next Steps

1. **Read the Full README**
   - See [README.md](README.md) for complete documentation

2. **Understand Folder Organization**
   - See [FOLDER_ORGANIZATION.md](FOLDER_ORGANIZATION.md) for project structure

3. **Run Tests**
   ```bash
   cd prompt_testing
   python3 prompt_test_integrator.py
   ```

4. **Explore Results**
   - Check `results/` folder for output JSON files
   - Review `prompt_iterations/` for historical test results

5. **Customize Prompts**
   - See component files: [llm_enricher.py](llm_enricher.py), [llm_classifier.py](llm_classifier.py), [llm_scorer.py](llm_scorer.py)
   - Modify prompts for better accuracy

---

## 💡 Pro Tips

1. **Always check Ollama first**
   ```bash
   ollama list  # Check installed models
   ollama ps    # Check running models
   ```

2. **Use debug mode for troubleshooting**
   ```python
   integrator = WorkflowIntegrator(debug=True)  # Verbose output
   ```

3. **Save results for analysis**
   ```python
   output_file = integrator.save_results(result)
   # Results saved with timestamp for tracking
   ```

4. **Check quality before trusting results**
   ```python
   if result['overall_quality'] >= 80 and result['valid']:
       # High quality, can trust
   else:
       # Low quality, review manually
   ```

5. **Batch processing is efficient**
   - Process multiple HS codes in one session
   - Ollama stays warm, faster responses

---

## ✅ Checklist: Am I Ready?

- [ ] Python 3.8+ installed
- [ ] Ollama installed
- [ ] Mistral 7B model downloaded
- [ ] Ollama server running (`ollama serve`)
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Tested with example code (see Option 1 above)
- [ ] Results saved to `results/` folder
- [ ] Quality score >= 70 on test run

**If all checked, you're ready to go!** 🚀

---

**Need help? Check [README.md](README.md) or review test files in `prompt_testing/`**
