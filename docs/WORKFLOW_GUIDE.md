# n8n Workflow Guide & Node Operations Manual (v6)
## MySivi Facebook Ad Intelligence & Creative Strategy Automation

This manual details the architecture, node configurations, data contracts, loop mechanics, execution routing, and error handling for `n8n/mysivi_ad_intelligence_workflow_v6.json`.

---

## 1. Workflow Architecture Map (v6)

```
[1. Manual Trigger] 
       |
       v
[2. Init Configuration] (REPORT_SERVICE_URL: http://report-service:5000)
       |
       v
[3. Execution Mode Router (Switch v3)]
      /                 |                  \
  (live)         (dataset_replay)         (mock / fallback)
    v                   |                  v
[4. Apify Start]        |           [8. Load Mock / Fixture Data]
    |                   |                  |
    v                   |                  |
[5. Wait 10s]           |                  |
    |                   |                  |
    v                   |                  |
[6. Poll Status]        |                  |
    |                   |                  |
    v                   v                  |
[7. Fetch Apify Dataset Items]             |
      \                                    /
       v                                  v
    [9. Merge Ingestion Streams (Mode: Append)]
                |
                v
    [10. Clean, Normalize & Deduplicate]
                |
                v
    [11. Loop Over Ad Creatives (Batch: 1)] <----------------------+
         |                        | (Loop Branch - Output 1)       |
         | (Done Branch - Out 0)  v                                |
         v            [12. Has Key?]                               |
    [16. Aggregate]           /     \                              |
         |                (True)   (False)                         |
         v                  v         v                            |
    [17. Validate Input] [13. AI]  [14. Heur]                      |
         |                  \         /                            |
         v                   v       v                             |
    [18. Score & Rank]   [15. Validate Analysis] ──────────────────┘
         |
         v
    [19. Trigger PDF Report Generation] (http://report-service:5000/generate-report)
         |
         v
    [20. Final Execution Summary]
```

> [!IMPORTANT]
> **Docker Service-to-Service Networking & Scoring Routing in v6:**
> 1. **PDF Service URL**: Within Docker Compose (`mysivi-network`), services communicate via service name DNS. Node 19 connects to `http://report-service:5000/generate-report` (never `localhost:5000` or `::1:5000`).
> 2. **Scoring Input Ingestion**: Node 18 (`Score, Rank & Synthesize Intelligence`) directly ingests `$input.all()` from Node 17 (`Validate Scoring Input`), ensuring all 4 validated advertisements are scored and ranked.
> 3. **Execution Summary Integrity**: Node 20 verifies both scoring success (`ads_analyzed >= 4`) and PDF generation (`pdf_generated: true`), accurately returning `SUCCESS`, `PARTIAL_FAILURE`, or `FAILED`.

> [!IMPORTANT]
> **n8n Loop Over Items (SplitInBatches v3) Output Indexing:**
> In modern n8n v2.47.5, `splitInBatches` v3 uses:
> - **Output Index 0 = DONE**: Emitted once all batches complete. Connected directly to `Aggregate Validated Advertisements`.
> - **Output Index 1 = LOOP**: Emitted for each batch item. Connected to `Has Gemini API Key?`.
> - **Input Index 0 = Feedback**: Emitted by `Validate & Structure Ad Analysis` back to `Loop Over Ad Creatives`.

---

## 2. Normalized Data Contract (v4)

Every analyzed advertisement emitted by `Validate & Structure Ad Analysis` and passed to `Aggregate Validated Advertisements` strictly adheres to this contract:

