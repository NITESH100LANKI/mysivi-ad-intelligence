"""Verification script executing the exact JavaScript code blocks from the n8n workflow v2 JSON."""
import json
import subprocess
from pathlib import Path
import pytest

WORKFLOW_V2_FILE = Path("n8n/mysivi_ad_intelligence_workflow_v2.json")
RAW_DATA_FILE = Path("data/raw/raw_ads_live_20261112_163334.json")


def test_n8n_v2_workflow_json_schema():
    """Verify workflow v2 JSON has all required nodes and valid structure."""
    assert WORKFLOW_V2_FILE.exists()
    with open(WORKFLOW_V2_FILE, "r", encoding="utf-8") as f:
        wf = json.load(f)

    assert "nodes" in wf
    assert "connections" in wf
    assert len(wf["nodes"]) == 18

    node_names = [n["name"] for n in wf["nodes"]]
    assert "Manual Trigger" in node_names
    assert "Init Configuration" in node_names
    assert "Execution Mode Router" in node_names
    assert "Apify Start Scraper Run" in node_names
    assert "Fetch Apify Dataset Items" in node_names
    assert "Load Mock / Fixture Data" in node_names
    assert "Merge Ingestion Streams" in node_names
    assert "Clean, Normalize & Deduplicate" in node_names
    assert "Loop Over Ad Creatives" in node_names
    assert "Has Gemini API Key?" in node_names
    assert "Call Google Gemini AI" in node_names
    assert "Heuristic Mock Analyzer" in node_names
    assert "Validate & Structure Ad Analysis" in node_names
    assert "Score, Rank & Synthesize Intelligence" in node_names
    assert "Trigger PDF Report Generation" in node_names
    assert "Final Execution Summary" in node_names


def test_n8n_v2_node_8_load_mock_fixture_js(tmp_path):
    """Verify Node 8 generates all 4 unique ads from original verified dataset."""
    with open(WORKFLOW_V2_FILE, "r", encoding="utf-8") as f:
        wf = json.load(f)
    node8 = [n for n in wf["nodes"] if n["name"] == "Load Mock / Fixture Data"][0]
    js_code = node8["parameters"]["jsCode"]

    harness = f"""
    const result = (function() {{
        {js_code}
    }})();
    console.log(JSON.stringify(result));
    """

    script_file = tmp_path / "node8.js"
    script_file.write_text(harness, encoding="utf-8")
    res = subprocess.run(["node", str(script_file)], capture_output=True, text=True, check=True)
    output = json.loads(res.stdout)
    assert len(output) == 4, f"Expected 4 mock ads in fixture node, got {len(output)}"
    ids = [item["json"]["ad_archive_id"] for item in output]
    assert "946551737840774" in ids
    assert "1843111363320189" in ids
    assert "2966208700429750" in ids
    assert "2823814924671305" in ids


def test_n8n_v2_node_10_clean_normalize_deduplicate_js(tmp_path):
    """Execute Node 10 jsCode directly in Node.js with raw live records."""
    with open(WORKFLOW_V2_FILE, "r", encoding="utf-8") as f:
        wf = json.load(f)
    node10 = [n for n in wf["nodes"] if n["name"] == "Clean, Normalize & Deduplicate"][0]
    js_code = node10["parameters"]["jsCode"]

    with open(RAW_DATA_FILE, "r", encoding="utf-8") as f:
        raw_items = json.load(f)

    harness = f"""
    const rawData = {json.dumps(raw_items)};
    const $input = {{
        all: () => rawData.map(item => ({{ json: item }}))
    }};
    const result = (function() {{
        {js_code}
    }})();
    console.log(JSON.stringify(result));
    """

    script_file = tmp_path / "node10.js"
    script_file.write_text(harness, encoding="utf-8")
    res = subprocess.run(["node", str(script_file)], capture_output=True, text=True, check=True)
    output = json.loads(res.stdout)
    assert len(output) == 4
    internal_ids = [item["json"]["internal_id"] for item in output]
    assert internal_ids == ["MYSIVI-AD-001", "MYSIVI-AD-002", "MYSIVI-AD-003", "MYSIVI-AD-004"]


