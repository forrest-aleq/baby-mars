"""
Test Report Generator
======================

Generates formatted reports from test harness results.
Supports CLI, JSON, and HTML output formats.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from .schema import HarnessReport, CompanyResult, PersonaResult, TestCaseResult


def get_status_indicator(score: float, threshold: float = 96.0) -> tuple[str, str]:
    """Get status indicator and color for a score."""
    if score >= threshold:
        return ("READY", "green")
    elif score >= 70:
        return ("PARTIAL", "yellow")
    elif score >= 50:
        return ("LIMITED", "orange")
    else:
        return ("NOT READY", "red")


class Reporter:
    """Generates reports from harness results."""

    def __init__(self, report: HarnessReport):
        self.report = report

    def to_cli(self) -> str:
        """Generate CLI-formatted report."""
        lines = []
        r = self.report

        lines.append("")
        lines.append("=" * 60)
        lines.append("Baby MARS Readiness Report")
        lines.append("=" * 60)
        lines.append("")

        status, _ = get_status_indicator(r.overall_score, r.pass_threshold)
        passed_str = "PASSED" if r.passed else "FAILED"

        lines.append(f"Overall Score: {r.overall_score:.1f}% [{status}]")
        lines.append(f"Result: {passed_str} (threshold: {r.pass_threshold}%)")
        lines.append("")

        # Company breakdown
        lines.append("By Company:")
        for cr in r.company_results:
            status, _ = get_status_indicator(cr.score, r.pass_threshold)
            lines.append(f"  {cr.company:20} {cr.score:5.1f}% [{status}] ({cr.total_personas} personas)")

        lines.append("")

        # Top failures
        if r.top_failures:
            lines.append("Top Failures:")
            for f in r.top_failures[:5]:
                lines.append(f"  X {f['persona']}/{f['test_case']} - {f['score']:.1f}%")
                for err in f.get("errors", [])[:1]:
                    lines.append(f"      {err}")
            lines.append("")

        # Recommendations
        if r.recommendations:
            lines.append("Recommendations:")
            for i, rec in enumerate(r.recommendations, 1):
                lines.append(f"  {i}. {rec}")
            lines.append("")

        # Summary
        lines.append("-" * 60)
        lines.append(f"Execution Time: {r.execution_time_ms/1000:.1f}s")
        lines.append(f"Total: {r.total_tests} tests, {r.passed_tests} passed, {r.failed_tests} failed")
        lines.append(f"Personas: {r.total_personas}")
        lines.append("=" * 60)
        lines.append("")

        return "\n".join(lines)

    def to_json(self) -> str:
        """Generate JSON report."""
        return json.dumps(self.report.model_dump(), indent=2, default=str)

    def to_html(self) -> str:
        """Generate HTML report."""
        r = self.report
        status, color = get_status_indicator(r.overall_score, r.pass_threshold)

        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Baby MARS Readiness Report</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 40px; background: #f5f5f5; }}
        .container {{ max-width: 1000px; margin: 0 auto; background: white; padding: 40px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; margin-bottom: 10px; }}
        .score {{ font-size: 48px; font-weight: bold; color: {color}; }}
        .status {{ display: inline-block; padding: 4px 12px; border-radius: 4px; background: {color}; color: white; font-weight: bold; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #eee; }}
        th {{ background: #f9f9f9; font-weight: 600; }}
        .passed {{ color: green; }}
        .failed {{ color: red; }}
        .failure {{ background: #fff5f5; padding: 10px; margin: 10px 0; border-left: 3px solid red; }}
        .recommendation {{ background: #f0f7ff; padding: 10px; margin: 5px 0; border-left: 3px solid #0066cc; }}
        .meta {{ color: #666; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Baby MARS Readiness Report</h1>
        <p class="meta">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

        <div style="margin: 30px 0;">
            <span class="score">{r.overall_score:.1f}%</span>
            <span class="status">{status}</span>
            <span style="margin-left: 20px;">{'PASSED' if r.passed else 'FAILED'} (threshold: {r.pass_threshold}%)</span>
        </div>

        <h2>Results by Company</h2>
        <table>
            <tr>
                <th>Company</th>
                <th>Score</th>
                <th>Status</th>
                <th>Personas</th>
                <th>Tests</th>
                <th>Passed</th>
            </tr>
"""

        for cr in r.company_results:
            status, color = get_status_indicator(cr.score, r.pass_threshold)
            html += f"""
            <tr>
                <td><strong>{cr.company}</strong></td>
                <td>{cr.score:.1f}%</td>
                <td style="color: {color};">{status}</td>
                <td>{cr.total_personas}</td>
                <td>{cr.total_tests}</td>
                <td>{cr.passed_tests}</td>
            </tr>
"""

        html += """
        </table>
"""

        if r.top_failures:
            html += """
        <h2>Top Failures</h2>
"""
            for f in r.top_failures[:10]:
                html += f"""
        <div class="failure">
            <strong>{f['persona']}/{f['test_case']}</strong> - {f['score']:.1f}%
            <ul>
"""
                for err in f.get("errors", []):
                    html += f"<li>{err}</li>\n"
                html += "</ul></div>\n"

        if r.recommendations:
            html += """
        <h2>Recommendations</h2>
"""
            for rec in r.recommendations:
                html += f'<div class="recommendation">{rec}</div>\n'

        html += f"""
        <h2>Summary</h2>
        <ul>
            <li>Total Personas: {r.total_personas}</li>
            <li>Total Tests: {r.total_tests}</li>
            <li>Passed: {r.passed_tests} ({r.passed_tests/r.total_tests*100 if r.total_tests else 0:.1f}%)</li>
            <li>Failed: {r.failed_tests}</li>
            <li>Execution Time: {r.execution_time_ms/1000:.1f}s</li>
        </ul>
    </div>
</body>
</html>
"""
        return html

    def save(self, output_path: Path, format: str = "auto"):
        """Save report to file."""
        if format == "auto":
            if output_path.suffix == ".json":
                format = "json"
            elif output_path.suffix == ".html":
                format = "html"
            else:
                format = "txt"

        if format == "json":
            content = self.to_json()
        elif format == "html":
            content = self.to_html()
        else:
            content = self.to_cli()

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content)


def generate_cli_report(report: HarnessReport) -> str:
    """Generate CLI report from HarnessReport."""
    return Reporter(report).to_cli()


def generate_json_report(report: HarnessReport) -> str:
    """Generate JSON report from HarnessReport."""
    return Reporter(report).to_json()


def generate_html_report(report: HarnessReport) -> str:
    """Generate HTML report from HarnessReport."""
    return Reporter(report).to_html()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate report from harness results")
    parser.add_argument("input", help="Input JSON file with harness results")
    parser.add_argument("--output", "-o", help="Output file path")
    parser.add_argument("--format", choices=["cli", "json", "html"], default="cli")
    args = parser.parse_args()

    # Load results
    with open(args.input) as f:
        data = json.load(f)
    report = HarnessReport(**data)

    # Generate report
    reporter = Reporter(report)

    if args.output:
        reporter.save(Path(args.output), args.format)
        print(f"Report saved to {args.output}")
    else:
        if args.format == "json":
            print(reporter.to_json())
        elif args.format == "html":
            print(reporter.to_html())
        else:
            print(reporter.to_cli())
