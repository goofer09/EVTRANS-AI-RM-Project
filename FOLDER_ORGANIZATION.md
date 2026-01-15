# Folder Organization Guide

This document provides a plan for organizing the RM project into a cleaner structure.

---

## 🎯 Current vs. Proposed Structure

### Current Structure (Needs Organization)
```
RM/
├── llm_enricher.py, llm_classifier.py, llm_scorer.py (CORE - Keep in root)
├── llm_enricher_v5.py, llm_enricher_v6_backup.py, etc. (VARIANTS - Move to archive)
├── llm_enricher copy.py, llm_scorer copy.py (DUPLICATES - Delete or archive)
├── workflow_integrator.py (CORE - Keep in root)
├── comprehensive_validator.py (CORE - Keep in root)
├── data_structures.py (CORE - Keep in root)
├── run_llm_enricher_all.py, generate_v5_jsons.py (UTILITIES - Move to scripts/)
├── prompt_testing/ (ORGANIZED - Keep as-is)
├── validator_testing/ (ORGANIZED - Keep as-is)
├── stage1/, stage2/, stage3/, stage4/, stage5/ (WORKFLOW - Keep as-is)
├── enricher/, classifier/, scorer/ (VARIANTS - Keep as-is for now)
└── prompt_iterations/ (RESULTS - Keep as-is)
```

### Proposed Organized Structure
```
RM/
│
├── 📦 CORE FILES (Keep in Root - These are production-ready)
│   ├── llm_enricher.py              ✅ Main enricher
│   ├── llm_classifier.py            ✅ Main classifier
│   ├── llm_scorer.py                ✅ Main scorer
│   ├── workflow_integrator.py       ✅ Master orchestrator
│   ├── comprehensive_validator.py   ✅ Validation framework
│   ├── data_structures.py           ✅ Data models
│   ├── requirements.txt             ✅ Dependencies
│   ├── README.md                    ✅ Main documentation
│   └── Setup                        ✅ Setup guide
│
├── 📂 prompt_testing/               ✅ Testing framework (already organized)
│   ├── prompt_benchmark_test.py
│   ├── prompt_enricher_test.py
│   ├── prompt_classifier_test.py
│   ├── prompt_scorer_test.py
│   └── prompt_test_integrator.py
│
├── 📂 validator_testing/            ✅ Validation tests (already organized)
│   └── validator_testing.py
│
├── 📂 stage1/, stage2/, stage3/, stage4/, stage5/   ✅ Multi-stage workflow (keep as-is)
│
├── 📂 enricher/, classifier/, scorer/   ✅ Component variants (keep for reference)
│
├── 📂 prompt_iterations/            ✅ Test results (keep as-is)
│
├── 📂 input/                        ✅ Input data (keep as-is)
│
├── 📂 scripts/ (NEW - Move utility scripts here)
│   ├── run_llm_enricher_all.py
│   ├── run_llm_enricher_all_v6.py
│   ├── generate_v5_jsons.py
│   └── data_structure_test.py
│
├── 📂 archive/ (NEW - Move old versions and copies here)
│   ├── llm_enricher_v5.py
│   ├── llm_enricher_v6_backup.py
│   ├── llm_enricher_v5_reconstructed.py
│   ├── llm_enricher_current_v6.py
│   ├── llm_enricher copy.py
│   ├── llm_classifier copy.py
│   ├── llm_scorer copy.py
│   └── workflow_integrator_copy.py
│
└── 📂 results/ (NEW - For workflow integrator outputs)
    └── analysis_*.json files go here
```

---

## 🔧 Reorganization Steps

### Step 1: Create New Folders
```bash
mkdir -p scripts archive results
```

### Step 2: Move Utility Scripts
```bash
mv run_llm_enricher_all.py scripts/
mv run_llm_enricher_all_v6.py scripts/
mv generate_v5_jsons.py scripts/
mv data_structure_test.py scripts/
```

### Step 3: Archive Old Versions
```bash
mv llm_enricher_v5.py archive/
mv llm_enricher_v6_backup.py archive/
mv llm_enricher_v5_reconstructed.py archive/
mv llm_enricher_current_v6.py archive/
mv "llm_enricher copy.py" archive/
mv "llm_classifier copy.py" archive/
mv "llm_scorer copy.py" archive/
mv workflow_integrator_copy.py archive/
```

### Step 4: Keep Core Files in Root
These files should stay in the root directory:
- ✅ llm_enricher.py
- ✅ llm_classifier.py
- ✅ llm_scorer.py
- ✅ workflow_integrator.py
- ✅ comprehensive_validator.py
- ✅ data_structures.py
- ✅ requirements.txt
- ✅ README.md
- ✅ Setup

### Step 5: Verify Folder Structure
```bash
# After reorganization, your root should look like:
ls -la RM/
# Expected output:
# llm_enricher.py
# llm_classifier.py
# llm_scorer.py
# workflow_integrator.py
# comprehensive_validator.py
# data_structures.py
# requirements.txt
# README.md
# Setup
# prompt_testing/
# validator_testing/
# stage1/ through stage5/
# enricher/, classifier/, scorer/
# prompt_iterations/
# input/
# scripts/ (NEW)
# archive/ (NEW)
# results/ (NEW)
```

---

