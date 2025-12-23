"""
Action Proposal Tests
======================

Tests for the HITL action proposal node including:
- Summary generation
- Interrupt payload construction
- Routing logic
"""

from unittest.mock import patch

import pytest


class TestGenerateActionSummary:
    """Test human-readable summary generation."""

    @pytest.mark.asyncio
    async def test_generates_summary_with_claude(
        self, sample_state_with_action, mock_claude_client
    ):
        """Should use Claude to generate summary."""
        from src.cognitive_loop.nodes.action_proposal import generate_action_summary

        mock_claude_client.complete.return_value = "I'd like to process the invoice..."

        with patch(
            "src.cognitive_loop.nodes.action_proposal.get_claude_client",
            return_value=mock_claude_client,
        ):
            summary = await generate_action_summary(
                sample_state_with_action, sample_state_with_action["selected_action"]
            )

        assert len(summary) > 0
        mock_claude_client.complete.assert_called_once()

    @pytest.mark.asyncio
    async def test_summary_fallback_on_error(self, sample_state_with_action, mock_claude_client):
        """Should use fallback summary on Claude error."""
        from src.cognitive_loop.nodes.action_proposal import generate_action_summary

        mock_claude_client.complete.side_effect = Exception("API Error")

        with patch(
            "src.cognitive_loop.nodes.action_proposal.get_claude_client",
            return_value=mock_claude_client,
        ):
            summary = await generate_action_summary(
                sample_state_with_action, sample_state_with_action["selected_action"]
            )

        assert "perform the following action" in summary
        assert "requires your approval" in summary

    @pytest.mark.asyncio
    async def test_summary_includes_work_units(self, sample_state_with_action, mock_claude_client):
        """Summary prompt should include work unit details."""
        from src.cognitive_loop.nodes.action_proposal import generate_action_summary

        mock_claude_client.complete.return_value = "Summary"

        with patch(
            "src.cognitive_loop.nodes.action_proposal.get_claude_client",
            return_value=mock_claude_client,
        ):
            await generate_action_summary(
                sample_state_with_action, sample_state_with_action["selected_action"]
            )

        # Check the prompt contains work unit info
        call_args = mock_claude_client.complete.call_args
        prompt = str(call_args)
        assert "process_invoice" in prompt.lower() or "invoice" in prompt.lower()


class TestBuildInterruptPayload:
    """Test interrupt payload construction."""

    def test_payload_structure(self, sample_state_with_action):
        """Payload should have required fields."""
        from src.cognitive_loop.nodes.action_proposal import build_interrupt_payload

        payload = build_interrupt_payload(
            sample_state_with_action, sample_state_with_action["selected_action"], "Test summary"
        )

        assert payload["type"] == "action_proposal"
        assert payload["summary"] == "Test summary"
        assert "options" in payload
        assert "approve" in payload["options"]
        assert "reject" in payload["options"]

    def test_payload_includes_action_details(self, sample_state_with_action):
        """Payload should include action details."""
        from src.cognitive_loop.nodes.action_proposal import build_interrupt_payload

        action = sample_state_with_action["selected_action"]

        payload = build_interrupt_payload(sample_state_with_action, action, "Summary")

        assert payload["action_type"] == action["action_type"]
        assert payload["work_unit_count"] == len(action["work_units"])
        assert payload["estimated_difficulty"] == action["estimated_difficulty"]

    def test_payload_includes_thread_id(self, sample_state_with_action):
        """Payload should include thread_id for correlation."""
        from src.cognitive_loop.nodes.action_proposal import build_interrupt_payload

        payload = build_interrupt_payload(
            sample_state_with_action, sample_state_with_action["selected_action"], "Summary"
        )

        assert payload["thread_id"] == sample_state_with_action["thread_id"]


