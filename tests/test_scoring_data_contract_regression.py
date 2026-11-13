"""Comprehensive regression test suite for n8n workflow v3:
Validating Normalized Data Contract, Loop Aggregation, and Error Boundaries.
"""
import json
import subprocess
from pathlib import Path
import pytest

WORKFLOW_V3_FILE = Path("n8n/mysivi_ad_intelligence_workflow_v3.json")


def load_v3_nodes():
    with open(WORKFLOW_V3_FILE, "r", encoding="utf-8") as f:
        wf = json.load(f)
    nodes = {n["name"]: n for n in wf["nodes"]}
    return wf, nodes


def run_node_js(js_code, input_items, context_nodes=None, tmp_path=None):
    """Execute Node.js snippet with mock $input and $ environment."""
    if context_nodes is None:
        context_nodes = {}

    harness = f"""
    const inputData = {json.dumps(input_items)};
    const contextData = {json.dumps(context_nodes)};
    
    const $input = {{
        all: () => inputData.map(item => ({{ json: item }})),
        first: () => ({{ json: inputData[0] || {{}} }})
    }};
    
    const $ = (nodeName) => ({{
        all: () => (contextData[nodeName] || inputData).map(item => ({{ json: item }})),
        first: () => ({{ json: (contextData[nodeName] ? contextData[nodeName][0] : inputData[0]) || {{ EXECUTION_MODE: "dataset_replay", FB_SEARCH_URL: "https://facebook.com/ads/library" }} }}),
        item: {{ json: inputData[0] || {{}} }}
    }});

    const result = (function() {{
        {js_code}
    }})();
    console.log(JSON.stringify(result));
    """

    p = subprocess.Popen(["node"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    out, err = p.communicate(input=harness)
    if p.returncode != 0:
        raise RuntimeError(f"Node.js execution failed (code {p.returncode}): {err}")
    return json.loads(out)


# 1. Gemini response with nested analysis
def test_gemini_response_with_nested_analysis():
    _, nodes = load_v3_nodes()
    validate_js = nodes["Validate & Structure Ad Analysis"]["parameters"]["jsCode"]
    score_js = nodes["Score, Rank & Synthesize Intelligence"]["parameters"]["jsCode"]

    nested_gemini_payload = {
        "analysis": {
            "hook": {"score": 8.5, "explanation": "Engaging hook."},
            "message_clarity": {"score": 9.0, "explanation": "Crystal clear value."},
            "value_prop_usp": {"score": 8.0, "explanation": "Strong ₹1 anchor."},
            "target_audience": {"score": 8.5, "explanation": "Targeted at Indian learners."},
            "trust_social_proof": {"score": 6.0, "explanation": "Needs more testimonials."},
            "cta_effectiveness": {"score": 7.5, "explanation": "Clear Install Now CTA."},
            "creative_execution": {"score": 8.0, "explanation": "Good visual rhythm."},
            "differentiation": {"score": 8.5, "explanation": "Mother-tongue AI practice."}
        },
        "marketing_angle": "Vernacular AI Tutoring",
        "usp": "₹1 trial"
    }

    gemini_http_item = {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": json.dumps(nested_gemini_payload)}]
                }
            }
        ],
        "ad": {
            "internal_id": "MYSIVI-AD-001",
            "ad_id": "946551737840774",
            "headline": "MySivi Se Shuru Karo – Sirf ₹1 Mein",
            "hook": "Speak English fluently with AI!",
            "primary_text": "Speak English fluently with AI! Start at ₹1/-",
            "body": "Speak English fluently with AI! Start at ₹1/-",
            "cta": "Install now"
        }
    }

    # Pass to Validate node
    val_out = run_node_js(validate_js, [gemini_http_item])
    norm = val_out[0]["json"]

    assert norm["internal_id"] == "MYSIVI-AD-001"
    assert norm["hook"] == "Speak English fluently with AI!"
    assert norm["analysis"]["hook"]["score"] == 8.5
    assert norm["analysis"]["message_clarity"]["score"] == 9.0

    # Pass to Score node
    score_out = run_node_js(score_js, [norm])
    master = score_out[0]["json"]
    assert master["rankings"][0]["score"] == 81.0