```json
{
  "internal_id": "MYSIVI-AD-001",
  "ad_id": "946551737840774",
  "headline": "MySivi Se Shuru Karo – Sirf ₹1 Mein",
  "primary_text": "Speak English fluently with the power of AI! ...",
  "hook": "Speak English fluently with the power of AI!",
  "body": "Speak English fluently with the power of AI! ...",
  "cta": "Install now",
  "analysis": {
    "hook": {
      "score": 8.5,
      "explanation": "High stopping power with low-friction ₹1 anchor."
    },
    "message_clarity": {
      "score": 9.0,
      "explanation": "Crystal clear value proposition."
    },
    "value_prop_usp": {
      "score": 8.0,
      "explanation": "Mother-tongue conversational AI tutor."
    },
    "target_audience": {
      "score": 8.5,
      "explanation": "Targeted at Tier 2/3 Indian regional language learners."
    },
    "trust_social_proof": {
      "score": 6.0,
      "explanation": "Low financial risk builds initial trial trust."
    },
    "cta_effectiveness": {
      "score": 7.5,
      "explanation": "Direct Install now CTA."
    },
    "creative_execution": {
      "score": 8.0,
      "explanation": "Strong localized vernacular headline."
    },
    "differentiation": {
      "score": 8.5,
      "explanation": "Combines conversational AI with ₹1 price barrier."
    },
    "customer_pain_point": "Hesitation speaking English and expensive classroom tutoring.",
    "value_proposition": "Private, AI-guided English speaking practice for ₹1.",
    "usp": "Localized regional language support at ₹1",
    "marketing_angle": "Low-Barrier ₹1 Trial & Regional Language Support",
    "persuasion_techniques": "₹1 micro-trial price anchoring and mother-tongue comfort.",
    "strengths": ["Compelling ₹1 trial stopping power", "Localized regional reassurance"],
    "weaknesses": ["Lacks student video testimonials in ad copy"],
    "improvement_suggestions": ["Add student video testimonials"],
    "creative_summary": "Direct acquisition ad targeting Indian learners."
  },
  "ad": {
    "internal_id": "MYSIVI-AD-001",
    "headline": "MySivi Se Shuru Karo – Sirf ₹1 Mein",
    "hook": "Speak English fluently with the power of AI!",
    "cta": "Install now"
  }
}
```

---

## 3. Dedicated Aggregation, Scoring & Report Generation (v6)

### A. Aggregate Validated Advertisements (Node 16)
- **Role:** Connects exclusively to the **DONE output (Output 0)** of `Loop Over Ad Creatives`.
- **Mechanics:** Directly consumes `$input.all()` from the loop's Done output, which carries the completed results from all loop iterations.
- **Deduplication & Verification:** Deduplicates by `internal_id`, confirms that all received items contain a normalized `analysis` object and core fields, and asserts that exactly 4 unique records are present.
- **Output:** Exactly 4 normalized advertisement records.

### B. Validate Scoring Input (Node 17)
- **Role:** Strict gatekeeper between aggregation and scoring.
- **Verifications:**
  1. Exactly 4 unique advertisement records are present.
  2. All records contain an `analysis` object.
  3. All 8 weighted scoring dimensions exist.
  4. Each score is numeric and between 0 and 10.
  5. Zero duplicate advertisements exist.
  6. Throws a clear descriptive error if any condition fails.

### C. Score, Rank & Synthesize Intelligence (Node 18)
- Receives guaranteed clean, validated items directly from Node 17 via `$input.all()`.
- Analyzes and scores all 4 advertisements.
- Evaluates the mathematical 100-point rubric.
- Executes Olympic competition ranking (Joint Rank 1 for `MYSIVI-AD-001`, `003`, `004` at 81.0; Rank 4 for `002` at 6.0).
- Packages comparison, rankings, and strategic recommendations.

### D. Trigger PDF Report Generation (Node 19)
- Connected to `http://report-service:5000/generate-report`.
- Retains `onError: continueRegularOutput` so error details (if any) are forwarded to the summary node rather than unhandled workflow aborts.

### E. Final Execution Summary (Node 20)
- Computes `ads_analyzed` from `master.rankings.length` (guaranteed 4).
- Populates `pdf_generated` as a strict boolean.
- Maps all four ranked advertisements (`internal_id`, `headline`, `rank`, `score`).
- Emits execution status:
  - `SUCCESS`: 4 ads analyzed and PDF report generated.
  - `PARTIAL_FAILURE`: 4 ads analyzed, but PDF service returned an error.
  - `FAILED`: critical analysis or scoring stages aborted.

