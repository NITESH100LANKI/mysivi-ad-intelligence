"""Pydantic data schemas for validation across pipeline stages."""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class RawSnapshot(BaseModel):
    """Raw snapshot schema from Apify output."""
    body: Optional[Any] = None
    title: Optional[str] = None
    caption: Optional[str] = None
    link_description: Optional[str] = None
    cta_text: Optional[str] = None
    link_url: Optional[str] = None
    images: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    videos: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    cards: Optional[List[Dict[str, Any]]] = Field(default_factory=list)


class NormalizedAd(BaseModel):
    """Cleaned, deduplicated and normalized advertisement representation."""
    internal_id: str
    ad_id: str
    page_name: str
    page_id: Optional[str] = "Unavailable"
    ad_library_url: str
    primary_text: str
    hook: str
    headline: str
    description: str
    cta: str
    landing_page_url: str
    image_urls: List[str] = Field(default_factory=list)
    video_urls: List[str] = Field(default_factory=list)
    start_date: Optional[str] = "Unavailable"
    end_date: Optional[str] = "Unavailable"
    is_active: bool = True
    publisher_platforms: List[str] = Field(default_factory=list)
    impression_info: str = "Unavailable in standard public ad library view"
    media_type: str = "image"
    raw_snapshot: Optional[Dict[str, Any]] = Field(default_factory=dict)


class GeminiAnalysisResult(BaseModel):
    """Structured AI analysis result according to the 14 required dimensions."""
    hook: str = Field(description="The opening attention-grabbing statement or opening creative message.")
    body: str = Field(description="Complete advertising message.")
    headline: str = Field(description="Main advertisement headline.")
    cta: str = Field(description="Actual call-to-action or unavailable.")
    target_audience: str = Field(description="Likely intended customer segment (Inference).")
    customer_pain_point: str = Field(description="Problem the advertisement attempts to solve.")
    value_proposition: str = Field(description="Main customer benefit.")
    usp: str = Field(description="Unique selling point.")
    marketing_angle: str = Field(description="E.g. problem-solution, urgency, aspirational, educational, social proof.")
    persuasion_techniques: str = Field(description="Explanation of persuasion techniques used.")
    strengths: List[str] = Field(description="Key factors making the ad compelling.")
    weaknesses: List[str] = Field(description="Areas where the ad could improve.")
    improvement_suggestions: List[str] = Field(description="Specific, actionable recommendations.")
    creative_summary: str = Field(description="Concise synthesis of the ad's creative strategy.")
    media_analysis_notes: str = Field(default="Text-based creative analysis. Media review verified where accessible.")


class CreativeScore(BaseModel):
    """Transparent, mathematically calculated quality score based on 100-pt rubric."""
    hook_effectiveness: float = Field(ge=0, le=10, description="Hook effectiveness (Weight: 20%)")
    message_clarity: float = Field(ge=0, le=10, description="Message clarity (Weight: 15%)")
    value_prop_usp: float = Field(ge=0, le=10, description="Value proposition and USP (Weight: 15%)")
    target_audience_relevance: float = Field(ge=0, le=10, description="Target audience relevance (Weight: 10%)")
    trust_social_proof: float = Field(ge=0, le=10, description="Trust and social proof (Weight: 10%)")
    cta_effectiveness: float = Field(ge=0, le=10, description="CTA effectiveness (Weight: 10%)")
    creative_execution: float = Field(ge=0, le=10, description="Creative execution (Weight: 10%)")
    differentiation: float = Field(ge=0, le=10, description="Differentiation (Weight: 10%)")
    total_score: float = Field(ge=0, le=100, description="Weighted total score out of 100")
    scoring_explanations: Dict[str, str] = Field(default_factory=dict)


class AnalyzedAd(BaseModel):
    """Complete analyzed advertisement model combining normalized data, AI analysis, and scoring."""
    ad: NormalizedAd
    analysis: GeminiAnalysisResult
    score: CreativeScore
    rank: Optional[int] = None
    is_best_creative: bool = False


class FullAnalysisResult(BaseModel):
    """Master output schema matching Section 8 requirements."""
    project: str = "MySivi Ad Intelligence"
    source: str = "Facebook Ad Library"
    execution_timestamp: str
    execution_mode: str
    collection_summary: Dict[str, Any]
    advertisements: List[AnalyzedAd]
    rankings: List[Dict[str, Any]]
    top_ad: Optional[Dict[str, Any]] = None
    comparison: Dict[str, Any]
    marketing_insights: List[str]
    recommendations: List[str]
    limitations: List[str]

