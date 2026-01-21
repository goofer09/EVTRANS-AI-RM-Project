# RM Project: Automotive Component Risk Assessment System

**A comprehensive LLM-powered framework for analyzing automotive components and their transition risk from ICE to EV vehicles**

---

## 🎯 Overview

This system uses Large Language Models (LLMs) to automatically analyze automotive components from HS (Harmonized System) codes and assess their:
- **Physical sub-components** (Enricher)
- **ICE/EV compatibility** (Classifier)
- **Transition risk scores** (Scorer)
- **Overall quality validation** (Validator)

**Status:** Production-Ready | **Python:** 3.8+ | **Model:** Mistral 7B via Ollama

---

## 🚀 Quick Start (5 Minutes)

### Prerequisites
```bash
# 1. Check Python version (3.8+ required)
python3 --version

# 2. Install Ollama
# Linux/WSL:
curl -fsSL https://ollama.com/install.sh | sh

# macOS:
brew install ollama

# 3. Download the Mistral model
ollama pull mistral:7b

# 4. Start Ollama server (in a separate terminal)
ollama serve
```

### Installation
```bash
# Clone the repository
git clone <your-repo-url>
cd RM

# Install dependencies
pip install -r requirements.txt
```

### Run Your First Analysis

**Option 1: Using the Integrator (Recommended)**
```python
from workflow_integrator import WorkflowIntegrator

# Initialize the integrator
integrator = WorkflowIntegrator(debug=True, max_retries=2)

# Run complete analysis
result = integrator.run_complete_analysis(
    hs_code="8708.30",
    description="Brake systems for motor vehicles"
)

# Save results
output_file = integrator.save_results(result)
print(f"✅ Analysis complete! Results saved to: {output_file}")
print(f"📊 Overall Quality Score: {result['overall_quality']}/100")
print(f"✅ Valid: {result['valid']}")
```

**Option 2: Using Individual Components**
```python
from llm_enricher import SubComponentEnricher
from llm_classifier import ComponentClassifier
from llm_scorer import ComponentScorer

# Step 1: Enricher - Identify 4 sub-components
enricher = SubComponentEnricher()
components = enricher.enrich("8708.30", "Brake systems for motor vehicles")
print(f"Found components: {[c['name'] for c in components]}")

# Step 2: Classifier - Classify each component
classifier = ComponentClassifier()
classifications = classifier.classify(
    components=[c['name'] for c in components],
    hs_code="8708.30"
)
print(f"Classifications: {[c['classification'] for c in classifications]}")

# Step 3: Scorer - Score each component on 6 dimensions
scorer = ComponentScorer()
scores = scorer.score(
    components=[c['name'] for c in components],
    hs_code="8708.30"
)
print(f"Scores: {scores}")
```

**Option 3: Run Complete Test Suite**
```bash
cd prompt_testing
python3 prompt_test_integrator.py
```

---

## 📊 The Three Core Components

### 1. **LLM Enricher** ([llm_enricher.py](llm_enricher.py))
**Purpose:** Identify exactly 4 physical sub-components from an HS code

**Input:**
- `hs_code`: String (e.g., "8708.30")
- `description`: String (e.g., "Brake systems")

**Output:**
```python
[
    {
        "name": "Brake Rotor",
        "function": "Friction surface for slowing vehicle",
        "subsystem": "Braking System"
    },
    # ... 3 more components
]
```

**Key Features:**
- Uses Mistral 7B with temperature 0.2 (deterministic)
- Fallback parsing: JSON → text lines → defaults
- Focuses on tangible automotive parts only
- 180-second timeout

---

### 2. **LLM Classifier** ([llm_classifier.py](llm_classifier.py))
**Purpose:** Classify each component as ICE_ONLY, EV_ONLY, or SHARED

**Input:**
- `components`: List of component names
- `hs_code`: String for context