| Mode | Trigger Condition | Execution Flow | Cost |
| :--- | :--- | :--- | :---: |
| **`live`** | `EXECUTION_MODE == 'live'` | Start Apify Actor (`apify/facebook-ads-scraper`) $\to$ Wait 10s $\to$ Poll Status $\to$ Fetch Dataset Items | Billable (Safeguard limit $0.10) |
| **`dataset_replay`** | `EXECUTION_MODE == 'dataset_replay'` | Directly GET `https://api.apify.com/v2/datasets/EITwCgU3aub104ezB/items` without starting a new scraper run | **$0.00 (Zero Scraping Cost)** |
| **`mock`** | `EXECUTION_MODE == 'mock'` (or fallback) | Load local validated fixtures from `Load Mock / Fixture Data` | **$0.00 (Offline)** |

All branches converge into `Merge Ingestion Streams` with `mode: "append"`, ensuring no accidental multiplexing or Cartesian joins occur.

---

## 4. Root Cause Analysis: The Missing Fourth Advertisement

### Investigation Summary
- **Original Dataset (`raw_ads_live_20261112_163334.json` / Dataset ID `EITwCgU3aub104ezB`):** Contains **10 raw placements** that normalize into **4 unique advertisements**:
  1. `946551737840774` (Hindi: *"MySivi Se Shuru Karo – Sirf ₹1 Mein"*)
  2. `1843111363320189` (Malformed Dynamic Creative Template: `"{{product.name}}"`, `"{{product.brand}}"`)
  3. `2966208700429750` (Marathi: *"MySivi सोबत सुरुवात करा – केवळ ₹1 मध्ये"*)
  4. `2823814924671305` (Bengali: *"₹1 theke English start korun"*)
- **Why Previous Execution Produced 3 Ads:**
  1. `Load Mock / Fixture Data` in workflow v1 hardcoded only **3 advertisements**, omitting `1843111363320189`.
  2. When `Fetch Apify Dataset Items` was called in an environment without `APIFY_API_TOKEN` or with network isolation, it received HTTP 403 Forbidden.
  3. Because `Fetch Apify Dataset Items` had `onError: continueErrorOutput`, the error branch routed into `Load Mock / Fixture Data`.
  4. `Load Mock / Fixture Data` emitted its 3 items into `Clean, Normalize & Deduplicate`, resulting in `Clean, Normalize & Deduplicate: 3 items`.
- **Resolution in v2/v3:**
  - `Load Mock / Fixture Data` has been updated with the authentic fourth advertisement (`1843111363320189`) directly from the verified Apify dataset.
  - `Heuristic Mock Analyzer` detects unparsed template variables (`{{`) and assigns the appropriate penalty score (6.0), exactly matching the canonical Gemini evaluation.
  - Both live dataset replay and mock fixture modes now consistently produce all **4 unique advertisements**.

---

## 5. How to Import and Run the Workflow in n8n

1. Start your local n8n instance:
   ```powershell
   docker compose up -d
   ```
   *(Or run `npx n8n`)*
2. Open your browser to `http://localhost:5678`.
3. In the left navigation bar, click **"Workflows"**.
4. Click **"Add Workflow"** $\to$ click the **"..." (More Options)** menu in the top right.
5. Select **"Import from File"** and choose:
   `c:\FacebookAdsAnalysier\n8n\mysivi_ad_intelligence_workflow_v6.json`
6. Verify node configurations:
   - `Init Configuration` sets `REPORT_SERVICE_URL: http://report-service:5000`.
   - `Trigger PDF Report Generation` targets `http://report-service:5000/generate-report`.
   - Loop branch (Output 1) routes to `Has Gemini API Key?`.
   - Feedback routes from `Validate & Structure Ad Analysis` to `Loop Over Ad Creatives` input.
   - Done branch (Output 0) routes to `Aggregate Validated Advertisements` $\to$ `Validate Scoring Input` $\to$ `Score, Rank & Synthesize Intelligence` $\to$ `Trigger PDF Report Generation` $\to$ `Final Execution Summary`.
7. Configure `Init Configuration` node:
   - To replay the collected dataset at zero cost, ensure `EXECUTION_MODE` is `"dataset_replay"`.
   - To run completely offline, set `EXECUTION_MODE` to `"mock"`.
8. Click **"Save"**, then click **"Test workflow"** to execute.
