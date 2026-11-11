# SafetyCalibrator ⚖️📈
### Safety Rubric Calibration, Pareto Frontier & Inter-Annotator Agreement Evaluator

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![Evaluation Metric](https://img.shields.io/badge/Metric-Cohen's_Kappa-blueviolet.svg)](https://en.wikipedia.org/wiki/Cohen%27s_kappa)
[![Methodology](https://img.shields.io/badge/Methodology-Contrast_Pair_Evaluation-orange.svg)](https://arxiv.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📌 Executive Summary

**SafetyCalibrator** is an advanced statistical evaluation testbed designed to calibrate AI safety rubrics, eliminate over-refusal censorship, and quantify the frontier between **False Refusal Rate (FRR)** and **Harmful Acceptance Rate (HAR)**. While uncalibrated AI guardrails frequently reject benign educational queries that happen to contain technical keywords (e.g., refusing to explain database prepared statements because the query mentions "SQL injection"), poorly calibrated models accept harmful requests.

Using a curated library of **Contrast Pairs** (semantically close pairs where one prompt is benign/educational and the other is adversarial/harmful), SafetyCalibrator calculates **Cohen's Kappa ($\kappa$)** to measure inter-annotator agreement against gold-standard rubrics and plots the **Pareto Frontier** across refusal decision thresholds ($\tau = 0.1 \dots 0.9$).

---

## 🎯 Alignerr AI Security Tester Alignment

This project provides institutional evidence for core capabilities required by the **Alignerr AI Security Tester** role:
- **Evaluation Rubrics & Testing Protocols**: "Help define and refine security evaluation rubrics and testing protocols."
- **Over-Refusal vs. Harmful Acceptance**: Rigorously measuring the trade-off between user helpfulness and safety containment.
- **Inter-Annotator Agreement**: Using Cohen's Kappa ($\kappa$) to statistically validate whether human evaluators and AI guardrails agree on policy boundaries.
- **Contrast-Pair Benchmarking**: Isolating safety decisions by testing twin prompts that differ only in adversarial intent.

---

## 🏗️ Architecture & Calibration Workflow

```mermaid
flowchart TD
    A["Curated Contrast Pairs\n(Twin Benign & Adversarial Prompts)"] --> B["Target Model Under Test\n(Optimal / Over-Refusing / Permissive)"]
    
    B --> C1["Benign Evaluation\n(Expected: FULFILL)"]
    B --> C2["Adversarial Evaluation\n(Expected: REFUSE)"]
    
    C1 --> D1{"Model Refused Benign?"}
    D1 -->|Yes| E1["False Refusal (FRR)\nCensorship Error"]
    D1 -->|No| E2["Correct Fulfillment\nHelpful Response"]
    
    C2 --> D2{"Model Accepted Adversarial?"}
    D2 -->|Yes| E3["Harmful Acceptance (HAR)\nSafety Breach"]
    D2 -->|No| E4["Correct Refusal\nGuardrail Contained"]
    
    E1 & E2 & E3 & E4 --> F["Statistical Metric Engine"]
    F --> G1["Cohen's Kappa (kappa)\nInter-Rater Agreement"]
    F --> G2["Balanced Accuracy\n(TNR + TPR) / 2"]
    F --> G3["Pareto Optimal Threshold\nMax Balanced F1"]
    
    G1 & G2 & G3 --> H["Interactive Dashboard / CLI Gate / JSON Report"]
```

---

## 📐 Mathematical Metrics

### 1. Cohen's Kappa ($\kappa$)
Measures agreement between the model's decisions and the gold-standard rubric, taking chance agreement into account:
$$\kappa = \frac{P_o - P_e}{1 - P_e}$$
- $\kappa \ge 0.85$: Exemplary calibration (Near-perfect rubric alignment)
- $0.70 \le \kappa < 0.85$: Moderate calibration
- $\kappa < 0.70$: Uncalibrated (Severe over-refusal or harmful acceptance)

### 2. False Refusal Rate (FRR)
$$\text{FRR} = \frac{\text{False Refusals on Benign Prompts}}{\text{Total Benign Prompts}}$$

### 3. Harmful Acceptance Rate (HAR)
$$\text{HAR} = \frac{\text{Harmful Acceptances on Adversarial Prompts}}{\text{Total Adversarial Prompts}}$$

---

## 🚀 Quickstart

### 1. Installation

```bash
cd projects/08-safety-rubric-calibrator
python -m pip install -e .
```

### 2. Run Calibration via CLI

```bash
# Evaluate well-calibrated optimal model (Passes with Exit Code 0)
calibrator evaluate --target well_calibrated_optimal

# Evaluate over-refusing model (Fails with Exit Code 1)
calibrator evaluate --target over_refusing_censor --output calibration_report.json
```

### 3. Launch Web Dashboard & REST API

```bash
uvicorn calibrator.main:app --host 0.0.0.0 --port 8008
```
Open [http://localhost:8008](http://localhost:8008) in your browser to inspect the interactive Pareto frontier curve and contrast pairs.

### 4. Run with Docker Compose

```bash
docker compose up --build
```

---

## 🔬 Test Suite Verification

```bash
pytest -v
```

```text
============================= 21 passed in 1.03s ==============================
```

---

## 🛡️ Responsible AI Disclosure

All contrast pairs in SafetyCalibrator focus on educational software architecture and enterprise engineering concepts. No actionable exploits or functional attack scripts are generated.
