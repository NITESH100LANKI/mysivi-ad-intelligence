"""Version 6 Regression Tests:
Verifying Docker Report Service Connectivity, Accurate 4-Ad Counting,
Strict Execution Status Logic (SUCCESS / PARTIAL_FAILURE / FAILED), and PDF Generation.
"""
import json
import os
import subprocess
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
import pytest

from backend.report.pdf_generator import generate_ad_intelligence_pdf

WORKFLOW_V6_FILE = Path("n8n/mysivi_ad_intelligence_workflow_v6.json")


def load_v6_workflow():
    assert WORKFLOW_V6_FILE.exists(), f"Workflow file not found: {WORKFLOW_V6_FILE}"
    with open(WORKFLOW_V6_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def load_v6_nodes():
    wf = load_v6_workflow()
    return wf, {n["name"]: n for n in wf["nodes"]}


def run_node_js(js_code, input_items, context_node_map=None):
    """Execute Node.js with mock $input and context querying support via temp file."""
    if context_node_map is None:
        context_node_map = {}

    harness = f"""
    const inputData = {json.dumps(input_items)};
    const contextData = {json.dumps(context_node_map)};

    const $input = {{
        all: () => inputData.map(item => ({{ json: item }})),
        first: () => ({{ json: inputData[0] || {{}} }})
    }};

    const $ = (nodeName) => ({{
        all: () => {{
            if (contextData[nodeName]) {{
                return contextData[nodeName].map(item => ({{ json: item }}));
            }}
            return inputData.map(item => ({{ json: item }}));
        }},
        first: () => ({{
            json: (contextData[nodeName] ? contextData[nodeName][0] : inputData[0]) || {{}}
        }}),
        item: {{ json: (contextData[nodeName] ? contextData[nodeName][0] : inputData[0]) || {{}} }}
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


# 1. Structure, service URL and node version check
def test_v6_nodes_structure_and_report_url():
    wf, nodes = load_v6_nodes()
    assert len(wf.get("nodes", [])) == 20

    init_node = nodes["Init Configuration"]
    assignments = init_node["parameters"]["assignments"]["assignments"]
    report_url_param = next(a for a in assignments if a["name"] == "REPORT_SERVICE_URL")
    assert report_url_param["value"] == "http://report-service:5000", (
        f"Expected http://report-service:5000, got {report_url_param['value']}"
    )

    pdf_node = nodes["Trigger PDF Report Generation"]
    assert "report-service:5000" in pdf_node["parameters"]["url"]
    assert "localhost" not in pdf_node["parameters"]["url"]


# 2. Score node prioritizes direct input ($input.all()) and analyzes all 4 ads
def test_v6_score_node_processes_all_four_ads():
    _, nodes = load_v6_nodes()
    score_js = nodes["Score, Rank & Synthesize Intelligence"]["parameters"]["jsCode"]

    valid_four_ads = [
        {"internal_id": "MYSIVI-AD-001", "headline": "Hindi", "hook": "H1", "cta": "Install now", "analysis": {"hook": {"score": 8.5}, "message_clarity": {"score": 9.0}, "value_prop_usp": {"score": 8.0}, "target_audience": {"score": 8.5}, "trust_social_proof": {"score": 6.0}, "cta_effectiveness": {"score": 7.5}, "creative_execution": {"score": 8.0}, "differentiation": {"score": 8.5}}},
        {"internal_id": "MYSIVI-AD-003", "headline": "Marathi", "hook": "H3", "cta": "Install now", "analysis": {"hook": {"score": 8.5}, "message_clarity": {"score": 9.0}, "value_prop_usp": {"score": 8.0}, "target_audience": {"score": 8.5}, "trust_social_proof": {"score": 6.0}, "cta_effectiveness": {"score": 7.5}, "creative_execution": {"score": 8.0}, "differentiation": {"score": 8.5}}},
        {"internal_id": "MYSIVI-AD-004", "headline": "Bengali", "hook": "H4", "cta": "Install now", "analysis": {"hook": {"score": 8.5}, "message_clarity": {"score": 9.0}, "value_prop_usp": {"score": 8.0}, "target_audience": {"score": 8.5}, "trust_social_proof": {"score": 6.0}, "cta_effectiveness": {"score": 7.5}, "creative_execution": {"score": 8.0}, "differentiation": {"score": 8.5}}},
        {"internal_id": "MYSIVI-AD-002", "headline": "{{product.name}}", "hook": "{{product.brand}}", "cta": "Install now", "analysis": {"hook": {"score": 0.0}, "message_clarity": {"score": 0.0}, "value_prop_usp": {"score": 0.0}, "target_audience": {"score": 1.0}, "trust_social_proof": {"score": 0.0}, "cta_effectiveness": {"score": 5.0}, "creative_execution": {"score": 0.0}, "differentiation": {"score": 0.0}}}
    ]

    out = run_node_js(score_js, valid_four_ads)
    master = out[0]["json"]
    assert len(master["advertisements"]) == 4
    assert len(master["rankings"]) == 4

    ranks = {r["internal_id"]: (r["rank"], r["score"]) for r in master["rankings"]}
    assert ranks["MYSIVI-AD-001"] == (1, 81.0)
    assert ranks["MYSIVI-AD-003"] == (1, 81.0)
    assert ranks["MYSIVI-AD-004"] == (1, 81.0)
    assert ranks["MYSIVI-AD-002"] == (4, 6.0)


# 3. Final Execution Summary: SUCCESS case when PDF generation succeeds
def test_v6_final_execution_summary_success():
    _, nodes = load_v6_nodes()
    summary_js = nodes["Final Execution Summary"]["parameters"]["jsCode"]

    master_scoring = {
        "execution_mode": "DATASET_REPLAY",
        "advertisements": [{"id": 1}, {"id": 2}, {"id": 3}, {"id": 4}],
        "rankings": [
            {"rank": 1, "internal_id": "MYSIVI-AD-001", "headline": "Hindi", "score": 81.0},
            {"rank": 1, "internal_id": "MYSIVI-AD-003", "headline": "Marathi", "score": 81.0},
            {"rank": 1, "internal_id": "MYSIVI-AD-004", "headline": "Bengali", "score": 81.0},
            {"rank": 4, "internal_id": "MYSIVI-AD-002", "headline": "Placeholder", "score": 6.0}
        ],
        "top_ad": {
            "rank": 1,
            "internal_id": "MYSIVI-AD-001",
            "headline": "Hindi",
            "score": {"total_score": 81.0},
            "hook": "H1"
        }
    }

    successful_pdf_res = [{
        "status": "success",
        "message": "PDF report successfully generated",
        "file_path": "/app/reports/MySivi_Ad_Intelligence_Report.pdf",
        "file_size_bytes": 23946
    }]

    context = {"Score, Rank & Synthesize Intelligence": [master_scoring]}
    out = run_node_js(summary_js, successful_pdf_res, context_node_map=context)
    summary = out[0]["json"]

    assert summary["status"] == "SUCCESS"
    assert summary["ads_analyzed"] == 4
    assert summary["pdf_generated"] is True
    assert len(summary["rankings"]) == 4
    assert summary["rankings"][0]["internal_id"] == "MYSIVI-AD-001"
    assert summary["rankings"][0]["rank"] == 1
    assert summary["rankings"][0]["score"] == 81.0
    assert summary["rankings"][3]["internal_id"] == "MYSIVI-AD-002"
    assert summary["rankings"][3]["rank"] == 4
    assert summary["rankings"][3]["score"] == 6.0


# 4. Final Execution Summary: PARTIAL_FAILURE case when PDF generation fails
def test_v6_final_execution_summary_partial_failure_on_pdf_error():
    _, nodes = load_v6_nodes()
    summary_js = nodes["Final Execution Summary"]["parameters"]["jsCode"]

    master_scoring = {
        "execution_mode": "DATASET_REPLAY",
        "advertisements": [{"id": 1}, {"id": 2}, {"id": 3}, {"id": 4}],
        "rankings": [
            {"rank": 1, "internal_id": "MYSIVI-AD-001", "headline": "Hindi", "score": 81.0},
            {"rank": 1, "internal_id": "MYSIVI-AD-003", "headline": "Marathi", "score": 81.0},
            {"rank": 1, "internal_id": "MYSIVI-AD-004", "headline": "Bengali", "score": 81.0},
            {"rank": 4, "internal_id": "MYSIVI-AD-002", "headline": "Placeholder", "score": 6.0}
        ],
        "top_ad": {"rank": 1, "internal_id": "MYSIVI-AD-001", "headline": "Hindi", "score": {"total_score": 81.0}, "hook": "H1"}
    }

    failed_pdf_res = [{
        "error": "connect ECONNREFUSED ::1:5000",
        "errorMessage": "connect ECONNREFUSED ::1:5000"
    }]

    context = {"Score, Rank & Synthesize Intelligence": [master_scoring]}
    out = run_node_js(summary_js, failed_pdf_res, context_node_map=context)
    summary = out[0]["json"]

    # Must NOT claim SUCCESS
    assert summary["status"] == "PARTIAL_FAILURE"
    assert summary["ads_analyzed"] == 4
    assert summary["pdf_generated"] is False
    assert "ECONNREFUSED" in str(summary["pdf_service_response"])


# 5. Final Execution Summary: FAILED case when scoring fails
def test_v6_final_execution_summary_failed():
    _, nodes = load_v6_nodes()
    summary_js = nodes["Final Execution Summary"]["parameters"]["jsCode"]

    master_empty = {
        "execution_mode": "DATASET_REPLAY",
        "advertisements": [],
        "rankings": []
    }

    context = {"Score, Rank & Synthesize Intelligence": [master_empty]}
    out = run_node_js(summary_js, [{}], context_node_map=context)
    summary = out[0]["json"]

    assert summary["status"] == "FAILED"
    assert summary["ads_analyzed"] == 0
    assert summary["pdf_generated"] is False


# 6. PDF Generation engine produces valid file
def test_v6_pdf_engine_generates_valid_report(tmp_path):
    fixture_path = Path("data/results/mysivi_analysis_results.json")
    assert fixture_path.exists()
    with open(fixture_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    out_file = tmp_path / "v6_test_report.pdf"
    gen_file = generate_ad_intelligence_pdf(data, out_file)

    assert gen_file.exists()
    assert os.path.getsize(gen_file) > 10000
    with open(gen_file, "rb") as f:
        header = f.read(5)
        assert header == b"%PDF-"


# 7. Verification that Docker service host mapping is correct
def test_v6_docker_service_host_naming():
    docker_compose_path = Path("docker-compose.yml")
    assert docker_compose_path.exists()
    with open(docker_compose_path, "r", encoding="utf-8") as f:
        dc_text = f.read()

    assert "report-service:" in dc_text
    assert "mysivi-network" in dc_text
    assert "mysivi-report-service" in dc_text