# 2. Gemini response with a different JSON nesting structure (flat rubric_scores & explanations)
def test_gemini_response_with_different_nesting_structure():
    _, nodes = load_v3_nodes()
    validate_js = nodes["Validate & Structure Ad Analysis"]["parameters"]["jsCode"]
    score_js = nodes["Score, Rank & Synthesize Intelligence"]["parameters"]["jsCode"]

    flat_gemini_payload = {
        "hook": "Bengali English Start",
        "headline": "₹1 theke English start korun",
        "body": "AI teacher apnake Bangla te English bujhiye debe.",
        "cta": "Install now",
        "rubric_scores": {
            "hook_effectiveness": 8.5,
            "message_clarity": 9.0,
            "value_prop_usp": 8.0,
            "target_audience_relevance": 8.5,
            "trust_social_proof": 6.0,
            "cta_effectiveness": 7.5,
            "creative_execution": 8.0,
            "differentiation": 8.5
        },
        "rubric_explanations": {
            "hook_effectiveness": "Bengali hook creates comfort.",
            "message_clarity": "Very clear."
        }
    }

    gemini_http_item = {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": json.dumps(flat_gemini_payload)}]
                }
            }
        ],
        "ad": {
            "internal_id": "MYSIVI-AD-004",
            "ad_id": "2823814924671305",
            "headline": "₹1 theke English start korun",
            "hook": "₹1 theke English start korun",
            "primary_text": "AI teacher apnake Bangla te English bujhiye debe.",
            "cta": "Install now"
        }
    }

    val_out = run_node_js(validate_js, [gemini_http_item])
    norm = val_out[0]["json"]

    assert norm["internal_id"] == "MYSIVI-AD-004"
    assert norm["analysis"]["hook"]["score"] == 8.5
    assert norm["analysis"]["message_clarity"]["score"] == 9.0

    score_out = run_node_js(score_js, [norm])
    master = score_out[0]["json"]
    assert master["rankings"][0]["score"] == 81.0


# 3. Heuristic analyzer response satisfies normalized contract
def test_heuristic_analyzer_response():
    _, nodes = load_v3_nodes()
    heuristic_js = nodes["Heuristic Mock Analyzer"]["parameters"]["jsCode"]
    validate_js = nodes["Validate & Structure Ad Analysis"]["parameters"]["jsCode"]

    ad_input = {
        "internal_id": "MYSIVI-AD-003",
        "ad_id": "2966208700429750",
        "headline": "MySivi सोबत सुरुवात करा – केवळ ₹1 मध्ये",
        "primary_text": "हुशारीनं शिका, कष्ट न करता! MySivi AI सोबत अस्खलित इंग्रजी बोलायला शिका. फक्त ₹1 मध्ये चाचणी सुरू करा!",
        "hook": "हुशारीनं शिका, कष्ट न करता!",
        "cta": "Install now"
    }

    heur_out = run_node_js(heuristic_js, [ad_input])
    heur_ad = heur_out[0]["json"]

    assert heur_ad["internal_id"] == "MYSIVI-AD-003"
    assert heur_ad["analysis"]["hook"]["score"] == 8.5
    assert heur_ad["analysis"]["message_clarity"]["score"] == 9.0
    assert heur_ad["analysis"]["value_prop_usp"]["score"] == 8.0

    # Validate node pass-through
    val_out = run_node_js(validate_js, [heur_ad])
    assert val_out[0]["json"]["analysis"]["hook"]["score"] == 8.5


# 4. Missing hook field error in scoring node
def test_missing_hook_field():
    _, nodes = load_v3_nodes()
    score_js = nodes["Score, Rank & Synthesize Intelligence"]["parameters"]["jsCode"]

    broken_ad = {
        "internal_id": "MYSIVI-AD-999",
        "headline": "Headline with no hook",
        "hook": None,
        "primary_text": "Some text",
        "cta": "Install now",
        "analysis": {
            "hook": {"score": 8.0, "explanation": "x"},
            "message_clarity": {"score": 8.0, "explanation": "x"},
            "value_prop_usp": {"score": 8.0, "explanation": "x"},
            "target_audience": {"score": 8.0, "explanation": "x"},
            "trust_social_proof": {"score": 8.0, "explanation": "x"},
            "cta_effectiveness": {"score": 8.0, "explanation": "x"},
            "creative_execution": {"score": 8.0, "explanation": "x"},
            "differentiation": {"score": 8.0, "explanation": "x"}
        }
    }

    with pytest.raises(RuntimeError) as exc_info:
        run_node_js(score_js, [broken_ad])
    assert "missing 'hook' field" in str(exc_info.value).lower()