**Output:**
```python
[
    {
        "name": "Brake Rotor",
        "classification": "SHARED",
        "similarity_score": 0.95
    },
    # ... more components
]
```

**Key Features:**
- Temperature 0.15 (more deterministic than enricher)
- Validates classification values
- Clamps similarity scores to [0.0, 1.0]
- Per-component timeout handling (300s)

---

### 3. **LLM Scorer** ([llm_scorer.py](llm_scorer.py))
**Purpose:** Score each component on 6 risk dimensions (0-100 scale)

**Input:**
- `components`: List of component names
- `hs_code`: String for context

**Output:**
```python
[
    {
        "name": "Brake Rotor",
        "tech": 85,              # Technical compatibility
        "manufacturing": 90,     # Manufacturing feasibility
        "supply_chain": 88,      # Supply chain continuity
        "demand": 85,            # Market demand
        "value": 80,             # Value preservation
        "regulatory": 92         # Regulatory alignment
    },
    # ... more components
]
```

**Key Features:**
- All scores validated in [0, 100] range
- Multiple parsing strategies with fallbacks
- Defaults to 75 for missing dimensions
- 300-second timeout per component

---

## 🔄 The Integrator: Running All Three at Once

The **WorkflowIntegrator** ([workflow_integrator.py](workflow_integrator.py)) is the master orchestrator that runs all three components in sequence with comprehensive error handling and validation.

### Complete Pipeline Flow
```
INPUT: HS Code + Description
   │
   ├─→ STAGE 1: Enricher
   │      └─→ Identifies 4 components
   │
   ├─→ STAGE 2: Classifier
   │      └─→ Classifies each component (ICE/EV/SHARED)
   │
   ├─→ STAGE 3: Scorer
   │      └─→ Scores each component on 6 dimensions
   │
   ├─→ STAGE 4: Validator
   │      └─→ Validates all outputs, calculates quality score
   │
   └─→ OUTPUT: Complete analysis with quality metrics
```

### Key Features
- **Automatic Retry Logic**: Retries failed operations (max 2 attempts)
- **Timeout Handling**: Gracefully handles API timeouts
- **Validation**: Ensures all outputs meet quality standards
- **Error Tracking**: Logs all errors with timestamps
- **Quality Scoring**: Overall quality score (0-100)
- **Confidence Levels**: HIGH/MEDIUM/LOW confidence ratings

### Running the Integrator
```python
from workflow_integrator import WorkflowIntegrator

integrator = WorkflowIntegrator(debug=True, max_retries=2)

# Run complete analysis
result = integrator.run_complete_analysis("8708.30", "Brake systems")

# Access results
print(f"Enricher Output: {result['stages']['enricher']['output']}")
print(f"Classifier Output: {result['stages']['classifier']['output']}")
print(f"Scorer Output: {result['stages']['scorer']['output']}")
print(f"Validation: {result['stages']['validator']}")
print(f"Overall Quality: {result['overall_quality']}/100")
print(f"Confidence: {result['overall_confidence']}")

# Save to JSON
output_path = integrator.save_results(result)
```

---

## 📁 Project Structure