## 📋 What Each Folder Contains

### Root Directory (Core Production Files)
- **llm_enricher.py** - Production enricher (identifies 4 components)
- **llm_classifier.py** - Production classifier (ICE/EV/SHARED)
- **llm_scorer.py** - Production scorer (6 dimensions)
- **workflow_integrator.py** - Master orchestrator
- **comprehensive_validator.py** - Validation framework
- **data_structures.py** - Component & HSCode data models
- **requirements.txt** - Python dependencies
- **README.md** - Main documentation
- **Setup** - Setup instructions

### prompt_testing/
Testing framework for all components:
- prompt_benchmark_test.py - Common test utilities
- prompt_enricher_test.py - Enricher testing
- prompt_classifier_test.py - Classifier testing
- prompt_scorer_test.py - Scorer testing
- prompt_test_integrator.py - End-to-end testing

### validator_testing/
- validator_testing.py - Validation test suite

### stage1/ through stage5/
Multi-stage workflow for regional analysis:
- stage1/run_stage1_v1.py - Identify companies
- stage2/run_stage2_v1.py - Identify plants
- stage3/run_stage3_v1.py - List components
- stage4/run_stage4_v1.py - Estimate employment
- stage5/run_stage5_v1.py - Aggregate & validate

### enricher/, classifier/, scorer/
Component variant history (v1-v6):
- Kept for reference and version tracking
- Shows evolution of prompts

### prompt_iterations/
All test results organized by version:
- v1-v6 baseline results
- classifier_v1_outputs/ through classifier_v5_outputs/
- scorer_v1_outputs/ through scorer_v3_outputs/
- stage outputs

### scripts/ (NEW)
Utility scripts and runners:
- run_llm_enricher_all.py - Batch enricher runner
- run_llm_enricher_all_v6.py - Version 6 batch runner
- generate_v5_jsons.py - Generate test JSONs
- data_structure_test.py - Data model testing

### archive/ (NEW)
Old versions and backup copies:
- All "_v5", "_v6_backup", "copy" files
- Deprecated implementations
- Historical reference only

### results/ (NEW)
Output from workflow_integrator:
- analysis_*.json - Complete analysis results
- Auto-generated with timestamps

### input/
Input data files:
- hs_codes.xlsx - HS code reference data
- Other input CSV/Excel files

---

## ⚡ Quick Commands

### Clean Organization in One Go
```bash
# From RM directory
mkdir -p scripts archive results

# Move scripts
mv run_llm_enricher_all.py run_llm_enricher_all_v6.py generate_v5_jsons.py data_structure_test.py scripts/ 2>/dev/null

# Archive old versions
mv llm_enricher_v*.py llm_enricher_current_v6.py archive/ 2>/dev/null
mv *copy.py archive/ 2>/dev/null
mv workflow_integrator_copy.py archive/ 2>/dev/null

echo "✅ Reorganization complete!"
```

### Verify Organization
```bash
# Check root directory (should only have core files)
ls -1 *.py

# Expected output:
# comprehensive_validator.py
# data_structures.py
# llm_classifier.py
# llm_enricher.py
# llm_scorer.py
# workflow_integrator.py
```

---

## 🎯 Benefits of This Organization

1. **Clean Root Directory**
   - Only production-ready files visible
   - Easy to identify core components
   - Less confusion for new users

2. **Logical Grouping**
   - Testing files in prompt_testing/
   - Utility scripts in scripts/
   - Old versions in archive/
   - Results in results/

3. **Easy Navigation**
   - Clear folder names indicate purpose
   - Related files grouped together
   - Historical versions preserved but hidden

4. **Git-Friendly**
   - Can add archive/ to .gitignore
   - results/ can be gitignored
   - Clean commit history

---

## 🚨 Important Notes

1. **Don't Delete Archive Files Yet**
   - Keep them in archive/ for reference
   - May need to compare implementations
   - Can delete after 2-3 months of stable production

2. **Update Import Paths**
   - If you move scripts, update any import statements
   - workflow_integrator.py should still work as-is

3. **Git Considerations**
   ```bash
   # Add to .gitignore:
   archive/
   results/
   prompt_iterations/
   *.pyc
   __pycache__/
   ```

4. **Test After Reorganization**
   ```bash
   # Run quick test to ensure everything works
   python3 -c "from workflow_integrator import WorkflowIntegrator; print('✅ Import successful')"
   ```

---

## 📊 File Count Summary

### Before Organization
- Root directory: ~18 Python files (messy)
- Hard to find production files

### After Organization
- Root directory: 6 core Python files (clean)
- Everything else organized in folders
- Much easier to navigate

---

## 🎓 How to Use Organized Structure

### Running Production Code
```python
# Everything stays the same! Imports don't change
from workflow_integrator import WorkflowIntegrator
from llm_enricher import SubComponentEnricher
from llm_classifier import ComponentClassifier
from llm_scorer import ComponentScorer
```

### Running Utility Scripts
```bash
# Now run from scripts folder
python3 scripts/run_llm_enricher_all.py
python3 scripts/generate_v5_jsons.py
```

### Running Tests
```bash
# Tests stay the same
cd prompt_testing
python3 prompt_test_integrator.py
```

---

**This organization makes the project professional, maintainable, and easy to navigate!** 🎯
