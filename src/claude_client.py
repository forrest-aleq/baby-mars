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
from dataclasses import dataclass
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

from .claude_models import (
    ActionSelectionOutput,
    AppraisalOutput,
    DialecticalOutput,
    ResponseOutput,
    ValidationOutput,
)
from .observability import get_instrumentation, get_logger
from .utils.retry import CircuitBreaker, CircuitOpenError, RetryConfig, RetryStrategy, retry_async

T = TypeVar("T", bound=BaseModel)
logger = get_logger(__name__)

# Load .env file if present
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

DEFAULT_MODEL = os.environ.get("ANTHROPIC_DEFAULT_SONNET_MODEL", "claude-sonnet-4-5-20250929")
STRUCTURED_OUTPUTS_BETA = "structured-outputs-2025-11-13"

# Retry config for Claude API
CLAUDE_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    base_delay=1.0,
    max_delay=30.0,
    strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
    jitter=True,
    retryable_exceptions=(RateLimitError, APIConnectionError, APIError),
)

# Global circuit breaker
_circuit_breaker = CircuitBreaker(failure_threshold=5, reset_timeout=60.0)

# Backwards compatible aliases
CircuitBreakerOpenError = CircuitOpenError
CircuitBreakerOpen = CircuitOpenError


def _check_circuit() -> None:
    """Check circuit breaker before API call."""
    if not _circuit_breaker.can_execute():
        raise CircuitOpenError(
            f"Claude API circuit breaker open. Retry after {_circuit_breaker.reset_timeout}s.",
            reset_after=_circuit_breaker.get_reset_time(),
        )


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

    async def _do_complete(
        self,
        messages: list[dict[str, Any]],
        system: str,
        temperature: float,
        node_name: str,
    ) -> str:
        """Internal completion call - wrapped with retry logic."""
        start_time = time()
        response = await self.client.messages.create(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            temperature=temperature,
            system=system,
            messages=cast(Any, messages),
        )
        self._track_response(response, node_name, start_time)
        return self._extract_text(response)

    async def complete(
        self,
        messages: list[dict[str, Any]],
        system: Optional[str] = None,
        skills: Optional[list[str]] = None,
        temperature: Optional[float] = None,
        node_name: str = "unknown",
    ) -> str:
        """Basic completion - returns text response with automatic retry."""
        _check_circuit()
        if system is None and skills:
            system = self.build_system_prompt(skills)

        def on_retry(attempt: int, error: Exception, delay: float) -> None:
            logger.warning(f"Claude API retry {attempt + 1}: {error}, waiting {delay:.1f}s")
            _circuit_breaker.record_failure()

        try:
            return await retry_async(
                self._do_complete,
                args=(messages, system or "", temperature or self.config.temperature, node_name),
                config=CLAUDE_RETRY_CONFIG,
                on_retry=on_retry,
            )
        except Exception:
            _circuit_breaker.record_failure()
            raise

    def _track_response(self, response: Any, node_name: str, start_time: float) -> None:
        """Track response metrics and record success."""
        latency_ms = (time() - start_time) * 1000
        _circuit_breaker.record_success()
        inst = get_instrumentation()
        inst.on_claude_call(
            node_name, response.usage.input_tokens, response.usage.output_tokens, latency_ms
        )

    def _extract_text(self, response: Any) -> str:
        """Extract text from response content."""
        first_block = response.content[0]
        if hasattr(first_block, "text"):
            return str(first_block.text)
        raise ValueError("Response did not contain text block")

    # ============================================================
    # STRUCTURED OUTPUTS (Beta)
    # ============================================================

    async def _do_complete_structured(
        self,
        messages: list[dict[str, Any]],
        response_model: Type[T],
        full_system: str,
        temperature: float,
        node_name: str,
    ) -> T:
        """Internal structured completion call - wrapped with retry logic."""
        start_time = time()
        response = await self.client.messages.create(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            temperature=temperature,
            system=full_system,
            messages=cast(Any, messages),
        )
        self._track_response(response, node_name, start_time)
        return self._parse_structured_response(response, response_model)

    async def complete_structured(
        self,
        messages: list[dict[str, Any]],
        response_model: Type[T],
        system: Optional[str] = None,
        skills: Optional[list[str]] = None,
        temperature: Optional[float] = None,
        node_name: str = "unknown",
    ) -> T:
        """Completion with structured output using JSON mode with automatic retry."""
        _check_circuit()
        if system is None and skills:
            system = self.build_system_prompt(skills)

        schema = response_model.model_json_schema()
        schema_prompt = f"\n\nRespond with valid JSON matching this schema:\n{json.dumps(schema, indent=2)}\n\nOutput ONLY valid JSON."
        full_system = (system or "") + schema_prompt

        def on_retry(attempt: int, error: Exception, delay: float) -> None:
            logger.warning(f"Claude API retry {attempt + 1}: {error}, waiting {delay:.1f}s")
            _circuit_breaker.record_failure()

        try:
            return await retry_async(
                self._do_complete_structured,
                args=(
                    messages,
                    response_model,
                    full_system,
                    temperature or self.config.temperature,
                    node_name,
                ),
                config=CLAUDE_RETRY_CONFIG,
                on_retry=on_retry,
            )
        except Exception:
            _circuit_breaker.record_failure()
            raise

    def _parse_structured_response(self, response: Any, response_model: Type[T]) -> T:
        """Parse JSON response into Pydantic model."""
        import re

        text = self._extract_text(response)
        if text.startswith("```"):
            match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
            if match:
                text = match.group(1)
        return response_model(**json.loads(text))

    async def _do_complete_json(
        self,
        messages: list[dict[str, Any]],
        schema: dict[str, Any],
        system: str,
        node_name: str,
    ) -> dict[str, Any]:
        """Internal JSON completion call - wrapped with retry logic."""
        start_time = time()
        response = await self.client.beta.messages.create(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            betas=[STRUCTURED_OUTPUTS_BETA],
            system=system,
            messages=cast(Any, messages),
            output_format=cast(Any, {"type": "json_schema", "schema": schema}),
        )
        self._track_response(response, node_name, start_time)
        return self._parse_json_response(response)

    async def complete_json(
        self,
        messages: list[dict[str, Any]],
        schema: dict[str, Any],
        system: Optional[str] = None,
        skills: Optional[list[str]] = None,
        node_name: str = "unknown",
    ) -> dict[str, Any]:
        """Completion with JSON schema validation with automatic retry."""
        _check_circuit()
        if system is None and skills:
            system = self.build_system_prompt(skills)

        def on_retry(attempt: int, error: Exception, delay: float) -> None:
            logger.warning(f"Claude API retry {attempt + 1}: {error}, waiting {delay:.1f}s")
            _circuit_breaker.record_failure()

        try:
            return await retry_async(
                self._do_complete_json,
                args=(messages, schema, system or "", node_name),
                config=CLAUDE_RETRY_CONFIG,
                on_retry=on_retry,
            )
        except Exception:
            _circuit_breaker.record_failure()
            raise

    def _parse_json_response(self, response: Any) -> dict[str, Any]:
        """Parse JSON from response content."""
        first_block = response.content[0]
        if hasattr(first_block, "text"):
            result: dict[str, Any] = json.loads(first_block.text)
            return result
        raise ValueError("Response did not contain text block")

    # ============================================================
    # TOOL USE
    # ============================================================

    async def _do_complete_with_tools(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        system: str,
        tool_choice: Optional[dict[str, Any]],
        node_name: str,
    ) -> dict[str, Any]:
        """Internal tool completion call - wrapped with retry logic."""
        kwargs: dict[str, Any] = {
            "model": self.config.model,
            "max_tokens": self.config.max_tokens,
            "system": system,
            "messages": messages,
            "tools": tools,
        }
        if tool_choice:
            kwargs["tool_choice"] = tool_choice

        start_time = time()
        response = await self.client.messages.create(**kwargs)
        self._track_response(response, node_name, start_time)
        return self._parse_tool_response(response)

    async def complete_with_tools(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        system: Optional[str] = None,
        skills: Optional[list[str]] = None,
        tool_choice: Optional[dict[str, Any]] = None,
        node_name: str = "unknown",
    ) -> dict[str, Any]:
        """Completion with tool use with automatic retry."""
        _check_circuit()
        if system is None and skills:
            system = self.build_system_prompt(skills)

        def on_retry(attempt: int, error: Exception, delay: float) -> None:
            logger.warning(f"Claude API retry {attempt + 1}: {error}, waiting {delay:.1f}s")
            _circuit_breaker.record_failure()

        try:
            return await retry_async(
                self._do_complete_with_tools,
                args=(messages, tools, system or "", tool_choice, node_name),
                config=CLAUDE_RETRY_CONFIG,
                on_retry=on_retry,
            )
        except Exception:
            _circuit_breaker.record_failure()
            raise

    def _parse_tool_response(self, response: Any) -> dict[str, Any]:
        """Parse tool use response into structured format."""
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


__all__ = [
    "ClaudeClient",
    "ClaudeConfig",
    "CircuitBreaker",
    "CircuitBreakerOpenError",
    "AppraisalOutput",
    "ActionSelectionOutput",
    "ValidationOutput",
    "ResponseOutput",
    "DialecticalOutput",
]
