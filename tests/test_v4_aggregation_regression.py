"""Version 4 Regression Tests:
Verifying Dedicated Aggregation, Pre-Scoring Validation, and Prevention of Raw Ad Leakage.
"""
import json
import os
import subprocess
import tempfile
from pathlib import Path
import pytest

WORKFLOW_V4_FILE = Path("n8n/mysivi_ad_intelligence_workflow_v4.json")


def load_v4_nodes():
    with open(WORKFLOW_V4_FILE, "r", encoding="utf-8") as f:
        wf = json.load(f)
    return wf, {n["name"]: n for n in wf["nodes"]}


def run_v4_node_js(js_code, input_items, context_runs=None):
    """Execute Node.js with mock $input and context querying support via temp file."""
    if context_runs is None:
        context_runs = {}

    harness = f"""
    const inputData = {json.dumps(input_items)};
    const contextRuns = {json.dumps(context_runs)};

    const $input = {{
        all: () => inputData.map(item => ({{ json: item }})),
        first: () => ({{ json: inputData[0] || {{}} }})
    }};

    const $ = (nodeName, branchIndex, runIndex) => ({{
        all: () => {{
            if (contextRuns[nodeName]) {{
                if (runIndex !== undefined) {{
                    const runData = contextRuns[nodeName][runIndex];
                    if (!runData) throw new Error("Run out of range");
                    return runData.map(item => ({{ json: item }}));
                }}
                // Flatten all runs
                return contextRuns[nodeName].flat().map(item => ({{ json: item }}));
            }}
            return inputData.map(item => ({{ json: item }}));
        }},
        first: () => ({{
            json: (contextRuns[nodeName] ? contextRuns[nodeName].flat()[0] : inputData[0]) || {{
                EXECUTION_MODE: "dataset_replay",
                FB_SEARCH_URL: "https://facebook.com/ads/library"
            }}
        }}),
        item: {{ json: (contextRuns[nodeName] ? contextRuns[nodeName].flat()[0] : inputData[0]) || {{}} }}
    }});

    const result = (function() {{
        {js_code}
    }})();
    console.log(JSON.stringify(result));
    """

    tf = tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False, encoding="utf-8")
    tf.write(harness)
    tf.close()
    tf_name = tf.name

    try:
        res = subprocess.run(["node", tf_name], capture_output=True, text=True, check=True)
        return json.loads(res.stdout)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Node.js execution error ({e.returncode}): {e.stderr}")
    finally:
        if os.path.exists(tf_name):
            try:
                os.remove(tf_name)
            except Exception:
                pass


# 1. One advertisement receives a valid analysis
def test_one_advertisement_receives_valid_analysis():
    _, nodes = load_v4_nodes()
    val_js = nodes["Validate & Structure Ad Analysis"]["parameters"]["jsCode"]

    raw_ad = {
        "internal_id": "MYSIVI-AD-001",
        "ad_id": "946551737840774",
        "headline": "MySivi Se Shuru Karo – Sirf ₹1 Mein",
        "primary_text": "Speak English fluently with AI!",
        "hook": "Speak English fluently with AI!",
        "cta": "Install now"
    }

    gemini_resp = {
        "candidates": [{
            "content": {"parts": [{"text": json.dumps({
                "hook": "Speak English fluently with AI!",
                "headline": "MySivi Se Shuru Karo – Sirf ₹1 Mein",
                "body": "Speak English fluently with AI!",
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
                }
            })}]}
        }],
        "ad": raw_ad
    }

    out = run_v4_node_js(val_js, [gemini_resp])
    rec = out[0]["json"]
    assert rec["internal_id"] == "MYSIVI-AD-001"
    assert "analysis" in rec
    assert rec["analysis"]["hook"]["score"] == 8.5
    assert rec["analysis"]["message_clarity"]["score"] == 9.0


