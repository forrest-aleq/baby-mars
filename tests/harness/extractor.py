"""
Scenario Extractor
===================

Uses Claude to extract structured test cases from persona scenario markdown files.
Generates YAML test specs for review and modification.

Supports both direct Anthropic API and Azure AI Foundry.
"""

import os
import re
import json
import yaml
from pathlib import Path
from typing import Optional
import anthropic
from anthropic import AnthropicFoundry

# Load .env file if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from .schema import PersonaSpec, TestCase, ExpectedOutput, ExpectedWorkUnit, ValidationRule, PersonaMetadata


def get_claude_client():
    """Get Claude client - supports Azure AI Foundry or direct Anthropic."""

    # Check for Azure AI Foundry configuration
    foundry_resource = os.environ.get("ANTHROPIC_FOUNDRY_RESOURCE")
    foundry_api_key = os.environ.get("ANTHROPIC_FOUNDRY_API_KEY")

    if foundry_resource and foundry_api_key:
        print(f"Using Azure AI Foundry: {foundry_resource}")
        return AnthropicFoundry(
            api_key=foundry_api_key,
            resource=foundry_resource,
        )

    # Fall back to direct Anthropic API
    return anthropic.Anthropic()


def get_model_name() -> str:
    """Get the model name to use."""
    # Use configured model or default
    return os.environ.get("ANTHROPIC_DEFAULT_SONNET_MODEL", "claude-sonnet-4-20250514")


EXTRACTION_PROMPT = """You are extracting test cases from a persona scenario document for Baby MARS (an AI agent for financial operations).

Analyze this persona scenario and extract:
1. Persona info (name, role, company, industry)
2. Metadata (difficulty, workflow_steps, decision_points, automation_susceptibility)
3. Test cases - concrete, testable scenarios from the workflow

For each test case:
- id: snake_case identifier (e.g., "weekly_bank_balance")
- description: What the test verifies
- input: The EXACT user message that would trigger this workflow
- expected:
  - supervision_mode: "autonomous" (routine, safe), "action_proposal" (needs approval), or "guidance_seeking" (needs help)
  - work_units: List of tool/verb/min_count objects the agent should generate
  - capabilities_used: Stargate capability keys (e.g., "qb.vendor.create", "plaid.balance.get")
  - should_escalate: Whether agent should ask human for help
  - should_flag_exceptions: Whether agent should flag edge cases/errors

Tools: erp, bank, email, documents, slack, crm, workflow, browser, stripe, billcom, netsuite, linear, asana, clickup, notion
Verbs: create_record, query_records, process_invoice, send, extract_data, approve_transaction, etc.

IMPORTANT: Generate realistic test cases that reflect the ACTUAL workflow described. Include both:
- Happy path (routine operations)
- Edge cases (exceptions, errors, unusual situations mentioned in the document)

Return a JSON object with this structure (note: use proper JSON, not placeholders):
{{
  "persona": {{"name": "Full Name", "role": "Job Title", "company": "Company Name", "industry": "industry_type"}},
  "metadata": {{"difficulty": 3, "workflow_steps": 89, "decision_points": 23, "automation_susceptibility": 2}},
  "test_cases": [
    {{
      "id": "example_test_id",
      "description": "What this test verifies",
      "input": "User message that triggers workflow",
      "expected": {{
        "supervision_mode": "autonomous",
        "work_units": [{{"tool": "erp", "verb": "query_records", "min_count": 1}}],
        "capabilities_used": ["qb.query"],
        "should_escalate": false,
        "should_flag_exceptions": false
      }},
      "tags": ["critical"]
    }}
  ]
}}

Scenario document:
---
{content}
---

Extract 3-8 test cases that cover the key workflows. Be specific with the user input messages."""


