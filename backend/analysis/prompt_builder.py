"""Prompt engineering templates for Google Gemini AI Creative Analysis."""
import json
from typing import Dict, Any
from ..utils.validator import NormalizedAd

GEMINI_SYSTEM_INSTRUCTION = """You are a Principal Creative Strategist, Performance Marketing Director, and AI Ad Intelligence Expert.
Your task is to conduct an in-depth, rigorous, and evidence-based creative analysis of Facebook advertisements for MySivi (sivi.ai), an AI generative design platform.

CRITICAL GUIDELINES:
1. Base your analysis solely on the actual advertising copy, headline, CTA, and creative metadata provided.
2. Label target audience descriptions explicitly as inferences.
3. Be objective: Identify genuine creative strengths and weaknesses. Do not award high trust or proof scores to unverified claims.
4. Output MUST BE valid, parseable JSON conforming strictly to the requested schema. No surrounding markdown codeblocks (no ```json). Pure JSON only.
5. If visual/video media is not directly readable in your context, perform thorough text-based creative analysis and explicitly identify that limitation in media_analysis_notes.
"""


def build_ad_analysis_prompt(ad: NormalizedAd) -> str:
    """Generate the user prompt instructing Gemini to analyze the ad across all 14 dimensions and 8 rubric metrics."""
    ad_dict = {
        "internal_id": ad.internal_id,
        "ad_id": ad.ad_id,
        "page_name": ad.page_name,
        "extracted_hook": ad.hook,
        "primary_text": ad.primary_text,
        "headline": ad.headline,
        "description": ad.description,
        "call_to_action": ad.cta,
        "landing_page_url": ad.landing_page_url,
        "media_type": ad.media_type,
        "publisher_platforms": ad.publisher_platforms,
        "image_urls": ad.image_urls[:2],
        "video_urls": ad.video_urls[:1]
    }

    prompt = f"""Analyze the following Facebook Advertisement for MySivi:

ADVERTISEMENT METADATA AND COPY:
{json.dumps(ad_dict, indent=2)}

You must return a single JSON object with EXACTLY the following structure:
{{
  "hook": "The opening attention-grabbing statement or opening creative message.",
  "body": "The complete advertising message and sales pitch.",
  "headline": "The main advertisement headline.",
  "cta": "Actual call-to-action found, or 'Unavailable'.",
  "target_audience": "Likely intended customer segment (Explicitly state this is an inference).",
  "customer_pain_point": "Core problem the advertisement attempts to solve.",
  "value_proposition": "Main customer benefit delivered by MySivi.",
  "usp": "Unique selling point that sets MySivi apart.",
  "marketing_angle": "Primary marketing angle (e.g. problem-solution, cost-saving, speed/efficiency, anti-template differentiation, creative fatigue).",
  "persuasion_techniques": "Specific persuasion techniques utilized (e.g. contrast framing, loss aversion, quantifiable time-savings).",
  "strengths": [
    "Specific compelling element 1",
    "Specific compelling element 2",
    "Specific compelling element 3"
  ],
  "weaknesses": [
    "Specific creative vulnerability or missing element 1",
    "Specific creative vulnerability or missing element 2"
  ],
  "improvement_suggestions": [
    "Actionable, high-impact recommendation 1",
    "Actionable, high-impact recommendation 2"
  ],
  "creative_summary": "Concise 2-sentence synthesis of the creative strategy.",
  "media_analysis_notes": "Note on creative format, visual composition implications, and analysis mode.",
  "rubric_scores": {{
    "hook_effectiveness": 8.5,
    "message_clarity": 9.0,
    "value_prop_usp": 8.0,
    "target_audience_relevance": 8.5,
    "trust_social_proof": 6.0,
    "cta_effectiveness": 7.5,
    "creative_execution": 8.0,
    "differentiation": 8.5
  }},
  "rubric_explanations": {{
    "hook_effectiveness": "Why this score (0-10) was assigned based on stopping power and relevance.",
    "message_clarity": "Why this score (0-10) was assigned based on readability and core offer.",
    "value_prop_usp": "Why this score (0-10) was assigned based on clear customer benefit vs competitors.",
    "target_audience_relevance": "Why this score (0-10) was assigned based on resonant messaging to the ICP.",
    "trust_social_proof": "Why this score (0-10) was assigned based on verifiable proof, metrics, or testimonials (score strictly!).",
    "cta_effectiveness": "Why this score (0-10) was assigned based on urgency, friction, and clarity.",
    "creative_execution": "Why this score (0-10) was assigned based on copy rhythm, format match, and positioning.",
    "differentiation": "Why this score (0-10) was assigned based on standing out from generic design tools."
  }}
}}

Remember: Return ONLY the JSON object. Do not wrap in markdown or backticks.
"""
    return prompt