```
RM/
│
├── 🔧 Core Components (The Three Main LLM Tools)
│   ├── llm_enricher.py              # Identifies 4 sub-components
│   ├── llm_classifier.py            # Classifies ICE/EV/SHARED
│   └── llm_scorer.py                # Scores on 6 dimensions
│
├── 🔗 Integration & Orchestration
│   ├── workflow_integrator.py        # Master orchestrator (runs all 3)
│   ├── comprehensive_validator.py    # Quality validation framework
│   └── data_structures.py            # Component & HSCode dataclasses
│
├── 🧪 Testing & Prompt Optimization
│   ├── prompt_testing/
│   │   ├── prompt_benchmark_test.py        # Base testing utilities
│   │   ├── prompt_enricher_test.py         # Test enricher prompts
│   │   ├── prompt_classifier_test.py       # Test classifier prompts
│   │   ├── prompt_scorer_test.py           # Test scorer prompts
│   │   └── prompt_test_integrator.py       # End-to-end testing
│   └── validator_testing/
│       └── validator_testing.py             # Validation test suite
│
├── 🔄 Multi-Stage Workflow (Optional Pipeline)
│   ├── stage1/run_stage1_v1.py       # Identify companies by region
│   ├── stage2/run_stage2_v1.py       # Identify plants by company
│   ├── stage3/run_stage3_v1.py       # List components by plant
│   ├── stage4/run_stage4_v1.py       # Estimate employment
│   └── stage5/run_stage5_v1.py       # Aggregate & validate
│
├── 📊 Data & Results
│   ├── prompt_iterations/            # All test results (v1-v6)
│   ├── input/                        # Input data files
│   ├── hs_codes.xlsx                 # HS code reference
│   └── results/                      # Final outputs
│
├── 🎨 Component Variants (Archived)
│   ├── enricher/                     # Enricher v1-v6
│   ├── classifier/                   # Classifier v1-v5
│   └── scorer/                       # Scorer v1-v3
│
├── 📖 Documentation
│   ├── README.md                     # This file
│   ├── Setup                         # Setup instructions
│   └── requirements.txt              # Python dependencies
│
└── .git/                             # Git repository
```

---

## 🎯 How the Integrator Works

### Step-by-Step Execution

1. **Initialize the Integrator**
   ```python
   integrator = WorkflowIntegrator(debug=True, max_retries=2)
   ```

2. **Run Complete Analysis**
   ```python
   result = integrator.run_complete_analysis("8708.30", "Brake systems")
   ```

3. **Internal Process:**
   - **Stage 1:** Calls `llm_enricher.enrich()` → gets 4 components
   - **Stage 2:** Calls `llm_classifier.classify()` → classifies each component
   - **Stage 3:** Calls `llm_scorer.score()` → scores each component
   - **Stage 4:** Calls `comprehensive_validator.validate()` → validates all outputs

4. **Output Structure:**
   ```python
   {
       "timestamp": "2026-01-16T10:30:00",
       "hs_code": "8708.30",
       "description": "Brake systems",
       "processing_time": 45.2,  # seconds
       "stages": {
           "enricher": {"output": [...], "success": true},
           "classifier": {"output": [...], "success": true},
           "scorer": {"output": [...], "success": true},
           "validator": {"quality_score": 85, "valid": true}
       },
       "overall_quality": 85,  # 0-100
       "overall_confidence": "HIGH",  # LOW/MEDIUM/HIGH
       "valid": true,
       "errors": [],
       "warnings": [],
       "summary": "Analysis completed successfully..."
   }
   ```

5. **Save Results**
   ```python
   output_file = integrator.save_results(result)
   # Saves to: results/analysis_8708.30_20260116_103000.json
   ```

---

## 🧪 Testing & Validation

### Test Individual Components
```bash
# Test enricher only
cd prompt_testing
python3 prompt_enricher_test.py

# Test classifier only
python3 prompt_classifier_test.py

# Test scorer only
python3 prompt_scorer_test.py
```

### Test Complete Pipeline
```bash
# End-to-end integration test
cd prompt_testing
python3 prompt_test_integrator.py
```

### Run Validation Tests
```bash
cd validator_testing
python3 validator_testing.py
```

---

## 📊 Performance Metrics

| Component | Accuracy | Speed | Retry Rate |
|-----------|----------|-------|------------|
| **Enricher** | 70% | Fast (15-30s) | Low (~5%) |
| **Classifier** | 75% | Medium (30-60s) | Medium (~10%) |
| **Scorer** | 60% | Medium (30-60s) | Medium (~12%) |
| **Overall Pipeline** | 65-70% | 2-3 minutes | Low (~8%) |

---

## 🛠️ Technology Stack