class ScenarioExtractor:
    """Extracts test cases from scenario markdown using Claude."""

    def __init__(self, client: Optional[anthropic.Anthropic] = None):
        self.client = client or get_claude_client()
        self.model = get_model_name()
        self.scenarios_dir = Path("docs/scenarios")
        self.output_dir = Path("tests/scenarios")

    def extract_persona(self, markdown_path: Path) -> PersonaSpec:
        """Extract test cases from a persona markdown file."""
        content = markdown_path.read_text()

        # Use Claude to extract structured test cases
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=[{
                "role": "user",
                "content": EXTRACTION_PROMPT.format(content=content)
            }]
        )

        # Parse JSON from response
        response_text = response.content[0].text

        # Extract JSON from response (handle markdown code blocks)
        json_match = re.search(r"```json?\s*(.*?)\s*```", response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to parse the whole response as JSON
            json_str = response_text

        data = json.loads(json_str)

        # Convert to PersonaSpec
        test_cases = []
        for tc in data.get("test_cases", []):
            expected_data = tc.get("expected", {})
            work_units = [
                ExpectedWorkUnit(**wu)
                for wu in expected_data.get("work_units", [])
            ]

            expected = ExpectedOutput(
                supervision_mode=expected_data.get("supervision_mode", "autonomous"),
                work_units=work_units,
                capabilities_used=expected_data.get("capabilities_used", []),
                should_escalate=expected_data.get("should_escalate", False),
                should_flag_exceptions=expected_data.get("should_flag_exceptions", False),
            )

            test_case = TestCase(
                id=tc["id"],
                description=tc["description"],
                input=tc["input"],
                expected=expected,
                tags=tc.get("tags", []),
            )
            test_cases.append(test_case)

        metadata = PersonaMetadata(**data.get("metadata", {}))

        return PersonaSpec(
            persona=data.get("persona", {}),
            metadata=metadata,
            test_cases=test_cases,
            source_file=str(markdown_path),
        )

    def save_spec(self, spec: PersonaSpec, output_path: Path) -> None:
        """Save PersonaSpec to YAML file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dict for YAML serialization
        data = spec.model_dump(exclude_none=True)

        with open(output_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    def load_spec(self, yaml_path: Path) -> PersonaSpec:
        """Load PersonaSpec from YAML file."""
        with open(yaml_path) as f:
            data = yaml.safe_load(f)
        return PersonaSpec(**data)

    def extract_all(self, company: Optional[str] = None) -> list[PersonaSpec]:
        """Extract all personas from scenarios directory."""
        specs = []
        scenarios_path = self.scenarios_dir

        if company:
            company_paths = [scenarios_path / company]
        else:
            company_paths = [p for p in scenarios_path.iterdir() if p.is_dir()]

        for company_dir in company_paths:
            if not company_dir.exists():
                continue

            for md_file in company_dir.glob("*.md"):
                # Skip README files
                if md_file.name.lower() == "readme.md":
                    continue

                print(f"Extracting: {md_file}")
                try:
                    spec = self.extract_persona(md_file)

                    # Save to output directory
                    persona_name = md_file.stem.lower().replace(" ", "_").replace("-", "_")
                    output_path = self.output_dir / company_dir.name / f"{persona_name}.yaml"
                    self.save_spec(spec, output_path)

                    specs.append(spec)
                    print(f"  -> {len(spec.test_cases)} test cases extracted")

                except Exception as e:
                    print(f"  ERROR: {e}")

        return specs

    def list_scenarios(self) -> list[dict]:
        """List all available scenarios without extracting."""
        scenarios = []

        for company_dir in self.scenarios_dir.iterdir():
            if not company_dir.is_dir():
                continue

            for md_file in company_dir.glob("*.md"):
                if md_file.name.lower() == "readme.md":
                    continue

                scenarios.append({
                    "company": company_dir.name,
                    "file": md_file.name,
                    "persona": md_file.stem,
                    "path": str(md_file),
                })

        return scenarios


def extract_single(persona_file: str) -> PersonaSpec:
    """Extract a single persona from a markdown file."""
    extractor = ScenarioExtractor()
    return extractor.extract_persona(Path(persona_file))


def extract_company(company: str) -> list[PersonaSpec]:
    """Extract all personas for a company."""
    extractor = ScenarioExtractor()
    return extractor.extract_all(company=company)


def extract_all() -> list[PersonaSpec]:
    """Extract all personas."""
    extractor = ScenarioExtractor()
    return extractor.extract_all()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Extract test cases from scenario markdown")
    parser.add_argument("--company", help="Extract only this company")
    parser.add_argument("--file", help="Extract single file")
    parser.add_argument("--list", action="store_true", help="List scenarios without extracting")
    args = parser.parse_args()

    extractor = ScenarioExtractor()

    if args.list:
        scenarios = extractor.list_scenarios()
        print(f"Found {len(scenarios)} scenarios:")
        for s in scenarios:
            print(f"  {s['company']}/{s['persona']}")
    elif args.file:
        spec = extract_single(args.file)
        print(f"Extracted {len(spec.test_cases)} test cases from {spec.name}")
    elif args.company:
        specs = extract_company(args.company)
        print(f"Extracted {len(specs)} personas")
    else:
        specs = extract_all()
        print(f"Extracted {len(specs)} personas total")
