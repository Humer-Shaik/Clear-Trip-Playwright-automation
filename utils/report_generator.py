from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from openpyxl import Workbook


@dataclass
class TestResult:
    test_id: str
    from_city: str
    to_city: str
    journey_type: str
    status: str
    duration_seconds: float
    message: str
    screenshot_path: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))


class ReportGenerator:
    def __init__(self, reports_dir: Path) -> None:
        self.reports_dir = reports_dir
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.results: list[TestResult] = []

    def add_result(self, result: TestResult) -> None:
        self.results.append(result)

    def _summary(self) -> dict[str, Any]:
        passed = sum(1 for result in self.results if result.status == "PASSED")
        failed = sum(1 for result in self.results if result.status == "FAILED")
        skipped = sum(1 for result in self.results if result.status == "SKIPPED")
        return {
            "total": len(self.results),
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "pass_rate": round((passed / len(self.results)) * 100, 2) if self.results else 0.0,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
        }

    def write_json_report(self, filename: str = "execution_summary.json") -> Path:
        payload = {"summary": self._summary(), "results": [asdict(result) for result in self.results]}
        output_path = self.reports_dir / filename
        output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return output_path

    def write_excel_report(self, filename: str = "test_execution_report.xlsx") -> Path:
        workbook = Workbook()
        summary_sheet = workbook.active
        summary_sheet.title = "Summary"

        summary = self._summary()
        summary_sheet.append(["Metric", "Value"])
        for key, value in summary.items():
            summary_sheet.append([key, value])

        details_sheet = workbook.create_sheet("TestResults")
        details_sheet.append(
            [
                "Test ID",
                "From",
                "To",
                "Journey Type",
                "Status",
                "Duration (s)",
                "Message",
                "Screenshot",
                "Timestamp",
            ]
        )
        for result in self.results:
            details_sheet.append(
                [
                    result.test_id,
                    result.from_city,
                    result.to_city,
                    result.journey_type,
                    result.status,
                    result.duration_seconds,
                    result.message,
                    result.screenshot_path,
                    result.timestamp,
                ]
            )

        output_path = self.reports_dir / filename
        workbook.save(output_path)
        workbook.close()
        return output_path

    def write_text_summary(self, filename: str = "execution_summary.txt") -> Path:
        summary = self._summary()
        lines = [
            "=" * 60,
            "CLEARTrip FLIGHT SEARCH - EXECUTION SUMMARY",
            "=" * 60,
            f"Generated At : {summary['generated_at']}",
            f"Total Tests  : {summary['total']}",
            f"Passed       : {summary['passed']}",
            f"Failed       : {summary['failed']}",
            f"Skipped      : {summary['skipped']}",
            f"Pass Rate    : {summary['pass_rate']}%",
            "-" * 60,
        ]
        for result in self.results:
            lines.append(
                f"[{result.status}] {result.test_id} | {result.from_city} -> {result.to_city} "
                f"| {result.duration_seconds:.1f}s | {result.message}"
            )
        lines.append("=" * 60)

        output_path = self.reports_dir / filename
        output_path.write_text("\n".join(lines), encoding="utf-8")
        return output_path

    def write_all_reports(self) -> dict[str, Path]:
        return {
            "json": self.write_json_report(),
            "excel": self.write_excel_report(),
            "text": self.write_text_summary(),
        }
