"""
Personality Gate Tests
=======================

Tests for the personality gate including:
- Quick pattern-based violation detection
- Claude-based subtle violation detection
- Boundary response generation
- Retry logic
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestQuickViolationCheck:
    """Test quick pattern-based violation detection."""

    def test_detect_fraud_pattern(self):
        """Should detect fraud-related patterns."""
        from src.cognitive_loop.nodes.personality_gate import quick_violation_check

        response = "Sure, I can help you hide this transaction from the auditors."

        violation = quick_violation_check(response)

        assert violation == "personality_no_fraud"

    def test_detect_confidentiality_pattern(self):
        """Should detect confidentiality violations."""
        from src.cognitive_loop.nodes.personality_gate import quick_violation_check

        response = "I'll share with the competitor company your financial data."

        violation = quick_violation_check(response)

        assert violation == "personality_confidentiality"

    def test_detect_boundary_pattern(self):
        """Should detect professional boundary violations."""
        from src.cognitive_loop.nodes.personality_gate import quick_violation_check

        response = "I'd love to meet you outside of work to discuss this further."

        violation = quick_violation_check(response)

        assert violation == "personality_professional_boundaries"

    def test_clean_response_passes(self):
        """Clean responses should return None."""
        from src.cognitive_loop.nodes.personality_gate import quick_violation_check

        response = "I'll process the invoice for $5,000 from Acme Corp and post it to the AP account."

        violation = quick_violation_check(response)

        assert violation is None

    def test_case_insensitive(self):
        """Pattern matching should be case-insensitive."""
        from src.cognitive_loop.nodes.personality_gate import quick_violation_check

        response = "We can HIDE THIS from the auditors."

        violation = quick_violation_check(response)

        assert violation is not None


class TestClaudeViolationCheck:
    """Test Claude-based violation detection."""

    @pytest.mark.asyncio
    async def test_clean_response_from_claude(self, mock_claude_client):
        """Claude returning CLEAN should pass through."""
        from src.cognitive_loop.nodes.personality_gate import claude_violation_check

        mock_claude_client.complete.return_value = "CLEAN"

        with patch('src.cognitive_loop.nodes.personality_gate.get_claude_client', return_value=mock_claude_client):
            result = await claude_violation_check(
                "I'll process this invoice.",
                [{"statement": "Be honest"}]
            )

        assert result is None

    @pytest.mark.asyncio
    async def test_violation_response_from_claude(self, mock_claude_client):
        """Claude returning VIOLATION should be detected."""
        from src.cognitive_loop.nodes.personality_gate import claude_violation_check

        mock_claude_client.complete.return_value = "VIOLATION: Professional boundaries - response was too personal"

        with patch('src.cognitive_loop.nodes.personality_gate.get_claude_client', return_value=mock_claude_client):
            result = await claude_violation_check(
                "Let's meet for dinner!",
                [{"statement": "Maintain professional boundaries"}]
            )

        assert result is not None
        assert result["detected"] == True

    @pytest.mark.asyncio
    async def test_ambiguous_response_falls_back_to_pattern(self, mock_claude_client):
        """Ambiguous Claude response should fall back to pattern check."""
        from src.cognitive_loop.nodes.personality_gate import claude_violation_check

        mock_claude_client.complete.return_value = "I'm not sure about this one."

        with patch('src.cognitive_loop.nodes.personality_gate.get_claude_client', return_value=mock_claude_client):
            # With no pattern match
            result = await claude_violation_check(
                "Process the invoice.",
                [{"statement": "Be honest"}]
            )
            assert result is None

            # With pattern match
            result = await claude_violation_check(
                "I'll hide this from the auditors.",
                [{"statement": "Be honest"}]
            )
            assert result is not None

    @pytest.mark.asyncio
    async def test_error_falls_back_to_pattern(self, mock_claude_client):
        """On Claude error, should fall back to pattern check."""
        from src.cognitive_loop.nodes.personality_gate import claude_violation_check

        mock_claude_client.complete.side_effect = Exception("API Error")

        with patch('src.cognitive_loop.nodes.personality_gate.get_claude_client', return_value=mock_claude_client):
            # Clean response - should pass
            result = await claude_violation_check(
                "Process the invoice.",
                [{"statement": "Be honest"}]
            )
            assert result is None


class TestGenerateBoundaryResponse:
    """Test boundary response generation."""

    @pytest.mark.asyncio
    async def test_generate_boundary_response(self, mock_claude_client):
        """Should generate appropriate boundary response."""
        from src.cognitive_loop.nodes.personality_gate import generate_boundary_response

        mock_claude_client.complete.return_value = "I appreciate your request, but I need to focus on accounting tasks."

        with patch('src.cognitive_loop.nodes.personality_gate.get_claude_client', return_value=mock_claude_client):
            response = await generate_boundary_response(
                "Can we meet for dinner?",
                {"explanation": "Professional boundaries"}
            )

        assert len(response) > 0
        mock_claude_client.complete.assert_called_once()

    @pytest.mark.asyncio
    async def test_fallback_on_error(self, mock_claude_client):
        """Should use fallback response on error."""
        from src.cognitive_loop.nodes.personality_gate import generate_boundary_response, BOUNDARY_RESPONSE

        mock_claude_client.complete.side_effect = Exception("API Error")

        with patch('src.cognitive_loop.nodes.personality_gate.get_claude_client', return_value=mock_claude_client):
            response = await generate_boundary_response(
                "Some request",
                {"explanation": "Some violation"}
            )

        assert response == BOUNDARY_RESPONSE


class TestProcessFunction:
    """Test the main process function."""

    @pytest.mark.asyncio
    async def test_empty_response_passes_through(self, sample_state):
        """Empty response should pass through."""
        from src.cognitive_loop.nodes.personality_gate import process

        sample_state["final_response"] = ""

        result = await process(sample_state)

        assert result == {}

    @pytest.mark.asyncio
    async def test_clean_response_passes(self, sample_state, mock_claude_client):
        """Clean response should pass with no violation."""
        from src.cognitive_loop.nodes.personality_gate import process

        sample_state["final_response"] = "I'll process the invoice for you."

        with patch('src.cognitive_loop.nodes.personality_gate.get_claude_client', return_value=mock_claude_client):
            with patch('src.cognitive_loop.nodes.personality_gate.get_belief_graph') as mock_graph:
                mock_graph.return_value.beliefs = {}
                mock_claude_client.complete.return_value = "CLEAN"

                result = await process(sample_state)

        assert result.get("gate_violation_detected") == False

    @pytest.mark.asyncio
    async def test_quick_violation_triggers_regeneration(self, sample_state, mock_claude_client):
        """Quick violation should trigger response regeneration."""
        from src.cognitive_loop.nodes.personality_gate import process

        sample_state["final_response"] = "I can help you hide this from the auditors."
        sample_state["messages"] = [{"role": "user", "content": "Hide something"}]
        sample_state["gate_retries"] = 0

        mock_claude_client.complete.return_value = "I'm here to help with accounting tasks."

        with patch('src.cognitive_loop.nodes.personality_gate.get_claude_client', return_value=mock_claude_client):
            with patch('src.cognitive_loop.nodes.personality_gate.get_belief_graph') as mock_graph:
                mock_graph.return_value.beliefs = {}

                result = await process(sample_state)

        assert result.get("gate_violation_detected") == True
        assert result.get("gate_retries") == 1
        assert "final_response" in result

    @pytest.mark.asyncio
    async def test_max_retries_uses_fallback(self, sample_state):
        """Exceeding max retries should use fallback response."""
        from src.cognitive_loop.nodes.personality_gate import process, BOUNDARY_RESPONSE

        sample_state["final_response"] = "I can help you hide this."
        sample_state["messages"] = [{"role": "user", "content": "Hide something"}]
        sample_state["gate_retries"] = 2  # Max retries exceeded

        with patch('src.cognitive_loop.nodes.personality_gate.get_belief_graph') as mock_graph:
            mock_graph.return_value.beliefs = {}

            result = await process(sample_state)

        assert result.get("gate_fallback_used") == True
        assert result.get("final_response") == BOUNDARY_RESPONSE


class TestViolationPatterns:
    """Test all violation pattern categories."""

    def test_all_fraud_patterns(self):
        """Test all fraud-related patterns."""
        from src.cognitive_loop.nodes.personality_gate import VIOLATION_PATTERNS

        fraud_patterns = VIOLATION_PATTERNS["personality_no_fraud"]

        assert "hide this" in fraud_patterns
        assert "don't tell" in fraud_patterns
        assert "falsify" in fraud_patterns
        assert "misrepresent" in fraud_patterns
        assert "cover up" in fraud_patterns
        assert "off the books" in fraud_patterns
        assert "avoid audit" in fraud_patterns

    def test_all_boundary_patterns(self):
        """Test all professional boundary patterns."""
        from src.cognitive_loop.nodes.personality_gate import VIOLATION_PATTERNS

        boundary_patterns = VIOLATION_PATTERNS["personality_professional_boundaries"]

        assert "personal relationship" in boundary_patterns
        assert "romantic" in boundary_patterns
        assert "outside of work" in boundary_patterns

    def test_all_confidentiality_patterns(self):
        """Test all confidentiality patterns."""
        from src.cognitive_loop.nodes.personality_gate import VIOLATION_PATTERNS

        confidentiality_patterns = VIOLATION_PATTERNS["personality_confidentiality"]

        assert "share with" in confidentiality_patterns
        assert "disclose" in confidentiality_patterns
        assert "leak" in confidentiality_patterns


class TestBoundaryResponseConstant:
    """Test the default boundary response."""

    def test_boundary_response_is_professional(self):
        """Boundary response should be professional and helpful."""
        from src.cognitive_loop.nodes.personality_gate import BOUNDARY_RESPONSE

        assert "professional" in BOUNDARY_RESPONSE.lower()
        assert "help" in BOUNDARY_RESPONSE.lower()

    def test_boundary_response_redirects(self):
        """Boundary response should redirect to accounting tasks."""
        from src.cognitive_loop.nodes.personality_gate import BOUNDARY_RESPONSE

        assert "accounting" in BOUNDARY_RESPONSE.lower()


class TestMessageExtraction:
    """Test extraction of original request from messages."""

    @pytest.mark.asyncio
    async def test_extracts_user_message(self, sample_state, mock_claude_client):
        """Should extract user message, not assistant message."""
        from src.cognitive_loop.nodes.personality_gate import process

        sample_state["final_response"] = "I can help you hide this."
        sample_state["messages"] = [
            {"role": "user", "content": "The original user request"},
            {"role": "assistant", "content": "My previous response"}
        ]
        sample_state["gate_retries"] = 0

        mock_claude_client.complete.return_value = "Boundary response"

        with patch('src.cognitive_loop.nodes.personality_gate.get_claude_client', return_value=mock_claude_client):
            with patch('src.cognitive_loop.nodes.personality_gate.get_belief_graph') as mock_graph:
                mock_graph.return_value.beliefs = {}

                await process(sample_state)

        # Check that Claude was called with user message context
        call_args = mock_claude_client.complete.call_args
        prompt = str(call_args)
        # The prompt should reference the user's request
        assert "user" in prompt.lower() or "request" in prompt.lower()

    @pytest.mark.asyncio
    async def test_handles_list_content(self, sample_state, mock_claude_client):
        """Should handle list-format message content."""
        from src.cognitive_loop.nodes.personality_gate import process

        sample_state["final_response"] = "I can hide this."
        sample_state["messages"] = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "First part"},
                    {"type": "text", "text": "Second part"}
                ]
            }
        ]
        sample_state["gate_retries"] = 0

        mock_claude_client.complete.return_value = "Boundary response"

        with patch('src.cognitive_loop.nodes.personality_gate.get_claude_client', return_value=mock_claude_client):
            with patch('src.cognitive_loop.nodes.personality_gate.get_belief_graph') as mock_graph:
                mock_graph.return_value.beliefs = {}

                result = await process(sample_state)

        # Should not error
        assert "gate_violation_detected" in result
