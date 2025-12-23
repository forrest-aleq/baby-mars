"""
Claude Client Wrapper
======================

Async client for Claude API with structured outputs support.
Supports both direct Anthropic API and Azure AI Foundry.

Uses the latest Anthropic SDK (December 2025) features:
- Structured outputs (beta)
- Tool use with strict schemas
- Streaming support
"""

import json
import os
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from pathlib import Path
from time import time
from typing import Any, Optional, Type, TypeVar, Union, cast

from anthropic import (
    APIConnectionError,
    APIError,
    AsyncAnthropic,
    AsyncAnthropicFoundry,
    RateLimitError,
)
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

# Load .env file if present
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

# Default model - can be overridden by env var for Azure Foundry
DEFAULT_MODEL = os.environ.get("ANTHROPIC_DEFAULT_SONNET_MODEL", "claude-sonnet-4-5-20250929")

# Beta header for structured outputs
STRUCTURED_OUTPUTS_BETA = "structured-outputs-2025-11-13"


# ============================================================
# CIRCUIT BREAKER
# ============================================================


@dataclass
class CircuitBreaker:
    """
    Circuit breaker for Claude API calls.

    Prevents cascading failures by temporarily blocking requests
    when the API is failing repeatedly.
    """

    failure_threshold: int = 5
    reset_timeout: float = 60.0
    failures: int = field(default=0, init=False)
    last_failure: float = field(default=0.0, init=False)

    def record_failure(self) -> None:
        """Record a failure and update timestamp."""
        self.failures += 1
        self.last_failure = time()

    def record_success(self) -> None:
        """Reset failures on success."""
        self.failures = 0

    def is_open(self) -> bool:
        """Check if circuit is open (blocking requests)."""
        if self.failures >= self.failure_threshold:
            # Check if enough time passed to try again (half-open)
            if time() - self.last_failure > self.reset_timeout:
                self.failures = 0  # Reset and allow retry
                return False
            return True
        return False

    def check_or_raise(self) -> None:
        """Raise if circuit is open."""
        if self.is_open():
            raise CircuitBreakerOpenError(
                f"Claude API circuit breaker open after {self.failure_threshold} failures. "
                f"Retry after {self.reset_timeout}s."
            )


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open."""

    pass


# Backwards compatible alias
CircuitBreakerOpen = CircuitBreakerOpenError


# Global circuit breaker for Claude API
_circuit_breaker = CircuitBreaker()


@dataclass
class ClaudeConfig:
    """Configuration for Claude client"""

    model: str = DEFAULT_MODEL
    max_tokens: int = 4096
    temperature: float = 0.7
    use_structured_outputs: bool = True


class ClaudeClient:
    """
    Async Claude client wrapper for Baby MARS.

    Features:
    - Skills loading from markdown files
    - Structured outputs for reliable JSON responses
    - Tool use for MCP integration
    - Conversation history management
    """

    client: Union[AsyncAnthropic, AsyncAnthropicFoundry]
    using_foundry: bool

    def __init__(
        self, config: Optional[ClaudeConfig] = None, skills_dir: Optional[Path] = None
    ) -> None:
        self.config = config or ClaudeConfig()

        # Check for Azure AI Foundry configuration
        foundry_resource = os.environ.get("ANTHROPIC_FOUNDRY_RESOURCE")
        foundry_api_key = os.environ.get("ANTHROPIC_FOUNDRY_API_KEY")

        if foundry_resource and foundry_api_key:
            # Use Azure AI Foundry with proper Foundry client
            self.client = AsyncAnthropicFoundry(
                api_key=foundry_api_key,
                resource=foundry_resource,
            )
            self.using_foundry = True
        else:
            # Use direct Anthropic API
            self.client = AsyncAnthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
            self.using_foundry = False

        self.skills_dir = skills_dir or Path(__file__).parent / "skills"
        self._skills_cache: dict[str, str] = {}

    # ============================================================
    # SKILL MANAGEMENT
    # ============================================================

    def load_skill(self, skill_name: str) -> str:
        """
        Load a skill (system prompt) from markdown file.

        Skills are stored as .md files in the skills directory.
        They contain domain-specific instructions for Claude.
        """
        if skill_name in self._skills_cache:
            return self._skills_cache[skill_name]

        skill_path = self.skills_dir / f"{skill_name}.md"

        if not skill_path.exists():
            raise FileNotFoundError(f"Skill not found: {skill_path}")

        skill_content = skill_path.read_text()
        self._skills_cache[skill_name] = skill_content

        return skill_content

    def build_system_prompt(self, skills: list[str]) -> str:
        """
        Build system prompt by combining multiple skills.

        Args:
            skills: List of skill names to load and combine

        Returns:
            Combined system prompt
        """
        parts = []

        for skill in skills:
            try:
                content = self.load_skill(skill)
                parts.append(f'<skill name="{skill}">\n{content}\n</skill>')
            except FileNotFoundError:
                # Skip missing skills with warning
                print(f"Warning: Skill '{skill}' not found, skipping")

        return "\n\n".join(parts)

    # ============================================================
    # BASIC COMPLETION
    # ============================================================

    async def complete(
        self,
        messages: list[dict[str, Any]],
        system: Optional[str] = None,
        skills: Optional[list[str]] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """
        Basic completion - returns text response.

        Args:
            messages: Conversation history in Claude format
            system: System prompt (overrides skills)
            skills: List of skill names to use for system prompt
            temperature: Override default temperature

        Returns:
            Text response from Claude
        """
        # Check circuit breaker
        _circuit_breaker.check_or_raise()

        # Build system prompt
        if system is None and skills:
            system = self.build_system_prompt(skills)

        try:
            # Call Claude
            response = await self.client.messages.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                temperature=temperature or self.config.temperature,
                system=system or "",
                messages=cast(Any, messages),
            )
            _circuit_breaker.record_success()
            # Extract text - content[0] is always TextBlock for text completions
            first_block = response.content[0]
            if hasattr(first_block, "text"):
                return first_block.text
            raise ValueError("Response did not contain text block")
        except (RateLimitError, APIConnectionError, APIError):
            _circuit_breaker.record_failure()
            raise

    # ============================================================
    # STRUCTURED OUTPUTS (Beta)
    # ============================================================

    async def complete_structured(
        self,
        messages: list[dict[str, Any]],
        response_model: Type[T],
        system: Optional[str] = None,
        skills: Optional[list[str]] = None,
        temperature: Optional[float] = None,
    ) -> T:
        """
        Completion with structured output.

        Uses JSON mode with schema in prompt for Azure Foundry compatibility.

        Args:
            messages: Conversation history
            response_model: Pydantic model class for response
            system: System prompt
            skills: Skills to use
            temperature: Temperature override

        Returns:
            Instance of response_model with parsed response
        """
        _circuit_breaker.check_or_raise()

        if system is None and skills:
            system = self.build_system_prompt(skills)

        # Add JSON schema to system prompt for structured output
        schema = response_model.model_json_schema()
        schema_prompt = f"\n\nRespond with valid JSON matching this schema:\n{json.dumps(schema, indent=2)}\n\nOutput ONLY valid JSON, no other text."

        full_system = (system or "") + schema_prompt

        try:
            response = await self.client.messages.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                temperature=temperature or self.config.temperature,
                system=full_system,
                messages=cast(Any, messages),
            )
            _circuit_breaker.record_success()

            # Parse JSON response into model
            first_block = response.content[0]
            if not hasattr(first_block, "text"):
                raise ValueError("Response did not contain text block")
            response_text: str = first_block.text
            # Handle potential markdown code blocks
            if response_text.startswith("```"):
                import re

                match = re.search(r"```(?:json)?\s*(.*?)\s*```", response_text, re.DOTALL)
                if match:
                    response_text = match.group(1)

            data = json.loads(response_text)
            return response_model(**data)
        except (RateLimitError, APIConnectionError, APIError):
            _circuit_breaker.record_failure()
            raise

    async def complete_json(
        self,
        messages: list[dict[str, Any]],
        schema: dict[str, Any],
        system: Optional[str] = None,
        skills: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """
        Completion with JSON schema validation.

        For cases where you have a raw JSON schema instead of Pydantic.

        Args:
            messages: Conversation history
            schema: JSON schema dict
            system: System prompt
            skills: Skills to use

        Returns:
            Parsed JSON dict matching schema
        """
        _circuit_breaker.check_or_raise()

        if system is None and skills:
            system = self.build_system_prompt(skills)

        try:
            response = await self.client.beta.messages.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                betas=[STRUCTURED_OUTPUTS_BETA],
                system=system or "",
                messages=cast(Any, messages),
                output_format=cast(Any, {"type": "json_schema", "schema": schema}),
            )
            _circuit_breaker.record_success()
            first_block = response.content[0]
            if hasattr(first_block, "text"):
                result: dict[str, Any] = json.loads(first_block.text)
                return result
            raise ValueError("Response did not contain text block")
        except (RateLimitError, APIConnectionError, APIError):
            _circuit_breaker.record_failure()
            raise

    # ============================================================
    # TOOL USE
    # ============================================================

    async def complete_with_tools(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        system: Optional[str] = None,
        skills: Optional[list[str]] = None,
        tool_choice: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Completion with tool use.

        Args:
            messages: Conversation history
            tools: Tool definitions (name, description, input_schema)
            system: System prompt
            skills: Skills to use
            tool_choice: Optional tool choice constraint

        Returns:
            Full response including tool_use blocks
        """
        if system is None and skills:
            system = self.build_system_prompt(skills)

        kwargs: dict[str, Any] = {
            "model": self.config.model,
            "max_tokens": self.config.max_tokens,
            "system": system or "",
            "messages": messages,
            "tools": tools,
        }

        if tool_choice:
            kwargs["tool_choice"] = tool_choice

        response = await self.client.messages.create(**kwargs)

        # Parse response into structured format
        result: dict[str, Any] = {
            "text_blocks": [],
            "tool_use_blocks": [],
            "stop_reason": response.stop_reason,
        }

        for block in response.content:
            if block.type == "text":
                result["text_blocks"].append(block.text)
            elif block.type == "tool_use":
                result["tool_use_blocks"].append(
                    {"id": block.id, "name": block.name, "input": block.input}
                )

        return result

    # ============================================================
    # STREAMING
    # ============================================================

    async def stream(
        self,
        messages: list[dict[str, Any]],
        system: Optional[str] = None,
        skills: Optional[list[str]] = None,
    ) -> AsyncIterator[str]:
        """
        Stream completion tokens.

        Yields text chunks as they arrive.
        """
        if system is None and skills:
            system = self.build_system_prompt(skills)

        async with self.client.messages.stream(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            system=system or "",
            messages=cast(Any, messages),
        ) as stream:
            async for text in stream.text_stream:
                yield text