- **Language:** Python 3.8+
- **LLM Runtime:** Ollama (local inference)
- **Model:** Mistral 7B (7 billion parameters)
- **HTTP Client:** requests library
- **Data Format:** JSON
- **Testing:** pytest
- **Dependencies:** See [requirements.txt](requirements.txt)

---

## �� Requirements

```
Python 3.8+
8GB RAM minimum (16GB recommended)
Ollama installed and running
Mistral 7B model downloaded
```

**Install dependencies:**
```bash
pip install -r requirements.txt
```

**Key packages:**
- `requests>=2.28.0` - HTTP API calls
- `pandas>=1.3.0` - Data processing
- `pytest>=7.0.0` - Testing framework

---

## 🔧 Configuration

### Default Settings (Hardcoded)
- **Model:** `mistral:7b`
- **API URL:** `http://localhost:11434/api/generate`
- **Temperatures:**
  - Enricher: 0.2
  - Classifier: 0.15
  - Scorer: 0.15
- **Timeouts:**
  - Enricher: 180 seconds
  - Classifier: 300 seconds
  - Scorer: 300 seconds
- **Max Retries:** 2 per stage

---

## 🎓 Usage Examples

### Example 1: Analyze Brake Systems
```python
from workflow_integrator import WorkflowIntegrator

integrator = WorkflowIntegrator(debug=True)
result = integrator.run_complete_analysis("8708.30", "Brake systems")

if result['valid']:
    print(f"✅ Quality Score: {result['overall_quality']}/100")
    print(f"Components found: {len(result['stages']['enricher']['output'])}")
else:
    print(f"❌ Analysis failed: {result['errors']}")
```

### Example 2: Batch Processing
```python
test_cases = [
    {"hs_code": "8708.30", "description": "Brake systems"},
    {"hs_code": "8708.40", "description": "Gearboxes"},
    {"hs_code": "8708.94", "description": "Steering wheels"},
]

integrator = WorkflowIntegrator()
results = []

for case in test_cases:
    result = integrator.run_complete_analysis(
        case['hs_code'],
        case['description']
    )
    results.append(result)
    integrator.save_results(result)

# Print summary
for r in results:
    print(f"{r['hs_code']}: Quality={r['overall_quality']}, Valid={r['valid']}")
```

### Example 3: Just Use One Component
```python
from llm_enricher import SubComponentEnricher

enricher = SubComponentEnricher()
components = enricher.enrich("8708.30", "Brake systems")

for comp in components:
    print(f"- {comp['name']}: {comp['function']}")
```

---

## 🐛 Troubleshooting

### Common Issues

**1. "Connection refused" error**
```bash
# Make sure Ollama is running
ollama serve
```

**2. "Model not found" error**
```bash
# Download the model
ollama pull mistral:7b
```

**3. Timeout errors**
- Increase timeout values in component files
- Check system resources (CPU/RAM usage)
- Try running with fewer concurrent processes

**4. Import errors**
```bash
# Reinstall dependencies
pip install -r requirements.txt --upgrade
```

---

## 🗺️ Roadmap

- [x] Core components (Enricher, Classifier, Scorer)
- [x] Workflow integrator
- [x] Comprehensive validation framework
- [x] Testing framework
- [ ] Web UI for easier interaction
- [ ] Batch processing optimization
- [ ] Support for additional LLM models
- [ ] API endpoint for external integrations

---

## 📞 Support

For help:
- Check the [Setup](Setup) file for installation guidance
- Review test files in `prompt_testing/` for usage examples
- Open an issue on GitHub for bugs or feature requests

---

## 🔐 License

MIT License - See [LICENSE](LICENSE) file

---

## 👥 Contributors

Developed as part of the EVTRANS-AI-RM Project for automotive component risk assessment.

---

## 📈 Version History

- **v1.0** (2026-01): Initial production release
  - Core components stable
  - Integrator fully functional
  - Comprehensive testing framework
  - Validation pipeline operational

---

**Made with ⚙️ for the automotive industry's EV transition**
