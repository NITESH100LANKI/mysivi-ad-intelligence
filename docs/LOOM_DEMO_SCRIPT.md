# Loom Video Demonstration Script & Recording Guide
## Project: MySivi Ad Intelligence & Creative Analysis System
### Prepared for: MySivi Growth Internship Assignment Evaluation

> **NOTE FOR THE APPLICANT:**
> This comprehensive, step-by-step presentation script is prepared for you to record your official Loom demonstration. You will record the video yourself using Loom, screen-sharing the n8n workflow and the generated PDF report. Do not claim an AI assistant recorded the video. Follow this timed script to deliver a polished, high-impact presentation that stands out to the engineering and growth leadership.

---

## Video Specifications & Setup Checklist

- **Target Duration:** 5 to 7 minutes.
- **Microphone & Camera:** Clear desktop audio with applicant webcam bubble enabled in the lower corner.
- **Pre-Recording Browser Tabs to Have Open:**
  1. **Tab 1:** Local n8n interface (`http://localhost:5678`) with `MySivi Facebook Ad Intelligence & Creative Strategy Pipeline` imported and opened on canvas.
  2. **Tab 2:** PDF viewer displaying `reports/MySivi_Ad_Intelligence_Report.pdf`.
  3. **Tab 3:** Official Meta Ad Library target URL for MySivi:
     `https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=IN&is_targeted_country=false&media_type=all&q=%22MySivi%22&search_type=keyword_exact_phrase&sort_data[mode]=total_impressions&sort_data[direction]=desc`
  4. **Tab 4 (Optional):** VS Code / IDE showing `data/results/mysivi_analysis_results.json` and the test suite passing.

---

## 10-Step Timed Presentation Script

```
+-----------------------------------------------------------------------------------------+
| TOTAL RUNTIME: ~6 MINUTES                                                               |
| [0:00 - 0:45] Step 1 & 2: Introduction & Business Problem                                |
| [0:45 - 1:45] Step 3 & 4: n8n Architecture & Apify Collection                           |
| [1:45 - 2:45] Step 5 & 6: Google Gemini AI Analysis & 100-Point Scoring Engine          |
| [2:45 - 3:45] Step 7: Live Workflow Execution Demonstration                             |
| [3:45 - 5:00] Step 8 & 9: PDF Deep Dive & Why the Winner Won                            |
| [5:00 - 6:00] Step 10: Strategic Recommendations, Limitations & Business Conclusion     |
+-----------------------------------------------------------------------------------------+
```

---

### Step 1: Project Introduction (0:00 - 0:25)
* **Visual on Screen:** Face cam + Project title screen or n8n Canvas.
* **Spoken Script:**
  > *"Hi team! My name is [Your Name], and today I am excited to present the end-to-end MySivi Ad Intelligence and Creative Analysis System that I built for the MySivi Growth Internship assignment.*
  >
  > *This system is a production-minded, fully automated creative intelligence pipeline that continuously monitors Meta Ad Library, normalizes advertising copy, uses Google Gemini multimodal AI to deconstruct marketing psychology, and algorithmically ranks the strongest creatives using an explainable 100-point rubric."*

---

### Step 2: The Business Problem (0:25 - 0:45)
* **Visual on Screen:** Switch tab to Meta Ad Library showing MySivi ads.
* **Spoken Script:**
  > *"Growth teams and performance marketers constantly struggle with creative fatigue and competitor blind spots. Manually auditing competitors' ad libraries is slow, subjective, and unstructured. Meta Ad Library exposes public creatives, but without conversion or sales data, marketing teams often guess which angles actually resonate.*
  >
  > *Our goal was to build a zero-cost, enterprise-grade automated workflow that ingests real MySivi ad creatives, extracts hooks, headlines, and CTAs, applies deep cognitive analysis, and outputs a professional 16-section executive PDF report automatically."*

---

