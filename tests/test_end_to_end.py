"""End-to-end integration test executing the complete pipeline."""
import os
from pathlib import Path
import pytest
from run_pipeline import run_ad_intelligence_pipeline
from backend.utils.config import get_settings


def test_end_to_end_pipeline_mock_execution(tmp_path):
    settings = get_settings()
    test_results_json = tmp_path / "test_mysivi_results.json"
    test_report_pdf = tmp_path / "test_report.pdf"

    master_result = run_ad_intelligence_pipeline(
        mode="mock",
        max_items=10,
        output_results_file=test_results_json,
        output_pdf_file=test_report_pdf
    )

    # 1. Structure assertions
    assert master_result["project"] == "MySivi Ad Intelligence"
    assert "Meta Ad Library" in master_result["source"] or "Facebook Ad Library" in master_result["source"]
    assert len(master_result["advertisements"]) >= 5

    # 2. Ranking assertions
    rankings = master_result["rankings"]
    assert rankings[0]["rank"] == 1
    assert rankings[0]["is_best_creative"] is True
    # Verify descending score sort
    for i in range(len(rankings) - 1):
        assert rankings[i]["score"] >= rankings[i + 1]["score"]

    # 3. Deliverables assertions (written to isolated test paths)
    assert test_report_pdf.exists()
    assert os.path.getsize(test_report_pdf) > 10000

    assert test_results_json.exists()
    assert os.path.getsize(test_results_json) > 1000

    # 4. Strategic recommendations
    assert len(master_result["recommendations"]) == 3
    assert len(master_result["marketing_insights"]) >= 3
    assert len(master_result["limitations"]) >= 3