# 5. Missing analysis object error in scoring node
def test_missing_analysis_object():
    _, nodes = load_v3_nodes()
    score_js = nodes["Score, Rank & Synthesize Intelligence"]["parameters"]["jsCode"]

    broken_ad = {
        "internal_id": "MYSIVI-AD-999",
        "headline": "Headline",
        "hook": "Hook text",
        "primary_text": "Text",
        "cta": "Install now",
        "analysis": None
    }

    with pytest.raises(RuntimeError) as exc_info:
        run_node_js(score_js, [broken_ad])
    assert "missing 'analysis' object" in str(exc_info.value).lower()


# 6. Invalid score values error in validate node
def test_invalid_score_values():
    _, nodes = load_v3_nodes()
    validate_js = nodes["Validate & Structure Ad Analysis"]["parameters"]["jsCode"]

    out_of_bounds_gemini = {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": json.dumps({
                        "rubric_scores": {
                            "hook_effectiveness": 15.0,  # Out of bounds (>10)
                            "message_clarity": 8.0,
                            "value_prop_usp": 8.0,
                            "target_audience_relevance": 8.0,
                            "trust_social_proof": 8.0,
                            "cta_effectiveness": 8.0,
                            "creative_execution": 8.0,
                            "differentiation": 8.0
                        }
                    })}]
                }
            }
        ],
        "ad": {"internal_id": "MYSIVI-AD-001", "headline": "Test", "hook": "Test"}
    }

    with pytest.raises(RuntimeError) as exc_info:
        run_node_js(validate_js, [out_of_bounds_gemini])
    assert "out of bounds" in str(exc_info.value).lower()


# 7. All four advertisements processed together
def test_all_four_advertisements_processed():
    _, nodes = load_v3_nodes()
    score_js = nodes["Score, Rank & Synthesize Intelligence"]["parameters"]["jsCode"]

    four_ads = [
        {"internal_id": "MYSIVI-AD-001", "headline": "Hindi", "hook": "Hook 1", "cta": "Install now", "analysis": {"hook": {"score": 8.5}, "message_clarity": {"score": 9.0}, "value_prop_usp": {"score": 8.0}, "target_audience": {"score": 8.5}, "trust_social_proof": {"score": 6.0}, "cta_effectiveness": {"score": 7.5}, "creative_execution": {"score": 8.0}, "differentiation": {"score": 8.5}}},
        {"internal_id": "MYSIVI-AD-002", "headline": "{{product.name}}", "hook": "{{product.brand}}", "cta": "Install now", "analysis": {"hook": {"score": 0.0}, "message_clarity": {"score": 0.0}, "value_prop_usp": {"score": 0.0}, "target_audience": {"score": 1.0}, "trust_social_proof": {"score": 0.0}, "cta_effectiveness": {"score": 5.0}, "creative_execution": {"score": 0.0}, "differentiation": {"score": 0.0}}},
        {"internal_id": "MYSIVI-AD-003", "headline": "Marathi", "hook": "Hook 3", "cta": "Install now", "analysis": {"hook": {"score": 8.5}, "message_clarity": {"score": 9.0}, "value_prop_usp": {"score": 8.0}, "target_audience": {"score": 8.5}, "trust_social_proof": {"score": 6.0}, "cta_effectiveness": {"score": 7.5}, "creative_execution": {"score": 8.0}, "differentiation": {"score": 8.5}}},
        {"internal_id": "MYSIVI-AD-004", "headline": "Bengali", "hook": "Hook 4", "cta": "Install now", "analysis": {"hook": {"score": 8.5}, "message_clarity": {"score": 9.0}, "value_prop_usp": {"score": 8.0}, "target_audience": {"score": 8.5}, "trust_social_proof": {"score": 6.0}, "cta_effectiveness": {"score": 7.5}, "creative_execution": {"score": 8.0}, "differentiation": {"score": 8.5}}}
    ]

    res = run_node_js(score_js, four_ads)
    master = res[0]["json"]
    assert len(master["advertisements"]) == 4
    assert len(master["rankings"]) == 4