# ============================================================
# PYDANTIC MODELS FOR STRUCTURED OUTPUTS
# ============================================================


class AppraisalOutput(BaseModel):
    """Structured output for appraisal node"""

    face_threat_level: float  # 0.0-1.0
    expectancy_violation: Optional[str]
    goal_alignment: dict[str, float]  # goal_id -> alignment score
    urgency: float  # 0.0-1.0
    uncertainty_areas: list[str]
    recommended_approach: str  # "seek_guidance", "propose_action", "execute"
    relevant_belief_ids: list[str]
    difficulty_assessment: int  # 1-5
    involves_ethical_beliefs: bool
    reasoning: str


class ActionSelectionOutput(BaseModel):
    """Structured output for action selection node"""

    action_type: str
    work_units: list[dict[str, Any]]
    tool_requirements: list[str]
    confidence: float
    requires_human_approval: bool
    approval_reason: Optional[str]
    estimated_difficulty: int


class ValidationOutput(BaseModel):
    """Structured output for validation node"""

    all_passed: bool
    results: list[dict[str, Any]]  # ValidationResult items
    recommended_action: str  # "proceed", "retry", "escalate"
    fix_suggestions: list[str]


class ResponseOutput(BaseModel):
    """Structured output for response generation"""

    main_content: str
    tone: str  # "professional", "explanatory", "apologetic", etc.
    action_items: list[str] = []
    questions: list[str] = []  # For guidance_seeking mode
    confirmation_prompt: Optional[str] = None  # For action_proposal mode
    awaiting_input: bool = False


class DialecticalOutput(BaseModel):
    """Structured output for dialectical resolution"""

    synthesis: str
    chosen_goal_id: str
    deferred_goal_ids: list[str]
    resolution_reasoning: str
    requires_human_input: bool


# Backwards-compatible re-exports from singleton module
from .claude_singleton import get_claude_client

__all__ = [
    "ClaudeClient",
    "ClaudeConfig",
    "CircuitBreaker",
    "CircuitBreakerOpenError",
    "get_claude_client",
    "AppraisalOutput",
    "ActionSelectionOutput",
    "ValidationOutput",
    "ResponseOutput",
    "DialecticalOutput",
]
