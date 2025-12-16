"""
Claude Client Wrapper
======================

Async client for Claude API with structured outputs support.
Uses the latest Anthropic SDK (December 2025) features:
- Structured outputs (beta)
- Tool use with strict schemas
- Streaming support
"""

import os
import json
from typing import Optional, Any, Type, TypeVar
from dataclasses import dataclass
from pathlib import Path
from anthropic import AsyncAnthropic
from pydantic import BaseModel

# Default model - Claude Sonnet 4.5 for good balance of speed/quality
DEFAULT_MODEL = "claude-sonnet-4-5-20250929"

# Beta header for structured outputs
STRUCTURED_OUTPUTS_BETA = "structured-outputs-2025-11-13"


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
    
    def __init__(
        self,
        config: Optional[ClaudeConfig] = None,
        skills_dir: Optional[Path] = None
    ):
        self.config = config or ClaudeConfig()
        self.client = AsyncAnthropic(
            api_key=os.environ.get("ANTHROPIC_API_KEY")
        )
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
                parts.append(f"<skill name=\"{skill}\">\n{content}\n</skill>")
            except FileNotFoundError:
                # Skip missing skills with warning
                print(f"Warning: Skill '{skill}' not found, skipping")
                
        return "\n\n".join(parts)
        
    # ============================================================
    # BASIC COMPLETION
    # ============================================================
    
    async def complete(
        self,
        messages: list[dict],
        system: Optional[str] = None,
        skills: Optional[list[str]] = None,
        temperature: Optional[float] = None
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
        # Build system prompt
        if system is None and skills:
            system = self.build_system_prompt(skills)
            
        # Call Claude
        response = await self.client.messages.create(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            temperature=temperature or self.config.temperature,
            system=system or "",
            messages=messages
        )
        
        # Extract text
        return response.content[0].text
        
    # ============================================================
    # STRUCTURED OUTPUTS (Beta)
    # ============================================================
    
    T = TypeVar('T', bound=BaseModel)
    
    async def complete_structured(
        self,
        messages: list[dict],
        response_model: Type[T],
        system: Optional[str] = None,
        skills: Optional[list[str]] = None,
        temperature: Optional[float] = None
    ) -> T:
        """
        Completion with guaranteed structured output.
        
        Uses Claude's structured outputs beta to ensure response
        matches the provided Pydantic model schema.
        
        Args:
            messages: Conversation history
            response_model: Pydantic model class for response
            system: System prompt
            skills: Skills to use
            temperature: Temperature override
            
        Returns:
            Instance of response_model with parsed response
        """
        if system is None and skills:
            system = self.build_system_prompt(skills)
            
        # Use beta.messages.parse for automatic schema handling
        response = await self.client.beta.messages.parse(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            betas=[STRUCTURED_OUTPUTS_BETA],
            temperature=temperature or self.config.temperature,
            system=system or "",
            messages=messages,
            response_model=response_model
        )
        
        return response.parsed_output
        
    async def complete_json(
        self,
        messages: list[dict],
        schema: dict,
        system: Optional[str] = None,
        skills: Optional[list[str]] = None
    ) -> dict:
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
        if system is None and skills:
            system = self.build_system_prompt(skills)
            
        response = await self.client.beta.messages.create(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            betas=[STRUCTURED_OUTPUTS_BETA],
            system=system or "",
            messages=messages,
            output_format={
                "type": "json_schema",
                "schema": schema
            }
        )
        
        return json.loads(response.content[0].text)
        
    # ============================================================
    # TOOL USE
    # ============================================================
    
    async def complete_with_tools(
        self,
        messages: list[dict],
        tools: list[dict],
        system: Optional[str] = None,
        skills: Optional[list[str]] = None,
        tool_choice: Optional[dict] = None
    ) -> dict:
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
            
        kwargs = {
            "model": self.config.model,
            "max_tokens": self.config.max_tokens,
            "system": system or "",
            "messages": messages,
            "tools": tools
        }
        
        if tool_choice:
            kwargs["tool_choice"] = tool_choice
            
        response = await self.client.messages.create(**kwargs)
        
        # Parse response into structured format
        result = {
            "text_blocks": [],
            "tool_use_blocks": [],
            "stop_reason": response.stop_reason
        }
        
        for block in response.content:
            if block.type == "text":
                result["text_blocks"].append(block.text)
            elif block.type == "tool_use":
                result["tool_use_blocks"].append({
                    "id": block.id,
                    "name": block.name,
                    "input": block.input
                })
                
        return result
        
    # ============================================================
    # STREAMING
    # ============================================================
    
    async def stream(
        self,
        messages: list[dict],
        system: Optional[str] = None,
        skills: Optional[list[str]] = None
    ):
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
            messages=messages
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
    work_units: list[dict]
    tool_requirements: list[str]
    confidence: float
    requires_human_approval: bool
    approval_reason: Optional[str]
    estimated_difficulty: int


class ValidationOutput(BaseModel):
    """Structured output for validation node"""
    all_passed: bool
    results: list[dict]  # ValidationResult items
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


# ============================================================
# SINGLETON INSTANCE
# ============================================================

_client: Optional[ClaudeClient] = None


def get_claude_client() -> ClaudeClient:
    """Get singleton Claude client instance"""
    global _client
    if _client is None:
        _client = ClaudeClient()
    return _client


async def complete(messages: list[dict], **kwargs) -> str:
    """Convenience function for basic completion"""
    return await get_claude_client().complete(messages, **kwargs)


async def complete_structured(messages: list[dict], response_model, **kwargs):
    """Convenience function for structured completion"""
    return await get_claude_client().complete_structured(
        messages, response_model, **kwargs
    )
