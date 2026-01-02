cat > README.md << 'EOF'
# Prompt Engineering System

A comprehensive framework for testing, optimizing, and validating LLM prompts through iterative refinement and measurement.

**Status:** Production-Ready | **Python:** 3.8+ | **License:** MIT

## 🎯 What This Is

A complete system for:
- Testing prompts (enricher, classifier, scorer)
- Getting industry expert feedback
- Validating output quality
- Iteratively improving prompts
- Measuring progress with metrics

## ✨ Key Features

- **Modular Testing Framework**: Test individual stages or full pipeline
- **Expert Feedback Interface**: Collect and apply domain-specific feedback
- **Comprehensive Validation**: Multi-stage quality validation
- **Iterative Optimization**: Structured feedback loop
- **Complete Documentation**: 15+ guides and tutorials
- **Production Ready**: Tested and validated system

## 📊 System Overview

Three core prompts optimized for LLM inference:

| Component | Purpose | Current | Target |
|-----------|---------|---------|--------|
| **Enricher** | Identify 4 main components | 70% | 85%+ |
| **Classifier** | Classify as ICE/EV/SHARED | 75% | 90%+ |
| **Scorer** | Score on 6 dimensions | 60% | 80%+ |

## 🚀 Quick Start (5 minutes)

### Prerequisites
```bash
# Check Python version
python3 --version  # Should be 3.8+

# Install Ollama
brew install ollama

# Download model
ollama pull mistral:7b
```

### Installation
```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/prompt-engineering-system.git
cd prompt-engineering-system

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start Ollama (in new terminal)
ollama serve
```

### First Test
```bash
python3 core/prompt_enricher_tester.py
```

## 📚 Documentation

### Getting Started
- **[First Day Guide](docs/PROMPT_ENGINEER_FIRST_DAY.md)** - 2-hour quick start
- **[Setup Instructions](SETUP.md)** - Detailed installation
- **[Ollama Setup](docs/OLLAMA_MACOS_SETUP_GUIDE.md)** - LLM runtime setup

### Role Guides
- **[Prompt Engineer Role](docs/PROMPT_ENGINEER_ROLE_GUIDE.md)** - Testing, optimization, iteration
- **[Industry Expert Guide](docs/INDUSTRY_EXPERT_FEEDBACK_GUIDE.md)** - Feedback process
- **[Validator Guide](docs/VALIDATOR_COMPREHENSIVE_GUIDE.md)** - Quality assurance

### Framework Docs
- **[Prompt Testing Guide](docs/PROMPT_TESTING_REFACTORED_GUIDE.md)** - How to test prompts
- **[Validation Framework](docs/VALIDATOR_ANALYSIS_SUMMARY.md)** - Quality validation

### Roadmap & Planning
- **[Full Roadmap](docs/ROADMAP_WAY_AHEAD.md)** - 9-week journey to production
- **[One-Page Roadmap](docs/ROADMAP_ONE_PAGE.md)** - Quick overview
- **[Action Checklist](docs/IMMEDIATE_ACTION_CHECKLIST.md)** - This week's tasks

## 🏗️ Project Structure
prompt-engineering-system/
├── core/                           # Main testing framework
│   ├── prompt_benchmark_common.py    # Shared utilities
│   ├── prompt_enricher_tester.py     # Enricher testing
│   ├── prompt_classifier_tester.py   # Classifier testing
│   ├── prompt_scorer_tester.py       # Scorer testing
│   └── prompt_test_overall.py        # End-to-end testing
│
├── validation/                     # Validation framework
│   └── validator_comprehensive.py    # Multi-stage validator
│
├── industry-expert/                # Expert feedback
│   └── industry_expert_feedback.py   # Feedback interface
│
├── docs/                           # Documentation (15+ guides)
├── examples/                       # Example usage
├── tests/                          # Test suite
│
├── README.md                       # This file
├── SETUP.md                        # Installation guide
├── requirements.txt                # Python dependencies
├── .gitignore                      # Git ignore rules
└── LICENSE                         # MIT License

## 🔄 The Iteration Cycle

TEST (15 min)
↓
FEEDBACK (30 min)
↓
MODIFY (20 min)
↓
RE-TEST (10 min)
↓
[Repeat 3-4 times per stage]

## 💻 Usage Examples

### Test Single Prompt
```python
from core.prompt_enricher_tester import EnricherPromptTester

tester = EnricherPromptTester(debug=True)
result = tester.test_prompt("8708.30", "Brake systems")
print(result)
```

### Test Multiple Codes
```python
test_cases = [
    {'hs_code': '8708.30', 'description': 'Brake systems'},
    {'hs_code': '8708.40', 'description': 'Steering systems'},
]
results = tester.test_multiple(test_cases)
tester.print_results(results)
tester.save_results()
```

### End-to-End Testing
```python
from core.prompt_test_overall import OverallPromptTest

tester = OverallPromptTest(debug=True)
results = tester.run_complete_test(test_cases)
tester.save_results()
```

### Comprehensive Validation
```python
from validation.validator_comprehensive import ValidatorPipeline

validator = ValidatorPipeline(debug=True)
results = validator.validate_complete_analysis(
    hs_code="8708.30",
    description="Brake systems",
    enricher_output=...,
    classifier_output=...,
    scorer_output=...,
    ground_truth=...
)
validator.save_validation_results()
```

## 🎯 Key Metrics

**Enricher Quality:**
- Completeness: 4 components always
- Specificity: Real component names, not generic
- Cost share validity: Sum to 1.0
- No hallucinations

**Classifier Accuracy:**
- vs ground truth: 90%+
- Confidence: Reliable scores
- Consistency: Same input = same output

**Scorer Reasonableness:**
- Range validity: All scores in acceptable ranges
- Consistency: Similar patterns across components
- No outliers: Extreme values are rare

## 🛠️ Technology Stack

- **Language:** Python 3.8+
- **LLM Runtime:** Ollama
- **Model:** Mistral 7B
- **HTTP Client:** requests
- **Data:** JSON

## 📋 Requirements

- Python 3.8 or higher
- 8GB RAM minimum
- Ollama installed and running
- Internet for initial setup

## 🔐 License

MIT License - See [LICENSE](LICENSE) file

## 🤝 Contributing

Contributions welcome! 

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📞 Support

For help:
- Check [docs/](docs/) directory for comprehensive guides
- Read [SETUP.md](SETUP.md) for installation help
- See [docs/OLLAMA_MACOS_SETUP_GUIDE.md](docs/OLLAMA_MACOS_SETUP_GUIDE.md) for troubleshooting

## 🗺️ Roadmap

See [docs/ROADMAP_WAY_AHEAD.md](docs/ROADMAP_WAY_AHEAD.md) for the complete 9-week production roadmap.

## 👥 Team Roles

- **Prompt Engineer:** Tests and optimizes prompts
- **Industry Expert:** Reviews accuracy and provides feedback
- **Validator:** Tests quality and detects issues

## 🎓 Learning Resources

- [First Day Quick Start](docs/PROMPT_ENGINEER_FIRST_DAY.md) - Get running in 2 hours
- [Prompt Engineer Role Guide](docs/PROMPT_ENGINEER_ROLE_GUIDE.md) - Understand your job
- [Testing Framework Guide](docs/PROMPT_TESTING_REFACTORED_GUIDE.md) - How testing works
- [Full Roadmap](docs/ROADMAP_WAY_AHEAD.md) - The complete journey

## 📊 Metrics & Tracking

All results are saved to JSON files with:
- Quality metrics per stage
- Processing times
- Error logs
- Success rates
- Improvement tracking