def test_n8n_v2_node_14_heuristic_mock_analyzer_js(tmp_path):
    """Execute Node 14 jsCode to verify placeholder penalty and vernacular evaluation."""
    with open(WORKFLOW_V2_FILE, "r", encoding="utf-8") as f:
        wf = json.load(f)
    node14 = [n for n in wf["nodes"] if n["name"] == "Heuristic Mock Analyzer"][0]
    js_code = node14["parameters"]["jsCode"]

    # Test 1: Placeholder ad
    bad_ad = {"internal_id": "MYSIVI-AD-002", "headline": "{{product.name}}", "primary_text": "{{product.brand}}", "hook": "{{product.brand}}", "cta": "Install now"}
    harness_bad = f"""
    const $input = {{ first: () => ({{ json: {json.dumps(bad_ad)} }}) }};
    const result = (function() {{ {js_code} }})();
    console.log(JSON.stringify(result));
    """
    script_bad = tmp_path / "node14_bad.js"
    script_bad.write_text(harness_bad, encoding="utf-8")
    res1 = subprocess.run(["node", str(script_bad)], capture_output=True, text=True, check=True)
    out1 = json.loads(res1.stdout)[0]["json"]
    assert out1["rubric_scores"]["hook_effectiveness"] == 0.0
    assert out1["analysis"]["marketing_angle"] == "Malformed Dynamic Creative Template"

    # Test 2: Vernacular Hindi ad
    good_ad = {"internal_id": "MYSIVI-AD-001", "headline": "MySivi Se Shuru Karo – Sirf ₹1 Mein", "primary_text": "Speak English fluently with AI! Start at ₹1/-", "hook": "Speak English fluently", "cta": "Install now"}
    harness_good = f"""
    const $input = {{ first: () => ({{ json: {json.dumps(good_ad)} }}) }};
    const result = (function() {{ {js_code} }})();
    console.log(JSON.stringify(result));
    """
    script_good = tmp_path / "node14_good.js"
    script_good.write_text(harness_good, encoding="utf-8")
    res2 = subprocess.run(["node", str(script_good)], capture_output=True, text=True, check=True)
    out2 = json.loads(res2.stdout)[0]["json"]
    assert out2["rubric_scores"]["hook_effectiveness"] == 8.5
    assert out2["rubric_scores"]["message_clarity"] == 9.0


def test_n8n_v2_node_16_score_and_rank_js(tmp_path):
    """Execute Node 16 jsCode directly in Node.js to verify ranking and joint winner logic."""
    with open(WORKFLOW_V2_FILE, "r", encoding="utf-8") as f:
        wf = json.load(f)
    node16 = [n for n in wf["nodes"] if n["name"] == "Score, Rank & Synthesize Intelligence"][0]
    js_code = node16["parameters"]["jsCode"]

    analyzed_input = [
        {
            "ad": {"internal_id": "MYSIVI-AD-001", "ad_id": "111", "headline": "Hindi Ad", "hook": "Hook 1", "cta": "Install now"},
            "analysis": {"strengths": ["Strong hook"], "marketing_angle": "Hindi Vernacular", "usp": "₹1 trial"},
            "rubric_scores": {"hook_effectiveness": 8.5, "message_clarity": 9.0, "value_prop_usp": 8.0, "target_audience_relevance": 8.5, "trust_social_proof": 6.0, "cta_effectiveness": 7.5, "creative_execution": 8.0, "differentiation": 8.5}
        },
        {
            "ad": {"internal_id": "MYSIVI-AD-003", "ad_id": "333", "headline": "Marathi Ad", "hook": "Hook 3", "cta": "Install now"},
            "analysis": {"strengths": ["Regional resonance"], "marketing_angle": "Marathi Vernacular", "usp": "₹1 trial"},
            "rubric_scores": {"hook_effectiveness": 8.5, "message_clarity": 9.0, "value_prop_usp": 8.0, "target_audience_relevance": 8.5, "trust_social_proof": 6.0, "cta_effectiveness": 7.5, "creative_execution": 8.0, "differentiation": 8.5}
        },
        {
            "ad": {"internal_id": "MYSIVI-AD-004", "ad_id": "444", "headline": "Bengali Ad", "hook": "Hook 4", "cta": "Install now"},
            "analysis": {"strengths": ["Bengali comfort"], "marketing_angle": "Bengali Vernacular", "usp": "₹1 trial"},
            "rubric_scores": {"hook_effectiveness": 8.5, "message_clarity": 9.0, "value_prop_usp": 8.0, "target_audience_relevance": 8.5, "trust_social_proof": 6.0, "cta_effectiveness": 7.5, "creative_execution": 8.0, "differentiation": 8.5}
        },
        {
            "ad": {"internal_id": "MYSIVI-AD-002", "ad_id": "222", "headline": "{{product.name}}", "hook": "{{product.brand}}", "cta": "Install now"},
            "analysis": {"strengths": [], "marketing_angle": "Template", "usp": "None"},
            "rubric_scores": {"hook_effectiveness": 0.0, "message_clarity": 0.0, "value_prop_usp": 0.0, "target_audience_relevance": 1.0, "trust_social_proof": 0.0, "cta_effectiveness": 5.0, "creative_execution": 0.0, "differentiation": 0.0}
        }
    ]

    harness = f"""
    const inputData = {json.dumps(analyzed_input)};
    const $input = {{
        all: () => inputData.map(item => ({{ json: item }}))
    }};
    const $ = (nodeName) => ({{
        all: () => inputData.map(item => ({{ json: item }})),
        first: () => ({{
            json: {{
                EXECUTION_MODE: "dataset_replay",
                FB_SEARCH_URL: "https://facebook.com/ads/library"
            }}
        }})
    }});
    const result = (function() {{
        {js_code}
    }})();
    console.log(JSON.stringify(result));
    """

    script_file = tmp_path / "node16.js"
    script_file.write_text(harness, encoding="utf-8")
    res = subprocess.run(["node", str(script_file)], capture_output=True, text=True, check=True)
    master_result = json.loads(res.stdout)[0]["json"]

    rankings = master_result["rankings"]
    assert rankings[0]["rank"] == 1
    assert rankings[1]["rank"] == 1
    assert rankings[2]["rank"] == 1
    assert rankings[3]["rank"] == 4

    assert master_result["comparison"]["winner_justification"][0].startswith("Joint Rank 1 Co-Winners")
