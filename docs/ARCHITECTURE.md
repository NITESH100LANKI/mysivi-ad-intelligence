# Architecture & System Design
## MySivi Facebook Ad Intelligence & Creative Analysis System

```
+--------------------------------------------------------------------------------------------------+
|                                    END-TO-END PIPELINE ARCHITECTURE                              |
+--------------------------------------------------------------------------------------------------+

                                Meta / Facebook Ad Library
                                (Filtered: India, Active, MySivi)
                                             |
                                             v
                             Apify Facebook Ads Scraper Actor
                             (REST API POST /acts/.../runs)
                                             |
                                             v
                                Polling Run Completion
                                (GET /actor-runs/{id})
                                             |
                                             v
                                Fetch Raw Dataset Items
                                (JSON Array of Snapshot Objects)
                                             |
                                             v
                           n8n Data Cleaning & Normalization
                           (Duplicate Detection, Schema Validation)
                                             |
                                             v
                           Loop Over Normalized Ad Creatives
                                             |
                                             v
                                Google Gemini Multimodal AI
                                (14 Strategic Marketing Dimensions)
                                             |
                                             v
                              Structured JSON Parse & Repair
                                             |
                                             v
                             100-Point Scoring Engine (Rubric)
                                             |
                                             v
                            Creative Ranking & Top Ad Selection
                              ("Best Creative Advertisement")
                                             |
                                             v
                         Comparative Deep Dive & Recommendations
                          (Top 3 Comparison, 3 New Campaign Concepts)
                                             |
                                             v
                         Professional Executive PDF Generation
                           (ReportLab 16-Section Automated Report)
                                             |
                                             v
                       Master Deliverables & Execution Summary
                         [PDF Report + Workflow JSON + Results]
```

---

## 1. Core Architectural Pillars

### A. Modular Service Separation
1. **Orchestration Layer:** Self-hosted n8n Community Edition handles lifecycle triggers, parameterization, looping, branching, error isolation, and notifications.
2. **Scraping Layer:** Apify Facebook Ads Library Scraper actor collects authentic ad creatives without bypassing bot protections or risking account bans.
3. **Cognitive AI Layer:** Google Gemini 1.5 Flash accessed via Google AI Studio API performs deep marketing analysis across 14 psychological and strategic dimensions with pure JSON schema enforcement.
4. **Scoring Engine:** Deterministic, mathematical evaluation based on an 8-criterion 100-point rubric, ensuring 100% reproducible results.
5. **Reporting Layer:** Python ReportLab engine rendering an 8-page, 16-section executive corporate PDF report.

### B. Dual-Mode Execution (Live vs. Mock)
The system is built with zero-lock-in dual-mode capability:
- **`EXECUTION_MODE=live`:** Calls live Apify REST API and live Google Gemini API endpoints.
- **`EXECUTION_MODE=mock`:** Utilizes validated local fixtures (`data/fixtures/sample_mysivi_raw_ads.json`) and deterministic heuristic analysis. This allows full offline verification, development, and unit testing without consuming API credits or exposing credentials.

---

## 2. Component Directory Structure

```
mysivi-ad-intelligence/
├── n8n/
│   └── mysivi_ad_intelligence_workflow.json      # Deliverable 2: Complete importable workflow
├── backend/
│   ├── scraper/
│   │   └── apify_client.py                       # Apify Actor API integration & polling
│   ├── analysis/
│   │   ├── gemini_client.py                      # Google Gemini API client & error isolation
│   │   └── prompt_builder.py                     # 14-dimension structured prompt templates
│   ├── scoring/
│   │   ├── scoring_engine.py                     # Mathematical 100-pt rubric evaluator
│   │   └── ranker.py                             # Ranking, top 3 comparison, 3 new ad concepts
│   ├── report/
│   │   ├── pdf_generator.py                      # ReportLab 16-section corporate PDF builder
│   │   └── report_service.py                     # HTTP Microservice (port 5000) for n8n
│   └── utils/
│       ├── config.py                             # Typed settings & environment management
│       ├── logger.py                             # Structured logging with secret masking
│       ├── normalizer.py                         # Text cleaning, hook extraction, deduplication
│       └── validator.py                          # Pydantic v2 schemas across all stages
├── data/
│   ├── raw/                                      # Scraped raw JSON snapshots
│   ├── processed/                                # Cleaned & normalized ad records
│   ├── results/                                  # Master analysis results JSON
│   └── fixtures/                                 # Offline test fixtures
├── reports/
│   └── MySivi_Ad_Intelligence_Report.pdf         # Deliverable 1: Generated PDF Report
├── tests/
│   ├── test_normalizer.py                        # Unit tests for deduplication & cleaning
│   ├── test_scoring.py                           # Mathematical verification of rubric
│   ├── test_ranking.py                           # Ranking & comparative logic tests
│   ├── test_gemini.py                            # AI prompt & schema validation tests
│   ├── test_pdf.py                               # PDF structure & header verification
│   └── test_end_to_end.py                        # Full end-to-end pipeline test
├── docs/
│   ├── ARCHITECTURE.md                           # System design & component specification
│   ├── API_SETUP.md                              # Step-by-step free API credentials guide
│   ├── WORKFLOW_GUIDE.md                         # n8n node-by-node operations manual
│   ├── SCORING_METHODOLOGY.md                    # Explanation of the 100-pt rubric
│   ├── TESTING.md                                # Testing protocols & verification output
│   └── LOOM_DEMO_SCRIPT.md                       # Deliverable 3: 10-step Loom script
├── docker-compose.yml                            # Local container orchestration
├── Dockerfile                                    # PDF reporting service container
├── .env.example                                  # Environment variables template
├── .gitignore                                    # Secrets & build artifact exclusions
├── requirements.txt                              # Python production dependencies
├── run_pipeline.py                               # CLI master pipeline runner
├── run_local.ps1                                 # One-click Windows PowerShell starter
└── README.md                                     # Executive summary & quickstart guide
```