class TestRouteAfterProposal:
    """Test routing after proposal response."""

    def test_route_approved_to_execution(self, sample_state_with_action):
        """Approved actions should route to execution."""
        from src.cognitive_loop.nodes.action_proposal import route_after_proposal

        sample_state_with_action["approval_status"] = "approved"

        route = route_after_proposal(sample_state_with_action)

        assert route == "execution"

    def test_route_rejected_to_response(self, sample_state_with_action):
        """Rejected actions should route to response generation."""
        from src.cognitive_loop.nodes.action_proposal import route_after_proposal

        sample_state_with_action["approval_status"] = "rejected"

        route = route_after_proposal(sample_state_with_action)

        assert route == "response_generation"

    def test_route_no_status_to_response(self, sample_state_with_action):
        """Missing status should route to response generation."""
        from src.cognitive_loop.nodes.action_proposal import route_after_proposal

        sample_state_with_action["approval_status"] = None

        route = route_after_proposal(sample_state_with_action)

        assert route == "response_generation"


class TestProcessFunction:
    """Test the main process function."""

    @pytest.mark.asyncio
    async def test_no_action_returns_guidance(self, sample_state):
        """No selected action should return guidance_seeking."""
        from src.cognitive_loop.nodes.action_proposal import process

        sample_state["selected_action"] = None

        result = await process(sample_state)

        assert result["supervision_mode"] == "guidance_seeking"
        assert result["approval_status"] == "no_action"

    @pytest.mark.asyncio
    async def test_approved_sets_status(self, sample_state_with_action, mock_claude_client):
        """Approved response should set approval_status."""
        from src.cognitive_loop.nodes.action_proposal import process

        mock_claude_client.complete.return_value = "Summary"

        with patch(
            "src.cognitive_loop.nodes.action_proposal.get_claude_client",
            return_value=mock_claude_client,
        ):
            with patch("src.cognitive_loop.nodes.action_proposal.interrupt") as mock_interrupt:
                mock_interrupt.return_value = {"choice": "approve"}

                result = await process(sample_state_with_action)

        assert result["approval_status"] == "approved"
        assert "approval_summary" in result

    @pytest.mark.asyncio
    async def test_rejected_changes_mode(self, sample_state_with_action, mock_claude_client):
        """Rejected response should change to guidance_seeking."""
        from src.cognitive_loop.nodes.action_proposal import process

        mock_claude_client.complete.return_value = "Summary"

        with patch(
            "src.cognitive_loop.nodes.action_proposal.get_claude_client",
            return_value=mock_claude_client,
        ):
            with patch("src.cognitive_loop.nodes.action_proposal.interrupt") as mock_interrupt:
                mock_interrupt.return_value = {"choice": "reject"}

                result = await process(sample_state_with_action)

        assert result["approval_status"] == "rejected"
        assert result["supervision_mode"] == "guidance_seeking"
        assert result["selected_action"] is None

    @pytest.mark.asyncio
    async def test_non_dict_response_treated_as_reject(
        self, sample_state_with_action, mock_claude_client
    ):
        """Non-dict interrupt response should be treated as rejection."""
        from src.cognitive_loop.nodes.action_proposal import process

        mock_claude_client.complete.return_value = "Summary"

        with patch(
            "src.cognitive_loop.nodes.action_proposal.get_claude_client",
            return_value=mock_claude_client,
        ):
            with patch("src.cognitive_loop.nodes.action_proposal.interrupt") as mock_interrupt:
                mock_interrupt.return_value = "invalid_response"

                result = await process(sample_state_with_action)

        assert result["approval_status"] == "rejected"