### Step 3: End-to-End n8n Architecture (0:45 - 1:15)
* **Visual on Screen:** Switch tab to n8n canvas. Pan smoothly across the 18 nodes from left to right.
* **Spoken Script:**
  > *"Here is the complete n8n workflow. It is orchestrated across seven distinct phases:*
  > 1. *First, the **Manual Trigger** and **Init Configuration** where parameters like search keywords, country code (India), and execution limits are initialized.*
  > 2. *Second, the **Apify Actor Ingestion** branch that calls the Facebook Ad Library scraper.*
  > 3. *Third, our **Data Cleaning and Deduplication** Code node that extracts hooks and filters out duplicate ad IDs and identical copy hashes.*
  > 4. *Fourth, a **Loop Over Items** structure that passes each creative to Google Gemini.*
  > 5. *Fifth, the **AI Extraction and Validation** node that parses 14 marketing dimensions into strict structured JSON.*
  > 6. *Sixth, our mathematical **Scoring Engine** that calculates weighted creative quality scores.*
  > 7. *And finally, an automated HTTP request to our local reporting microservice that compiles and renders the PDF report."*

---

### Step 4: Apify Facebook Ad Library Scraping (1:15 - 1:45)
* **Visual on Screen:** Zoom in on the Apify nodes and the Mock Ingestion stream.
* **Spoken Script:**
  > *"For data collection, we integrate with Apify's official Facebook Ads Scraper actor. The workflow sends the exact search URL filtered for India and active ads.*
  >
  > *Notice that we engineered a resilient dual-stream architecture: when live Apify tokens are configured, it triggers the live actor run, polls for completion, and streams the dataset. If tokens are not provided, or during offline testing, it gracefully routes to our validated local fixture stream. This guarantees complete pipeline reliability with zero chance of unexpected API bills."*

---

### Step 5: Google Gemini Multimodal AI Analysis (1:45 - 2:15)
* **Visual on Screen:** Open the 'Call Google Gemini AI' node and the 'Validate & Structure Ad Analysis' node.
* **Spoken Script:**
  > *"Next is the AI cognitive layer powered by Google Gemini 3.8 Flash (`gemini-3.8-flash`) via Google AI Studio's free tier. For each advertisement, Gemini analyzes the creative across 14 dedicated dimensions—including Hook stopping power, Headline clarity, Target Audience inference, Customer Pain Points, Value Proposition, USP, and Persuasion Techniques.*
  >
  > *We enforce a strict JSON schema with temperature 0.2, type coercion, and isolated per-ad error handling with automatic fallback to Gemini 2.5 Flash if demand spikes occur, meaning transient external timeouts will never crash the overall pipeline."*

---

### Step 6: 100-Point Scoring Engine & Ranking (2:15 - 2:45)
* **Visual on Screen:** Open the 'Score, Rank & Synthesize Intelligence' Code node and highlight the scoring weights.
* **Spoken Script:**
  > *"To rank creatives objectively, we implemented an explainable 100-point rubric. The weights reflect true performance marketing impact:*
  > - *Hook Effectiveness: 20 points (the single biggest factor in feed stopping power).*
  > - *Message Clarity & Value Proposition: 15 points each.*
  > - *Target Audience, Trust & Social Proof, CTA, Creative Execution, and Differentiation: 10 points each.*
  >
  > *Importantly, trust is scored conservatively: an ad doesn't receive 10/10 just for making bold claims unless verifiable evidence or social proof is present.*
  >
  > *Furthermore, we built an evidence-based tie-breaking hierarchy: if two ads have identical composite scores, the system breaks ties secondary to Hook Stopping Power (20%), then Value Proposition (15%). If both creatives display genuine vernacular parity, the system declares them Joint Rank 1 Co-Winners rather than inventing an arbitrary preference."*

---

### Step 7: Live Workflow Execution Demonstration (2:45 - 3:45)
* **Visual on Screen:** Click 'Test workflow' / 'Execute Workflow' button in n8n. Watch nodes turn green in real-time.
* **Spoken Script:**
  > *"Now let's watch the workflow execute live. I click 'Test workflow'...*
  >
  > *[Pause 3 seconds as nodes execute]*
  >
  > *Notice how cleanly data flows through: the configuration sets our parameters, our dataset replay path loads the 10 raw records previously collected from Meta Ad Library via Apify (Run ID rj6SNnqt6EZKwY6d9, Dataset ID EITwCgU3aub104ezB) at zero additional credit cost, the normalizer cleans whitespace and eliminates 6 duplicate collations, leaving 4 unique advertisements.*
  >
  > *The loop passes each ad creative individually to Google Gemini 3.8 Flash, which analyzes the creative across 14 dimensions. The results aggregate, scores and tie-breakers are calculated, and the final PDF generation endpoint is triggered. Execution completes reliably with full traceability!"*

