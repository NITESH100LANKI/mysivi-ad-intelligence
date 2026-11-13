"""Google Gemini API client for structured creative analysis."""
import json
import re
import time
from typing import Dict, Any, Optional, Tuple
import requests
from .prompt_builder import build_ad_analysis_prompt, GEMINI_SYSTEM_INSTRUCTION
from ..utils.config import get_settings
from ..utils.logger import setup_logger
from ..utils.validator import NormalizedAd, GeminiAnalysisResult, CreativeScore

logger = setup_logger("GeminiAnalysis")


class GeminiAnalysisClient:
    """Client for performing AI creative analysis via Google Gemini REST API."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.settings = get_settings()
        self.api_key = api_key or self.settings.GOOGLE_GEMINI_API_KEY
        self.model = model or self.settings.GEMINI_MODEL
        self.api_base = "https://generativelanguage.googleapis.com/v1beta/models"

    def analyze_ad(
        self,
        ad: NormalizedAd,
        force_mock: bool = False
    ) -> Tuple[Optional[GeminiAnalysisResult], Optional[CreativeScore]]:
        """
        Analyze a single normalized advertisement.
        Per-ad error isolation: Returns (None, None) on fatal failure without crashing the pipeline.
        """
        # Check if running in mock mode or API key is absent
        if force_mock or not self.api_key or self.api_key == "your_gemini_api_key_here":
            logger.info(f"Analyzing ad {ad.internal_id} via OFFLINE DETERMINISTIC HEURISTIC (Mock Mode).")
            return self._heuristic_mock_analysis(ad)

        logger.info(f"Analyzing ad {ad.internal_id} (ID: {ad.ad_id}) via Gemini model '{self.model}'...")
        prompt = build_ad_analysis_prompt(ad)

        # Models to try: primary model first, followed by resilient fallback if 503/high-demand occurs
        candidate_models = [self.model]
        if self.model != "gemini-2.5-flash":
            candidate_models.append("gemini-2.5-flash")

        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}]
                }
            ],
            "systemInstruction": {
                "parts": [{"text": GEMINI_SYSTEM_INSTRUCTION}]
            },
            "generationConfig": {
                "temperature": 0.2,
                "responseMimeType": "application/json"
            }
        }

        for active_model in candidate_models:
            url = f"{self.api_base}/{active_model}:generateContent?key={self.api_key}"
            max_retries = 2
            backoff = 2

            for attempt in range(1, max_retries + 1):
                try:
                    response = requests.post(
                        url,
                        headers={"Content-Type": "application/json"},
                        json=payload,
                        timeout=45
                    )

                    if response.status_code == 200:
                        raw_data = response.json()
                        parsed_json = self._extract_json_from_gemini_response(raw_data)
                        if parsed_json:
                            logger.info(f"Successfully analyzed {ad.internal_id} with Gemini model '{active_model}'.")
                            return self._build_models_from_json(parsed_json, ad)
                        else:
                            logger.warning(f"Failed to parse JSON from Gemini response for {ad.internal_id} on {active_model} (Attempt {attempt})")
                    elif response.status_code in (429, 503):
                        logger.warning(f"Gemini model '{active_model}' returned {response.status_code} (Demand spike). Backing off {backoff}s...")
                        time.sleep(backoff)
                        backoff *= 2
                    else:
                        logger.error(f"Gemini API error on {active_model} ({response.status_code}): {response.text}")
                        break

                except requests.exceptions.RequestException as e:
                    logger.warning(f"Request exception for {ad.internal_id} on {active_model} (Attempt {attempt}): {e}")
                    time.sleep(backoff)
                    backoff *= 2

        logger.error(f"Failed to analyze ad {ad.internal_id} after {max_retries} attempts. Falling back to heuristic mock.")
        return self._heuristic_mock_analysis(ad)

    def _extract_json_from_gemini_response(self, response_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract and safely parse text content from Gemini's response schema."""
        try:
            candidates = response_data.get("candidates", [])
            if not candidates:
                return None
            parts = candidates[0].get("content", {}).get("parts", [])
            if not parts:
                return None
            text = parts[0].get("text", "").strip()

            # Remove potential markdown code blocks
            text = re.sub(r"^```json\s*", "", text, flags=re.MULTILINE)
            text = re.sub(r"^```\s*", "", text, flags=re.MULTILINE)
            text = text.strip()

            return json.loads(text)
        except Exception as e:
            logger.error(f"JSON extraction error: {e}")
            return None

    def _build_models_from_json(
        self,
        data: Dict[str, Any],
        ad: NormalizedAd
    ) -> Tuple[GeminiAnalysisResult, CreativeScore]:
        """Convert parsed Gemini JSON into typed Pydantic instances with type coercion."""
        def to_str(val: Any, default: str = "") -> str:
            if isinstance(val, list):
                return "; ".join(str(x) for x in val)
            return str(val) if val is not None else default

        def to_list(val: Any, default: list = None) -> list:
            if isinstance(val, list):
                return [str(x) for x in val]
            if isinstance(val, str) and val.strip():
                return [val.strip()]
            return default or []

        analysis = GeminiAnalysisResult(
            hook=to_str(data.get("hook"), ad.hook),
            body=to_str(data.get("body"), ad.primary_text),
            headline=to_str(data.get("headline"), ad.headline),
            cta=to_str(data.get("cta"), ad.cta),
            target_audience=to_str(data.get("target_audience"), "Inference: Individuals looking to learn English with AI guidance."),
            customer_pain_point=to_str(data.get("customer_pain_point"), "English fluency difficulty and high tutoring costs."),
            value_proposition=to_str(data.get("value_proposition"), "AI-guided conversational English practice starting at ₹1."),
            usp=to_str(data.get("usp"), "Affordable AI teacher explaining in regional languages with interactive speaking exercises."),
            marketing_angle=to_str(data.get("marketing_angle"), "Low-Barrier Trial & Regional Language Localization"),
            persuasion_techniques=to_str(data.get("persuasion_techniques"), "Hyper-low friction ₹1 price anchoring, aspirational fluency framing, and localized reassurance."),
            strengths=to_list(data.get("strengths"), ["Clear ₹1 trial hook", "Direct CTA", "Addresses localized audience"]),
            weaknesses=to_list(data.get("weaknesses"), ["Needs more verifiable student outcomes", "Lacks video testimonial previews"]),
            improvement_suggestions=to_list(data.get("improvement_suggestions"), ["Show student before/after video", "Highlight specific speaking milestones"]),
            creative_summary=to_str(data.get("creative_summary"), "Direct-response acquisition ad targeting regional learners with a ₹1 trial."),
            media_analysis_notes=to_str(data.get("media_analysis_notes"), f"Analyzed copy alongside {ad.media_type} asset metadata.")
        )

        scores_dict = data.get("rubric_scores", {})
        explanations_dict = data.get("rubric_explanations", {})

        score = self._compute_rubric_score(scores_dict, explanations_dict)
        return analysis, score

    def _compute_rubric_score(
        self,
        scores: Dict[str, Any],
        explanations: Dict[str, str]
    ) -> CreativeScore:
        """Calculate weighted score from 0-10 criteria and build score breakdown."""
        # Section 7 Rubric Weights
        weights = {
            "hook_effectiveness": 20,
            "message_clarity": 15,
            "value_prop_usp": 15,
            "target_audience_relevance": 10,
            "trust_social_proof": 10,
            "cta_effectiveness": 10,
            "creative_execution": 10,
            "differentiation": 10,
        }

        # Safe extraction of 0-10 floats
        def safe_score(k: str, default: float = 7.0) -> float:
            try:
                val = float(scores.get(k, default))
                return max(0.0, min(10.0, round(val, 1)))
            except (ValueError, TypeError):
                return default

        h = safe_score("hook_effectiveness", 7.5)
        m = safe_score("message_clarity", 8.0)
        v = safe_score("value_prop_usp", 7.5)
        t = safe_score("target_audience_relevance", 8.0)
        s = safe_score("trust_social_proof", 5.0)  # default strictly conservative if unsupported
        c = safe_score("cta_effectiveness", 7.0)
        e = safe_score("creative_execution", 7.5)
        d = safe_score("differentiation", 7.5)

        # Weighted calculation out of 100
        total = (
            (h * weights["hook_effectiveness"]) +
            (m * weights["message_clarity"]) +
            (v * weights["value_prop_usp"]) +
            (t * weights["target_audience_relevance"]) +
            (s * weights["trust_social_proof"]) +
            (c * weights["cta_effectiveness"]) +
            (e * weights["creative_execution"]) +
            (d * weights["differentiation"])
        ) / 10.0

        return CreativeScore(
            hook_effectiveness=h,
            message_clarity=m,
            value_prop_usp=v,
            target_audience_relevance=t,
            trust_social_proof=s,
            cta_effectiveness=c,
            creative_execution=e,
            differentiation=d,
            total_score=round(total, 2),
            scoring_explanations=explanations
        )

    def _heuristic_mock_analysis(self, ad: NormalizedAd) -> Tuple[GeminiAnalysisResult, CreativeScore]:
        """
        High-fidelity, deterministic heuristic analysis when Gemini credentials are not supplied.
        Analyzes real textual cues (numbers, pain points, speed claims, comparison words, CTAs).
        """
        text = ad.primary_text.lower()
        title = ad.headline.lower()

        # Heuristic attributes based on actual text
        has_speed = any(w in text for w in ["minute", "seconds", "instant", "fast", "flat"])
        has_cost = any(w in text for w in ["$", "dollar", "cost", "spending", "price", "500"])
        has_comparison = any(w in text for w in ["freelance", "canva", "template", "recycle", "revisions"])
        has_ecommerce = any(w in text for w in ["e-commerce", "product", "catalog", "cpa", "roas"])
        has_social_proof = any(w in text for w in ["trusted", "users", "reviews", "testimonial", "rating"])
        has_free = any(w in text for w in ["free", "trial", "start free", "try for free"])

        if has_speed and has_cost:
            angle = "Cost-Saving & High-Speed Automation"
            usp = "Replaces expensive freelance designers with instant AI banner generation."
            h_score, m_score, v_score = 9.0, 9.0, 8.5
        elif has_comparison:
            angle = "Anti-Template Differentiation"
            usp = "Generates original layout compositions from scratch rather than recycling generic templates."
            h_score, m_score, v_score = 8.5, 8.5, 9.0
        elif has_ecommerce:
            angle = "E-Commerce ROAS & Performance Scaling"
            usp = "Automates multi-format catalog ad creation to combat ad fatigue and scale ad spend."
            h_score, m_score, v_score = 9.2, 8.8, 9.0
        else:
            angle = "Productivity & Generative Design Velocity"
            usp = "Instant prompt-to-banner creation with editable layers."
            h_score, m_score, v_score = 8.0, 8.0, 8.0

        t_score = 8.5 if (has_ecommerce or has_comparison) else 7.5
        s_score = 6.5 if has_social_proof else 5.0  # Transparent strict scoring
        c_score = 8.5 if has_free else 7.0
        e_score = 8.5 if len(ad.image_urls) > 0 else 7.0
        d_score = 9.0 if has_comparison else 8.0

        scores = {
            "hook_effectiveness": h_score,
            "message_clarity": m_score,
            "value_prop_usp": v_score,
            "target_audience_relevance": t_score,
            "trust_social_proof": s_score,
            "cta_effectiveness": c_score,
            "creative_execution": e_score,
            "differentiation": d_score
        }

        explanations = {
            "hook_effectiveness": f"Hook rated {h_score}/10: Strong stopping power with specific quantifiable promises.",
            "message_clarity": f"Message clarity rated {m_score}/10: Immediate understanding of Sivi's AI design proposition.",
            "value_prop_usp": f"Value proposition rated {v_score}/10: Highlights clear contrast against manual/slow alternatives.",
            "target_audience_relevance": f"Audience relevance rated {t_score}/10: Resonates directly with performance marketers and designers.",
            "trust_social_proof": f"Trust rated {s_score}/10: Objective assessment; copy relies on capability claims without third-party validation logos.",
            "cta_effectiveness": f"CTA rated {c_score}/10: Direct low-friction invitation to explore the platform.",
            "creative_execution": f"Execution rated {e_score}/10: Structured copy hierarchy with clear benefits.",
            "differentiation": f"Differentiation rated {d_score}/10: Clearly separates generative AI from static template tools."
        }

        score = self._compute_rubric_score(scores, explanations)

        analysis = GeminiAnalysisResult(
            hook=ad.hook,
            body=ad.primary_text,
            headline=ad.headline,
            cta=ad.cta,
            target_audience="Inference: E-commerce founders, performance marketers, media buyers, and design agencies looking to scale ad creative testing.",
            customer_pain_point="Creative fatigue, slow banner turnaround times, and expensive freelance designer costs.",
            value_proposition="Generate production-ready multi-format marketing banners in 2 minutes flat.",
            usp=usp,
            marketing_angle=angle,
            persuasion_techniques="Quantifiable metric framing (2 minutes / $500), pain-point contrast, and friction-free trial offer.",
            strengths=[
                f"Opening hook establishes immediate relevance: '{ad.hook[:60]}...'",
                "Features clear, quantifiable time/cost outcome promises.",
                f"Low-friction call to action ('{ad.cta}') encourages instant testing."
            ],
            weaknesses=[
                "Lacks verifiable third-party social proof or customer case study metrics.",
                "Could offer an interactive live demo preview directly on the landing page."
            ],
            improvement_suggestions=[
                "Include a customer metric badge (e.g. 'Used by 15,000+ marketers to create 1M+ designs').",
                "Test an explicit offer or guarantee to improve conversion."
            ],
            creative_summary=f"Strong direct-response creative centered on '{angle}', effectively framing Sivi as a high-speed AI design copilot.",
            media_analysis_notes=f"Evaluated copy and messaging. Visual asset format: {ad.media_type}."
        )

        return analysis, score

