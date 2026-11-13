# Free API Credentials & Setup Guide
## MySivi Ad Intelligence & Creative Analysis System

This system uses **100% free-tier services**. No paid subscriptions, credit card requirements, or billing accounts are required to run the full pipeline.

---

## 1. Google Gemini API Key (Free)

Google AI Studio provides generous free-tier API access to Gemini 1.5 Flash and Gemini 2.0.

### Step-by-Step Instructions:
1. Visit **Google AI Studio**: [https://aistudio.google.com/](https://aistudio.google.com/)
2. Sign in with your Google account.
3. Click the blue button labeled **"Get API key"** in the left navigation sidebar.
4. Click **"Create API key in new project"** (or select an existing Google Cloud project).
5. Copy the generated API key (format: `AIzaSy...`).
6. Open your local `.env` file and set:
   ```env
   GOOGLE_GEMINI_API_KEY=AIzaSyYourGeneratedGeminiKeyHere
   GEMINI_MODEL=gemini-1.5-flash
   ```

*Free Tier Quotas:*
- Gemini 1.5 Flash: 15 Requests Per Minute (RPM), 1,500 Requests Per Day (RPD), 1 Million Tokens Per Minute (TPM).
- Generously sufficient for analyzing 15–20 ads in seconds.

---

## 2. Apify API Token (Free)

Apify provides a monthly free-tier usage allowance ($5.00/month recurring free credit) with zero credit card needed.

### Step-by-Step Instructions:
1. Visit **Apify Console**: [https://console.apify.com/](https://console.apify.com/)
2. Sign up for a free account (using GitHub or Google).
3. Navigate to **Settings** > **Integrations** (or [https://console.apify.com/account/integrations](https://console.apify.com/account/integrations)).
4. Under the **API tokens** section, copy your **Personal API token** (format: `apify_api_...`).
5. Open your local `.env` file and set:
   ```env
   APIFY_API_TOKEN=apify_api_YourPersonalTokenHere
   APIFY_ACTOR_ID=apify/facebook-ads-scraper
   ```

---

## 3. Configuring Credentials in n8n

When running n8n locally:
1. Open the local n8n interface at `http://localhost:5678`.
2. The workflow is configured to read environment variables directly (`$env.GOOGLE_GEMINI_API_KEY` and `$env.APIFY_API_TOKEN`).
3. Alternatively, you can configure n8n Header Auth or query credentials for Apify and Gemini if you prefer storing them in n8n's internal credential vault.
4. In `.env`, switch execution mode to live:
   ```env
   EXECUTION_MODE=live
   ```
5. Click **"Execute Workflow"** in n8n.

