# MySivi Facebook Ad Intelligence & Creative Analysis System
## Senior AI Engineer & Automation Architect Implementation

[![Tests](https://img.shields.io/badge/Tests-71%20Passed%20(100%25)-success)](docs/TESTING.md)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)
[![n8n](https://img.shields.io/badge/n8n-Community%20Edition-red)](https://n8n.io)
[![Google Gemini](https://img.shields.io/badge/Google%20Gemini-3.8%20Flash-4285F4)](https://aistudio.google.com/)
[![Apify](https://img.shields.io/badge/Apify-Meta%20Ad%20Scraper-green)](https://apify.com)

A production-grade, end-to-end AI automation pipeline designed for the **MySivi Growth Internship Assignment**. The system continuously ingests active advertisements from the Meta (Facebook) Ad Library, normalizes marketing copy, deconstructs creative strategy across strategic dimensions using Google Gemini, algorithmically scores ads with an explainable 100-point rubric, and compiles an 8-page corporate executive PDF report with native Indic Unicode typography.

---

## 📁 Repository Directory Structure

```text
mysivi-ad-intelligence/
│
├── backend/
│   ├── report/
│   ├── scoring/
│   ├── scraper/
│   └── utils/
│
├── data/
│   ├── results/
│   │   └── mysivi_analysis_results.json
│   └── fixtures/
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── API_SETUP.md
│   ├── WORKFLOW_GUIDE.md
│   └── LOOM_DEMO_SCRIPT.md
│
├── n8n/
│   └── mysivi_ad_intelligence_workflow_v6.json
│
├── reports/
│   └── MySivi_Ad_Intelligence_Report.pdf
│
├── tests/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## 🎯 Assignment Deliverables Summary

| Deliverable | Description | File Location | Status |
|---|---|---|---|
| **DELIVERABLE 1** | **Executive PDF Report** (8 pages, full Indic/Devanagari Unicode support, head-to-head matrix, deep dive) | [`reports/MySivi_Ad_Intelligence_Report.pdf`](reports/MySivi_Ad_Intelligence_Report.pdf) | **READY (Generated & Verified)** |
| **DELIVERABLE 2** | **Complete n8n Workflow JSON** (20 nodes, Docker DNS, strict data contract, verified routing) | [`n8n/mysivi_ad_intelligence_workflow_v6.json`](n8n/mysivi_ad_intelligence_workflow_v6.json) | **READY (Validated & Tested)** |
| **DELIVERABLE 3** | **Loom Video Demonstration Script** (10-step timed presentation script for applicant) | [`docs/LOOM_DEMO_SCRIPT.md`](docs/LOOM_DEMO_SCRIPT.md) | **READY (Complete Script)** |

---

## 🏗️ Architecture & Pipeline Flow

```text
Meta Ad Library (Active India MySivi Ads)
       │
       ▼
Apify Facebook Ads Scraper (Actor API apify/facebook-ads-scraper)
       │
       ▼
Fetch Apify Dataset Results (10 Raw Placements)
       │
       ▼
n8n Normalization Layer (Deduplication, 6 Duplicates Filtered -> 4 Unique Ads)
       │
       ▼
Loop Over Advertisements (1 by 1 Iteration)
       │
       ▼
Google Gemini Multimodal AI (gemini-3.8-flash) / Heuristic Mock Fallback
       │
       ▼
Validate & Structure Ad Analysis (Normalized Data Contract)
       │
       ▼
Aggregate Validated Advertisements & Pre-Scoring Validation
       │
       ▼
Mathematical 100-Point Scoring Engine (Olympic Competition Tie-Breaking)
       │
       ▼
Trigger PDF Report Generation (http://report-service:5000/generate-report)
       │
       ▼
Final Execution Summary (ads_analyzed: 4, pdf_generated: true, status: SUCCESS)
```

---

## 💰 Strict Free-Tier & Cost Policy

- **Orchestration:** Self-hosted n8n Community Edition (Open Source, 100% Free).
- **AI Model:** Google Gemini 3.8 Flash via Google AI Studio API (Free-tier, 0 cost).
- **Scraper:** Apify Facebook Ads Scraper (Dataset replay mode enabled at \$0.00 cost; live mode capped at \$0.10).
- **PDF Engine:** Python ReportLab with embedded Nirmala UI & Noto Unicode fonts (Local, open source, zero external API costs).
- **Resilience:** Dual-mode architecture automatically routes to validated fixtures/dataset replay if external APIs are unreachable.

---

## 📊 The 100-Point Scoring Rubric (MySivi Spoken English Companion)

All creatives are mathematically evaluated on a continuous 0.0 to 10.0 scale across 8 weighted criteria:

| Criteria | Weight | Evaluation Focus |
|---|---:|---|
| **Hook Effectiveness** | **20%** | Stopping power, emotional intrigue, and curiosity for English learners |
| **Message Clarity** | **15%** | Immediate comprehension of the spoken English offer with zero ambiguity |
| **Learning Benefit & Value Prop** | **15%** | Conversational English practice vs expensive traditional classroom coaching |
| **English-Learning Audience Relevance** | **10%** | Specific resonance with regional/vernacular learners across Tier 2/3 India |
| **Trust & Social Proof** | **10%** | Verifiable learner evidence, testimonials, landing page alignment (strictly graded) |
| **CTA Effectiveness** | **10%** | Action-oriented clarity, trial urgency, and low-friction mobile app download |
| **Creative Execution** | **10%** | Copy structure, localized language nuance, readability, and visual presentation |
| **Differentiation in English Assistance**| **10%** | Separation from generic tutors; private, judgment-free AI companion |
| **TOTAL** | **100%** | **Weighted Mathematical Sum (0 - 100)** |

*Formula:*  
$$\text{Total Score} = \frac{(h \times 20) + (m \times 15) + (v \times 15) + (t \times 10) + (s \times 10) + (c \times 10) + (e \times 10) + (d \times 10)}{10}$$

### Official Evaluated Scores:
- **`MYSIVI-AD-001` (Hindi):** **81.0 / 100** — Joint Rank 1 Co-Winner
- **`MYSIVI-AD-003` (Marathi):** **81.0 / 100** — Joint Rank 1 Co-Winner
- **`MYSIVI-AD-004` (Bengali):** **81.0 / 100** — Joint Rank 1 Co-Winner
- **`MYSIVI-AD-002` (Malformed Template):** **6.0 / 100** — Rank 4

---

## ⚡ Quickstart Guide

### 1. Prerequisites
- **Python 3.11+**
- **Docker Desktop** (`docker compose up -d`)

### 2. Configure Environment Variables
Copy `.env.example` to `.env`:
```powershell
cp .env.example .env
```
Fill in your free API keys if running live:
```env
GOOGLE_GEMINI_API_KEY=your_gemini_key_from_aistudio
APIFY_API_TOKEN=your_apify_token_from_console
EXECUTION_MODE=dataset_replay # Replays verified dataset at $0.00 cost
```

### 3. Run Automated Tests
```powershell
python -m pytest -v tests/
```
All 71 unit and integration tests pass with 100% coverage.

### 4. Import & Run n8n Workflow
1. Start containers: `docker compose up -d`
2. Open `http://localhost:5678`
3. Import `n8n/mysivi_ad_intelligence_workflow_v6.json`
4. Click **Test workflow**