class TestMessageExtraction:
    """Test extraction of original request."""

    @pytest.mark.asyncio
    async def test_finds_user_message(self, sample_state_with_action, mock_claude_client):
        """Should find the user message, not assistant message."""
        from src.cognitive_loop.nodes.action_proposal import generate_action_summary

        sample_state_with_action["messages"] = [
            {"role": "user", "content": "Process my invoice please"},
            {"role": "assistant", "content": "I'll help you with that"},
        ]

        mock_claude_client.complete.return_value = "Summary"

        with patch(
            "src.cognitive_loop.nodes.action_proposal.get_claude_client",
            return_value=mock_claude_client,
        ):
            await generate_action_summary(
                sample_state_with_action, sample_state_with_action["selected_action"]
            )

        call_args = mock_claude_client.complete.call_args
        prompt = str(call_args)
        assert "invoice" in prompt.lower()

    @pytest.mark.asyncio
    async def test_handles_list_content(self, sample_state_with_action, mock_claude_client):
        """Should handle list-format message content."""
        from src.cognitive_loop.nodes.action_proposal import generate_action_summary

        sample_state_with_action["messages"] = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "First part"},
                    {"type": "text", "text": "Second part"},
                ],
            }
        ]

        mock_claude_client.complete.return_value = "Summary"

        with patch(
            "src.cognitive_loop.nodes.action_proposal.get_claude_client",
            return_value=mock_claude_client,
        ):
            # Should not raise error
            await generate_action_summary(
                sample_state_with_action, sample_state_with_action["selected_action"]
            )

    @pytest.mark.asyncio
    async def test_truncates_long_request(self, sample_state_with_action, mock_claude_client):
        """Should truncate very long requests."""
        from src.cognitive_loop.nodes.action_proposal import generate_action_summary

        long_message = "x" * 500
        sample_state_with_action["messages"] = [{"role": "user", "content": long_message}]

        mock_claude_client.complete.return_value = "Summary"

        with patch(
            "src.cognitive_loop.nodes.action_proposal.get_claude_client",
            return_value=mock_claude_client,
        ):
            await generate_action_summary(
                sample_state_with_action, sample_state_with_action["selected_action"]
            )

        # The prompt shouldn't contain the full 500 chars
        call_args = mock_claude_client.complete.call_args
        prompt = str(call_args)
        # Request is truncated to ~200 chars (may have slight variance in repr)
        assert prompt.count("x") <= 210


class TestWorkUnitDescriptions:
    """Test work unit description formatting."""

    @pytest.mark.asyncio
    async def test_formats_work_units(self, sample_state_with_action, mock_claude_client):
        """Should format work units for human reading."""
        from src.cognitive_loop.nodes.action_proposal import generate_action_summary

        sample_state_with_action["selected_action"]["work_units"] = [
            {
                "unit_id": "wu-1",
                "tool": "erp",
                "verb": "process_invoice",
                "entities": {"invoice_id": "INV-1234"},
                "slots": {},
                "constraints": [],
            },
            {
                "unit_id": "wu-2",
                "tool": "bank",
                "verb": "process_payment",
                "entities": {"amount": 5000},
                "slots": {},
                "constraints": [],
            },
        ]

        mock_claude_client.complete.return_value = "Summary"

        with patch(
            "src.cognitive_loop.nodes.action_proposal.get_claude_client",
            return_value=mock_claude_client,
        ):
            await generate_action_summary(
                sample_state_with_action, sample_state_with_action["selected_action"]
            )

        call_args = mock_claude_client.complete.call_args
        prompt = str(call_args)
        # Should contain formatted verbs
        assert "process" in prompt.lower()

    @pytest.mark.asyncio
    async def test_handles_empty_work_units(self, sample_state_with_action, mock_claude_client):
        """Should handle empty work units list."""
        from src.cognitive_loop.nodes.action_proposal import generate_action_summary

        sample_state_with_action["selected_action"]["work_units"] = []

        mock_claude_client.complete.return_value = "Summary"

        with patch(
            "src.cognitive_loop.nodes.action_proposal.get_claude_client",
            return_value=mock_claude_client,
        ):
            summary = await generate_action_summary(
                sample_state_with_action, sample_state_with_action["selected_action"]
            )

        # Should not error
        assert len(summary) > 0
