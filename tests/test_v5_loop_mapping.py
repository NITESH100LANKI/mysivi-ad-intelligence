"""Version 5 Regression Tests:
Verifying Correct n8n Loop Output Mapping (Output 0 = DONE, Output 1 = LOOP),
Aggregator Consumption via $input.all(), Pre-Scoring Validation, and Downstream Ranking.
"""
import json
import os
import subprocess
import tempfile
from pathlib import Path
import pytest

WORKFLOW_V5_FILE = Path("n8n/mysivi_ad_intelligence_workflow_v5.json")


def load_v5_workflow():
    assert WORKFLOW_V5_FILE.exists(), f"Workflow file not found: {WORKFLOW_V5_FILE}"
    with open(WORKFLOW_V5_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def load_v5_nodes():
    wf = load_v5_workflow()
    return wf, {n["name"]: n for n in wf["nodes"]}


def run_node_js(js_code, input_items, context_runs=None):
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
                return contextRuns[nodeName].flat().map(item => ({{ json: item }}));
            }}
            return inputData.map(item => ({{ json: item }}));
        }},
        first: () => ({{
            json: (contextRuns[nodeName] ? contextRuns[nodeName].flat()[0] : inputData[0]) || {{}}
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


# 1. Structure and node version check
def test_v5_nodes_structure_and_type_version():
    wf, nodes = load_v5_nodes()
    assert len(wf.get("nodes", [])) == 20, f"Expected 20 nodes, got {len(wf.get('nodes', []))}"

    loop_node = nodes["Loop Over Ad Creatives"]
    assert loop_node["type"] == "n8n-nodes-base.splitInBatches"
    assert loop_node.get("typeVersion") == 3, f"Expected Loop typeVersion 3, got {loop_node.get('typeVersion')}"
    assert loop_node["parameters"].get("batchSize") == 1

    assert "Aggregate Validated Advertisements" in nodes
    assert "Validate Scoring Input" in nodes
    assert "Score, Rank & Synthesize Intelligence" in nodes


# 2. Output 0 connects to Aggregator (DONE), Output 1 connects to Per-Ad Branch (LOOP)
def test_v5_loop_output_mapping_corrected():
    wf, _ = load_v5_nodes()
    connections = wf["connections"]

    loop_outputs = connections.get("Loop Over Ad Creatives", {}).get("main", [])
    assert len(loop_outputs) == 2, f"Loop Over Ad Creatives must have 2 output channels, got {len(loop_outputs)}"

    # Output 0 = DONE in SplitInBatches V3 -> connects to Aggregate Validated Advertisements
    done_targets = [c["node"] for c in loop_outputs[0]]
    assert done_targets == ["Aggregate Validated Advertisements"], (
        f"Output 0 (DONE) must connect to 'Aggregate Validated Advertisements', got {done_targets}"
    )

    # Output 1 = LOOP in SplitInBatches V3 -> connects to Has Gemini API Key?
    loop_targets = [c["node"] for c in loop_outputs[1]]
    assert loop_targets == ["Has Gemini API Key?"], (
        f"Output 1 (LOOP) must connect to 'Has Gemini API Key?', got {loop_targets}"
    )


# 3. Validation feeds back into Loop Over Ad Creatives input
def test_v5_validation_feedback_connection():
    wf, _ = load_v5_nodes()
    connections = wf["connections"]

    val_outputs = connections.get("Validate & Structure Ad Analysis", {}).get("main", [])
    assert len(val_outputs) >= 1
    feedback_targets = [c["node"] for c in val_outputs[0]]
    assert feedback_targets == ["Loop Over Ad Creatives"]
    assert val_outputs[0][0]["index"] == 0


# 4. Pipeline downstream sequence from Aggregator to PDF and Summary
def test_v5_downstream_sequence():
    wf, _ = load_v5_nodes()
    connections = wf["connections"]

    # Aggregate -> Validate Scoring Input
    agg_targets = [c["node"] for c in connections.get("Aggregate Validated Advertisements", {}).get("main", [[]])[0]]
    assert agg_targets == ["Validate Scoring Input"]

    # Validate Scoring Input -> Score, Rank & Synthesize Intelligence
    val_targets = [c["node"] for c in connections.get("Validate Scoring Input", {}).get("main", [[]])[0]]
    assert val_targets == ["Score, Rank & Synthesize Intelligence"]

    # Score -> Trigger PDF Report Generation
    score_targets = [c["node"] for c in connections.get("Score, Rank & Synthesize Intelligence", {}).get("main", [[]])[0]]
    assert score_targets == ["Trigger PDF Report Generation"]

    # Trigger PDF -> Final Execution Summary
    pdf_targets = [c["node"] for c in connections.get("Trigger PDF Report Generation", {}).get("main", [[]])[0]]
    assert pdf_targets == ["Final Execution Summary"]


# 5. Aggregator receives processed results through $input.all()
def test_v5_aggregator_receives_done_output_all():
    _, nodes = load_v5_nodes()
    agg_js = nodes["Aggregate Validated Advertisements"]["parameters"]["jsCode"]

    analyzed_ads = [
        {"internal_id": "MYSIVI-AD-001", "headline": "Hindi", "hook": "H1", "cta": "Install now", "analysis": {"hook": {"score": 8.5}, "message_clarity": {"score": 9.0}, "value_prop_usp": {"score": 8.0}, "target_audience": {"score": 8.5}, "trust_social_proof": {"score": 6.0}, "cta_effectiveness": {"score": 7.5}, "creative_execution": {"score": 8.0}, "differentiation": {"score": 8.5}}},
        {"internal_id": "MYSIVI-AD-002", "headline": "{{product.name}}", "hook": "{{product.brand}}", "cta": "Install now", "analysis": {"hook": {"score": 0.0}, "message_clarity": {"score": 0.0}, "value_prop_usp": {"score": 0.0}, "target_audience": {"score": 1.0}, "trust_social_proof": {"score": 0.0}, "cta_effectiveness": {"score": 5.0}, "creative_execution": {"score": 0.0}, "differentiation": {"score": 0.0}}},
        {"internal_id": "MYSIVI-AD-003", "headline": "Marathi", "hook": "H3", "cta": "Install now", "analysis": {"hook": {"score": 8.5}, "message_clarity": {"score": 9.0}, "value_prop_usp": {"score": 8.0}, "target_audience": {"score": 8.5}, "trust_social_proof": {"score": 6.0}, "cta_effectiveness": {"score": 7.5}, "creative_execution": {"score": 8.0}, "differentiation": {"score": 8.5}}},
        {"internal_id": "MYSIVI-AD-004", "headline": "Bengali", "hook": "H4", "cta": "Install now", "analysis": {"hook": {"score": 8.5}, "message_clarity": {"score": 9.0}, "value_prop_usp": {"score": 8.0}, "target_audience": {"score": 8.5}, "trust_social_proof": {"score": 6.0}, "cta_effectiveness": {"score": 7.5}, "creative_execution": {"score": 8.0}, "differentiation": {"score": 8.5}}}
    ]

    out = run_node_js(agg_js, analyzed_ads)
    assert len(out) == 4
    ids = [item["json"]["internal_id"] for item in out]
    assert ids == ["MYSIVI-AD-001", "MYSIVI-AD-002", "MYSIVI-AD-003", "MYSIVI-AD-004"]


# 6. Aggregator deduplicates by internal_id and enforces exactly 4 ads
def test_v5_aggregator_deduplicates_and_enforces_count():
    _, nodes = load_v5_nodes()
    agg_js = nodes["Aggregate Validated Advertisements"]["parameters"]["jsCode"]

    # 5 items with 1 duplicate (MYSIVI-AD-001 repeated)
    analyzed_with_dup = [
        {"internal_id": "MYSIVI-AD-001", "headline": "Hindi", "hook": "H1", "analysis": {"hook": {"score": 8.5}}},
        {"internal_id": "MYSIVI-AD-001", "headline": "Hindi", "hook": "H1", "analysis": {"hook": {"score": 8.5}}},
        {"internal_id": "MYSIVI-AD-002", "headline": "Ad2", "hook": "H2", "analysis": {"hook": {"score": 0.0}}},
        {"internal_id": "MYSIVI-AD-003", "headline": "Ad3", "hook": "H3", "analysis": {"hook": {"score": 8.5}}},
        {"internal_id": "MYSIVI-AD-004", "headline": "Ad4", "hook": "H4", "analysis": {"hook": {"score": 8.5}}}
    ]
    out = run_node_js(agg_js, analyzed_with_dup)
    assert len(out) == 4

    # Only 3 unique ads -> must throw
    only_3 = analyzed_with_dup[:3]
    with pytest.raises(RuntimeError) as exc_info:
        run_node_js(agg_js, only_3)
    assert "expected 4 unique analyzed advertisements" in str(exc_info.value).lower()


# 7. No raw advertisement reaches scoring
def test_v5_no_raw_ad_reaches_scoring():
    _, nodes = load_v5_nodes()
    agg_js = nodes["Aggregate Validated Advertisements"]["parameters"]["jsCode"]
    val_js = nodes["Validate Scoring Input"]["parameters"]["jsCode"]

    raw_ads = [
        {"internal_id": "MYSIVI-AD-001", "headline": "Hindi", "hook": "H1", "cta": "Install now"},
        {"internal_id": "MYSIVI-AD-002", "headline": "{{product.name}}", "hook": "{{product.brand}}", "cta": "Install now"},
        {"internal_id": "MYSIVI-AD-003", "headline": "Marathi", "hook": "H3", "cta": "Install now"},
        {"internal_id": "MYSIVI-AD-004", "headline": "Bengali", "hook": "H4", "cta": "Install now"}
    ]

    # Rejection at Aggregator
    with pytest.raises(RuntimeError) as exc_info_agg:
        run_node_js(agg_js, raw_ads)
    assert "received 0 completed advertisement analyses" in str(exc_info_agg.value).lower()

    # Rejection at Validate Scoring Input
    with pytest.raises(RuntimeError) as exc_info_val:
        run_node_js(val_js, raw_ads)
    assert "missing 'analysis' object" in str(exc_info_val.value).lower()


# 8. Four complete advertisements reach scoring with joint winners logic
def test_v5_four_complete_ads_reach_scoring_with_joint_winners():
    _, nodes = load_v5_nodes()
    score_js = nodes["Score, Rank & Synthesize Intelligence"]["parameters"]["jsCode"]

    valid_four_ads = [
        {"internal_id": "MYSIVI-AD-001", "headline": "Hindi", "hook": "H1", "cta": "Install now", "analysis": {"hook": {"score": 8.5}, "message_clarity": {"score": 9.0}, "value_prop_usp": {"score": 8.0}, "target_audience": {"score": 8.5}, "trust_social_proof": {"score": 6.0}, "cta_effectiveness": {"score": 7.5}, "creative_execution": {"score": 8.0}, "differentiation": {"score": 8.5}}},
        {"internal_id": "MYSIVI-AD-003", "headline": "Marathi", "hook": "H3", "cta": "Install now", "analysis": {"hook": {"score": 8.5}, "message_clarity": {"score": 9.0}, "value_prop_usp": {"score": 8.0}, "target_audience": {"score": 8.5}, "trust_social_proof": {"score": 6.0}, "cta_effectiveness": {"score": 7.5}, "creative_execution": {"score": 8.0}, "differentiation": {"score": 8.5}}},
        {"internal_id": "MYSIVI-AD-004", "headline": "Bengali", "hook": "H4", "cta": "Install now", "analysis": {"hook": {"score": 8.5}, "message_clarity": {"score": 9.0}, "value_prop_usp": {"score": 8.0}, "target_audience": {"score": 8.5}, "trust_social_proof": {"score": 6.0}, "cta_effectiveness": {"score": 7.5}, "creative_execution": {"score": 8.0}, "differentiation": {"score": 8.5}}},
        {"internal_id": "MYSIVI-AD-002", "headline": "{{product.name}}", "hook": "{{product.brand}}", "cta": "Install now", "analysis": {"hook": {"score": 0.0}, "message_clarity": {"score": 0.0}, "value_prop_usp": {"score": 0.0}, "target_audience": {"score": 1.0}, "trust_social_proof": {"score": 0.0}, "cta_effectiveness": {"score": 5.0}, "creative_execution": {"score": 0.0}, "differentiation": {"score": 0.0}}}
    ]

    out = run_node_js(score_js, valid_four_ads)
    rankings = out[0]["json"]["rankings"]
    assert len(rankings) == 4
    assert rankings[0]["rank"] == 1 and rankings[0]["score"] == 81.0
    assert rankings[1]["rank"] == 1 and rankings[1]["score"] == 81.0
    assert rankings[2]["rank"] == 1 and rankings[2]["score"] == 81.0
    assert rankings[3]["rank"] == 4 and rankings[3]["score"] == 6.0
    assert out[0]["json"]["comparison"]["winner_justification"][0].startswith("Joint Rank 1 Co-Winners")


# 9. PDF generation node receives final ranking structure
def test_v5_pdf_receives_final_ranking():
    _, nodes = load_v5_nodes()
    pdf_node = nodes["Trigger PDF Report Generation"]

    assert pdf_node["type"] == "n8n-nodes-base.httpRequest"
    assert "/generate-report" in pdf_node["parameters"]["url"]
    assert pdf_node["parameters"]["jsonBody"] == "={{ JSON.stringify($json) }}"