# 8. Mathematical scoring accuracy
def test_mathematical_scoring_accuracy():
    _, nodes = load_v3_nodes()
    score_js = nodes["Score, Rank & Synthesize Intelligence"]["parameters"]["jsCode"]

    test_ad = {
        "internal_id": "MYSIVI-AD-001",
        "headline": "Hindi",
        "hook": "Hook 1",
        "cta": "Install now",
        "analysis": {
            "hook": {"score": 8.5},
            "message_clarity": {"score": 9.0},
            "value_prop_usp": {"score": 8.0},
            "target_audience": {"score": 8.5},
            "trust_social_proof": {"score": 6.0},
            "cta_effectiveness": {"score": 7.5},
            "creative_execution": {"score": 8.0},
            "differentiation": {"score": 8.5}
        }
    }

    # Expected: (8.5*20 + 9.0*15 + 8.0*15 + 8.5*10 + 6.0*10 + 7.5*10 + 8.0*10 + 8.5*10) / 10.0 = 81.0
    res = run_node_js(score_js, [test_ad])
    assert res[0]["json"]["rankings"][0]["score"] == 81.0


# 9. Three joint winners Olympic ranking
def test_three_joint_winners():
    _, nodes = load_v3_nodes()
    score_js = nodes["Score, Rank & Synthesize Intelligence"]["parameters"]["jsCode"]

    three_tied_plus_one = [
        {"internal_id": "MYSIVI-AD-001", "headline": "Hindi", "hook": "Hook 1", "cta": "Install now", "analysis": {"hook": {"score": 8.5}, "message_clarity": {"score": 9.0}, "value_prop_usp": {"score": 8.0}, "target_audience": {"score": 8.5}, "trust_social_proof": {"score": 6.0}, "cta_effectiveness": {"score": 7.5}, "creative_execution": {"score": 8.0}, "differentiation": {"score": 8.5}}},
        {"internal_id": "MYSIVI-AD-003", "headline": "Marathi", "hook": "Hook 3", "cta": "Install now", "analysis": {"hook": {"score": 8.5}, "message_clarity": {"score": 9.0}, "value_prop_usp": {"score": 8.0}, "target_audience": {"score": 8.5}, "trust_social_proof": {"score": 6.0}, "cta_effectiveness": {"score": 7.5}, "creative_execution": {"score": 8.0}, "differentiation": {"score": 8.5}}},
        {"internal_id": "MYSIVI-AD-004", "headline": "Bengali", "hook": "Hook 4", "cta": "Install now", "analysis": {"hook": {"score": 8.5}, "message_clarity": {"score": 9.0}, "value_prop_usp": {"score": 8.0}, "target_audience": {"score": 8.5}, "trust_social_proof": {"score": 6.0}, "cta_effectiveness": {"score": 7.5}, "creative_execution": {"score": 8.0}, "differentiation": {"score": 8.5}}},
        {"internal_id": "MYSIVI-AD-002", "headline": "{{product.name}}", "hook": "{{product.brand}}", "cta": "Install now", "analysis": {"hook": {"score": 0.0}, "message_clarity": {"score": 0.0}, "value_prop_usp": {"score": 0.0}, "target_audience": {"score": 1.0}, "trust_social_proof": {"score": 0.0}, "cta_effectiveness": {"score": 5.0}, "creative_execution": {"score": 0.0}, "differentiation": {"score": 0.0}}}
    ]

    res = run_node_js(score_js, three_tied_plus_one)
    rankings = res[0]["json"]["rankings"]
    assert rankings[0]["rank"] == 1
    assert rankings[1]["rank"] == 1
    assert rankings[2]["rank"] == 1
    assert rankings[3]["rank"] == 4

    assert res[0]["json"]["comparison"]["winner_justification"][0].startswith("Joint Rank 1 Co-Winners")


# 10. Malformed placeholder advertisement
def test_malformed_placeholder_advertisement():
    _, nodes = load_v3_nodes()
    heuristic_js = nodes["Heuristic Mock Analyzer"]["parameters"]["jsCode"]
    score_js = nodes["Score, Rank & Synthesize Intelligence"]["parameters"]["jsCode"]

    malformed_ad = {
        "internal_id": "MYSIVI-AD-002",
        "ad_id": "1843111363320189",
        "headline": "{{product.name}}",
        "primary_text": "{{product.brand}}",
        "hook": "{{product.brand}}",
        "cta": "Install now"
    }

    heur_out = run_node_js(heuristic_js, [malformed_ad])
    ad_item = heur_out[0]["json"]

    assert ad_item["analysis"]["marketing_angle"] == "Malformed Dynamic Creative Template"
    assert ad_item["analysis"]["hook"]["score"] == 0.0
    assert ad_item["analysis"]["message_clarity"]["score"] == 0.0

    score_out = run_node_js(score_js, [ad_item])
    # Expected score: (1.0*10 + 5.0*10) / 10.0 = 6.0
    assert score_out[0]["json"]["rankings"][0]["score"] == 6.0

