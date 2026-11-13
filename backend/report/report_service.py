"""Microservice providing HTTP endpoints for PDF report generation and download."""
import json
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Dict, Any

from .pdf_generator import generate_ad_intelligence_pdf
from ..utils.config import get_settings
from ..utils.logger import setup_logger

logger = setup_logger("ReportService")


class ReportRequestHandler(BaseHTTPRequestHandler):
    """HTTP Request Handler for report generation and health checks."""

    def _set_headers(self, status: int = 200, content_type: str = "application/json"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(200)

    def do_GET(self):
        settings = get_settings()
        if self.path == "/health":
            self._set_headers(200)
            self.wfile.write(json.dumps({
                "status": "healthy",
                "service": "MySivi Report Generation Service",
                "pdf_engine": "ReportLab",
                "default_pdf_path": str(settings.REPORTS_DIR / "MySivi_Ad_Intelligence_Report.pdf")
            }).encode("utf-8"))
        elif self.path == "/download-report":
            pdf_path = settings.REPORTS_DIR / "MySivi_Ad_Intelligence_Report.pdf"
            if pdf_path.exists():
                self.send_response(200)
                self.send_header("Content-Type", "application/pdf")
                self.send_header("Content-Disposition", 'attachment; filename="MySivi_Ad_Intelligence_Report.pdf"')
                self.end_headers()
                with open(pdf_path, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self._set_headers(404)
                self.wfile.write(json.dumps({"error": "Report PDF not yet generated"}).encode("utf-8"))
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Not found"}).encode("utf-8"))

    def do_POST(self):
        settings = get_settings()
        if self.path in ("/generate-report", "/api/generate-report"):
            try:
                content_len = int(self.headers.get("Content-Length", 0))
                post_body = self.rfile.read(content_len)
                data = json.loads(post_body.decode("utf-8")) if post_body else {}

                output_path = settings.REPORTS_DIR / "MySivi_Ad_Intelligence_Report.pdf"
                generated_path = generate_ad_intelligence_pdf(data, output_path)

                response_payload = {
                    "status": "success",
                    "message": "PDF report successfully generated",
                    "file_path": str(generated_path),
                    "file_size_bytes": os.path.getsize(generated_path),
                    "download_url": f"http://localhost:{settings.PORT_REPORT_SERVICE}/download-report"
                }
                self._set_headers(200)
                self.wfile.write(json.dumps(response_payload).encode("utf-8"))
            except Exception as e:
                logger.error(f"Error generating PDF via service: {e}")
                self._set_headers(500)
                self.wfile.write(json.dumps({"status": "error", "error": str(e)}).encode("utf-8"))
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode("utf-8"))


def run_service(port: int = 5000):
    """Start the Report Generation HTTP server."""
    settings = get_settings()
    server_address = ("", port)
    httpd = HTTPServer(server_address, ReportRequestHandler)
    logger.info(f"Report Generation Service listening on http://0.0.0.0:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Report Service stopping...")
        httpd.server_close()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    run_service(port)