# 2. Four advertisements are aggregated across loop runs
def test_four_advertisements_aggregated():
    _, nodes = load_v4_nodes()
    agg_js = nodes["Aggregate Validated Advertisements"]["parameters"]["jsCode"]

    # Mock 4 loop runs from 'Validate & Structure Ad Analysis'
    runs_data = {
        "Validate & Structure Ad Analysis": [
            [{"internal_id": "MYSIVI-AD-001", "headline": "Hindi", "hook": "H1", "cta": "Install now", "analysis": {"hook": {"score": 8.5}, "message_clarity": {"score": 9.0}, "value_prop_usp": {"score": 8.0}, "target_audience": {"score": 8.5}, "trust_social_proof": {"score": 6.0}, "cta_effectiveness": {"score": 7.5}, "creative_execution": {"score": 8.0}, "differentiation": {"score": 8.5}}}],
            [{"internal_id": "MYSIVI-AD-002", "headline": "{{product.name}}", "hook": "{{product.brand}}", "cta": "Install now", "analysis": {"hook": {"score": 0.0}, "message_clarity": {"score": 0.0}, "value_prop_usp": {"score": 0.0}, "target_audience": {"score": 1.0}, "trust_social_proof": {"score": 0.0}, "cta_effectiveness": {"score": 5.0}, "creative_execution": {"score": 0.0}, "differentiation": {"score": 0.0}}}],
            [{"internal_id": "MYSIVI-AD-003", "headline": "Marathi", "hook": "H3", "cta": "Install now", "analysis": {"hook": {"score": 8.5}, "message_clarity": {"score": 9.0}, "value_prop_usp": {"score": 8.0}, "target_audience": {"score": 8.5}, "trust_social_proof": {"score": 6.0}, "cta_effectiveness": {"score": 7.5}, "creative_execution": {"score": 8.0}, "differentiation": {"score": 8.5}}}],
            [{"internal_id": "MYSIVI-AD-004", "headline": "Bengali", "hook": "H4", "cta": "Install now", "analysis": {"hook": {"score": 8.5}, "message_clarity": {"score": 9.0}, "value_prop_usp": {"score": 8.0}, "target_audience": {"score": 8.5}, "trust_social_proof": {"score": 6.0}, "cta_effectiveness": {"score": 7.5}, "creative_execution": {"score": 8.0}, "differentiation": {"score": 8.5}}}]
        ]
    }

    # Input to aggregator is the done signal (which in n8n might contain 1 raw ad)
    raw_done_input = [{"internal_id": "MYSIVI-AD-001", "headline": "Hindi", "hook": "H1"}]

    out = run_v4_node_js(agg_js, raw_done_input, context_runs=runs_data)
    assert len(out) == 4
    ids = [item["json"]["internal_id"] for item in out]
    assert ids == ["MYSIVI-AD-001", "MYSIVI-AD-002", "MYSIVI-AD-003", "MYSIVI-AD-004"]


# 3. No raw advertisement reaches scoring (pre-scoring validator rejects raw ads)
def test_no_raw_advertisement_reaches_scoring():
    _, nodes = load_v4_nodes()
    pre_val_js = nodes["Validate Scoring Input"]["parameters"]["jsCode"]

    # Raw ad missing 'analysis' object
    raw_ad_item = [
        {"internal_id": "MYSIVI-AD-001", "headline": "Hindi", "hook": "H1", "cta": "Install now"},
        {"internal_id": "MYSIVI-AD-002", "headline": "{{product.name}}", "hook": "H2", "cta": "Install now"},
        {"internal_id": "MYSIVI-AD-003", "headline": "Marathi", "hook": "H3", "cta": "Install now"},
        {"internal_id": "MYSIVI-AD-004", "headline": "Bengali", "hook": "H4", "cta": "Install now"}
    ]

    with pytest.raises(RuntimeError) as exc_info:
        run_v4_node_js(pre_val_js, raw_ad_item)
    assert "missing 'analysis' object" in str(exc_info.value).lower()


# 4. All eight scoring dimensions are present and strictly verified
def test_all_eight_scoring_dimensions_present():
    _, nodes = load_v4_nodes()
    pre_val_js = nodes["Validate Scoring Input"]["parameters"]["jsCode"]

    # Ad missing 'differentiation' dimension
    incomplete_ad = [
        {"internal_id": "MYSIVI-AD-001", "headline": "Hindi", "hook": "H1", "cta": "Install now", "analysis": {"hook": {"score": 8.5}, "message_clarity": {"score": 9.0}, "value_prop_usp": {"score": 8.0}, "target_audience": {"score": 8.5}, "trust_social_proof": {"score": 6.0}, "cta_effectiveness": {"score": 7.5}, "creative_execution": {"score": 8.0}}},
        {"internal_id": "MYSIVI-AD-002", "headline": "Ad2", "hook": "H2", "cta": "Install now", "analysis": {}},
        {"internal_id": "MYSIVI-AD-003", "headline": "Ad3", "hook": "H3", "cta": "Install now", "analysis": {}},
        {"internal_id": "MYSIVI-AD-004", "headline": "Ad4", "hook": "H4", "cta": "Install now", "analysis": {}}
    ]

    with pytest.raises(RuntimeError) as exc_info:
        run_v4_node_js(pre_val_js, incomplete_ad)
    assert "missing scoring dimension" in str(exc_info.value).lower()


