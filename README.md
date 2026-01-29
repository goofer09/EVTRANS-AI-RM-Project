# EVTRANS-AI-RM Project

A collection of pipelines and experiments for automotive transition-risk assessment, including an LLM-powered HS component analysis workflow and regional (NUTS2) factory/region risk pipelines.

## 🔍 Overview

This repository houses multiple workflows that support EV transition risk analysis:

- **HS Component Pipeline**: LLM-driven extraction of sub-components, ICE/EV compatibility classification, and risk scoring based on HS (Harmonized System) codes.
- **NUTS2 Factory/Region Pipelines**: Multi-stage OpenAI/LLM workflows for factory and regional risk data enrichment and validation.
- **Test Outputs & Prompt Iterations**: Stored outputs and experiments used to validate or tune prompts.

If you want a single, end-to-end walkthrough for the HS component workflow, start with the detailed guide in `HS_Component_Pipeline/README.md`.

## 📂 Repository Layout

| Path | Purpose |
| --- | --- |
| `HS_Component_Pipeline/` | Main LLM workflow for HS code-based component analysis (enricher → classifier → scorer → validator). |
| `NUTS2_Factory_Pipeline/` | Multi-stage pipeline for NUTS2 factory analysis and reporting. |
| `NUTS2_Region_Output/` | Region-level pipeline outputs and supporting scripts (e.g., heatmap). |
| `openai_stages/` | Supporting stage prompts/scripts for OpenAI-driven workflows. |
| `enricher/`, `prompt_iterations/`, `validator_testing/` | Prompt iterations, experiments, and validation runs. |
| `*_test_outputs/`, `Component Output/` | Historical outputs used for comparison and QA. |

## 🚀 Quick Start (HS Component Pipeline)

> For the full, step-by-step walkthrough (including Ollama setup), see `HS_Component_Pipeline/README.md`.

1. **Install dependencies**
   ```bash
   cd HS_Component_Pipeline
   pip install -r requirements.txt
   ```

2. **Run an end-to-end analysis**
   ```python
   from workflow_integrator import WorkflowIntegrator

   integrator = WorkflowIntegrator(debug=True, max_retries=2)
   result = integrator.run_complete_analysis(
       hs_code="8708.30",
       description="Brake systems for motor vehicles"
   )
   output_file = integrator.save_results(result)
   print(f"Results saved to: {output_file}")
   ```

## 🧪 Testing & Validation

- Prompt tests and output samples are stored under `Classifier_test_outputs/`, `Scorer_test_outputs/`, and other `*_test_outputs/` folders.
- Validation scripts and diagnostics for the factory/region pipelines live in `NUTS2_Factory_Pipeline/` and `NUTS2_Region_Output/`.

## 📌 Notes

- Several folders contain historical artifacts and experiment outputs. Use the primary pipeline directories for current workflows.
- Requirements may vary per pipeline; check the local `requirements.txt` where available.

## 📄 License

Refer to `MIT License` for licensing details.