---

### Step 8: PDF Report Deep Dive (Deliverable 1) (3:45 - 4:20)
* **Visual on Screen:** Switch to the generated PDF (`reports/MySivi_Ad_Intelligence_Report.pdf`). Scroll through the cover page, executive summary, and ad registry table.
* **Spoken Script:**
  > *"Here is Deliverable 1: our generated executive PDF report. It is an 8-page, 16-section corporate-grade document generated via ReportLab with dynamic running headers and 'Page X of Y' numbering.*
  >
  > *In Section 4, you can see our live Meta Ad Library findings for MySivi in India: the active campaigns focus on an AI-powered English speaking and learning companion targeting regional language speakers across Hindi, Marathi, Bengali, and Kannada with an irresistible ₹1 trial offer.*
  >
  > *In Section 5, our 100-point rubric methodology is fully documented, followed by a head-to-head comparison of the top creatives."*

---

### Step 9: Why the Winning Creative Outperformed the Rest (4:20 - 5:00)
* **Visual on Screen:** Zoom in on Section 7: 'Best Creative Advertisement Deep Dive' and the top comparison table.
* **Spoken Script:**
  > *"Now let's examine the winning creatives. In our live Meta ad set, two regional creatives achieved standout scores of 81.0 out of 100: MYSIVI-AD-003 ('MySivi सोबत सुरुवात करा – केवळ ₹1 मध्ये' in Marathi) and MYSIVI-AD-004 ('₹1 theke English start korun' in Bengali).*
  >
  > *Why did these vernacular ads outperform the English ads?*
  > 1. *First, their Hooks: MYSIVI-AD-003 uses an emotional relief hook ('हुशारीनं शिका, कष्ट न करता!' — 'Learn smart, without struggle!') while MYSIVI-AD-004 uses a practical comfort hook ('AI teacher apnake Bangla te English bujhiye debe'). Both combine immediate cultural stopping power with a hyper-low-friction ₹1 entry offer.*
  > 2. *Second, their Value Proposition is localized: they promise that an AI tutor will guide the user in their mother tongue, dismantling the intimidation of conventional English classes.*
  > 3. *Third, their CTA 'Install Now' points directly to the app store, driving frictionless user acquisition.*
  >
  > *Our scoring engine recognized this vernacular parity, celebrating mother-tongue localization as MySivi's strongest acquisition asset while identifying key vulnerabilities like the absence of verified student video testimonials."*

---

### Step 10: Strategic Recommendations & Conclusion (5:00 - 6:00)
* **Visual on Screen:** Scroll to Section 9 (Suggested New Marketing Concepts) and Section 10 (Limitations).
* **Spoken Script:**
  > *"Based on the gaps identified in MySivi's live ad set, we formulated three innovative campaign concepts ready to launch:*
  > 1. *Concept 1: A 'Job Interview Anxiety' before-and-after UGC video ad showing a regional graduate practicing mock interviews with Sivi AI and gaining fluency.*
  > 2. *Concept 2: A 'Mother Tongue to Fluency' carousel showing how Sivi switches seamlessly between Marathi, Hindi, and Bengali explanations.*
  > 3. *Concept 3: A '₹1 Daily Speaking Challenge' interactive story ad creating a daily gamified speaking habit.*
  >
  > *In Section 10, we transparently disclose limitations: Meta Ad Library does not expose private in-app conversion or ROAS data, so our rankings measure Creative Quality rather than empirical revenue attribution.*
  >
  > *All three deliverables—the PDF report generated from real live Meta data, the validated n8n workflow JSON, and this presentation guide—are committed in the workspace alongside automated unit tests. Thank you for your time, and I look forward to contributing to MySivi's growth!"*

---

## Technical Appendix & Frequently Asked Questions

**Q: What if n8n gives a timeout on Apify scraping?**
> A: The workflow features built-in polling with an automatic fallback to validated fixtures, ensuring the demonstration never stalls during a live presentation.

**Q: Where can the interviewer find the exported workflow?**
> A: The complete workflow JSON is located at `n8n/mysivi_ad_intelligence_workflow.json` and can be imported directly into any n8n instance via 'Import from File'.