# 5. Three joint winners remain correct
def test_three_joint_winners():
    _, nodes = load_v4_nodes()
    score_js = nodes["Score, Rank & Synthesize Intelligence"]["parameters"]["jsCode"]

    valid_four_ads = [
        {"internal_id": "MYSIVI-AD-001", "headline": "Hindi", "hook": "H1", "cta": "Install now", "analysis": {"hook": {"score": 8.5}, "message_clarity": {"score": 9.0}, "value_prop_usp": {"score": 8.0}, "target_audience": {"score": 8.5}, "trust_social_proof": {"score": 6.0}, "cta_effectiveness": {"score": 7.5}, "creative_execution": {"score": 8.0}, "differentiation": {"score": 8.5}}},
        {"internal_id": "MYSIVI-AD-003", "headline": "Marathi", "hook": "H3", "cta": "Install now", "analysis": {"hook": {"score": 8.5}, "message_clarity": {"score": 9.0}, "value_prop_usp": {"score": 8.0}, "target_audience": {"score": 8.5}, "trust_social_proof": {"score": 6.0}, "cta_effectiveness": {"score": 7.5}, "creative_execution": {"score": 8.0}, "differentiation": {"score": 8.5}}},
        {"internal_id": "MYSIVI-AD-004", "headline": "Bengali", "hook": "H4", "cta": "Install now", "analysis": {"hook": {"score": 8.5}, "message_clarity": {"score": 9.0}, "value_prop_usp": {"score": 8.0}, "target_audience": {"score": 8.5}, "trust_social_proof": {"score": 6.0}, "cta_effectiveness": {"score": 7.5}, "creative_execution": {"score": 8.0}, "differentiation": {"score": 8.5}}},
        {"internal_id": "MYSIVI-AD-002", "headline": "{{product.name}}", "hook": "{{product.brand}}", "cta": "Install now", "analysis": {"hook": {"score": 0.0}, "message_clarity": {"score": 0.0}, "value_prop_usp": {"score": 0.0}, "target_audience": {"score": 1.0}, "trust_social_proof": {"score": 0.0}, "cta_effectiveness": {"score": 5.0}, "creative_execution": {"score": 0.0}, "differentiation": {"score": 0.0}}}
    ]

    out = run_v4_node_js(score_js, valid_four_ads)
    rankings = out[0]["json"]["rankings"]
    assert rankings[0]["rank"] == 1 and rankings[0]["score"] == 81.0
    assert rankings[1]["rank"] == 1 and rankings[1]["score"] == 81.0
    assert rankings[2]["rank"] == 1 and rankings[2]["score"] == 81.0
    assert rankings[3]["rank"] == 4 and rankings[3]["score"] == 6.0
    assert out[0]["json"]["comparison"]["winner_justification"][0].startswith("Joint Rank 1 Co-Winners")


# 6. Malformed placeholder ad handled correctly
def test_malformed_placeholder_ad():
    _, nodes = load_v4_nodes()
    heur_js = nodes["Heuristic Mock Analyzer"]["parameters"]["jsCode"]
    score_js = nodes["Score, Rank & Synthesize Intelligence"]["parameters"]["jsCode"]

    malformed_ad = {
        "internal_id": "MYSIVI-AD-002",
        "ad_id": "1843111363320189",
        "headline": "{{product.name}}",
        "primary_text": "{{product.brand}}",
        "hook": "{{product.brand}}",
        "cta": "Install now"
    }

    out = run_v4_node_js(heur_js, [malformed_ad])
    norm = out[0]["json"]
    assert norm["analysis"]["hook"]["score"] == 0.0
    assert norm["analysis"]["marketing_angle"] == "Malformed Dynamic Creative Template"

    scored = run_v4_node_js(score_js, [norm])
    assert scored[0]["json"]["rankings"][0]["score"] == 6.0


# 7. PDF generation receives the final ranked results
def test_pdf_generation_receives_final_ranked_results():
    _, nodes = load_v4_nodes()
    pdf_node = nodes["Trigger PDF Report Generation"]

    # Verify endpoint and body binding
    assert pdf_node["type"] == "n8n-nodes-base.httpRequest"
    assert "/generate-report" in pdf_node["parameters"]["url"]
    assert pdf_node["parameters"]["jsonBody"] == "={{ JSON.stringify($json) }}"
