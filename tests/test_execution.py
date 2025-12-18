"""
Execution Node Tests
=====================

Tests for the execution node including:
- Mock tool executors (ERP, bank, documents, email, workflow)
- Work unit processing
- Error handling
- Singleton executor
"""

import pytest
from unittest.mock import AsyncMock, patch


class TestMockToolExecutorERP:
    """Test ERP mock executor operations."""

    @pytest.mark.asyncio
    async def test_process_invoice(self):
        """Should process invoice and return result."""
        from src.cognitive_loop.nodes.execution import MockToolExecutor

        executor = MockToolExecutor()

        wu = {
            "unit_id": "wu-1",
            "tool": "erp",
            "verb": "process_invoice",
            "entities": {"invoice_id": "INV-123"},
            "slots": {"gl_code": "5000", "amount": 1000}
        }

        result = await executor.execute(wu)

        assert result["success"] == True
        assert "invoice_id" in result["result"]
        assert result["result"]["status"] == "processed"
        assert result["result"]["gl_code"] == "5000"

    @pytest.mark.asyncio
    async def test_create_record(self):
        """Should create record and return ID."""
        from src.cognitive_loop.nodes.execution import MockToolExecutor

        executor = MockToolExecutor()

        wu = {
            "unit_id": "wu-1",
            "tool": "erp",
            "verb": "create_record",
            "entities": {"record_type": "vendor"},
            "slots": {}
        }

        result = await executor.execute(wu)

        assert result["success"] == True
        assert "record_id" in result["result"]
        assert result["result"]["record_id"].startswith("REC-")

    @pytest.mark.asyncio
    async def test_query_records(self):
        """Should query records."""
        from src.cognitive_loop.nodes.execution import MockToolExecutor

        executor = MockToolExecutor()

        wu = {
            "unit_id": "wu-1",
            "tool": "erp",
            "verb": "query_records",
            "entities": {},
            "slots": {"filters": {"status": "open"}}
        }

        result = await executor.execute(wu)

        assert result["success"] == True
        assert "records" in result["result"]
        assert "count" in result["result"]

    @pytest.mark.asyncio
    async def test_post_journal_entry(self):
        """Should post journal entry with balanced debits/credits."""
        from src.cognitive_loop.nodes.execution import MockToolExecutor

        executor = MockToolExecutor()

        wu = {
            "unit_id": "wu-1",
            "tool": "erp",
            "verb": "post_journal_entry",
            "entities": {},
            "slots": {
                "debits": [{"account": "5000", "amount": 100}],
                "credits": [{"account": "2000", "amount": 100}]
            }
        }

        result = await executor.execute(wu)

        assert result["success"] == True
        assert result["result"]["entry_id"].startswith("JE-")
        assert result["result"]["debits_total"] == 100
        assert result["result"]["credits_total"] == 100


class TestMockToolExecutorBank:
    """Test bank mock executor operations."""

    @pytest.mark.asyncio
    async def test_process_payment(self):
        """Should process payment."""
        from src.cognitive_loop.nodes.execution import MockToolExecutor

        executor = MockToolExecutor()

        wu = {
            "unit_id": "wu-1",
            "tool": "bank",
            "verb": "process_payment",
            "entities": {},
            "slots": {"payment_date": "2024-01-15"}
        }

        result = await executor.execute(wu)

        assert result["success"] == True
        assert result["result"]["payment_id"].startswith("PMT-")
        assert result["result"]["status"] == "pending"

    @pytest.mark.asyncio
    async def test_reconcile_account(self):
        """Should reconcile account."""
        from src.cognitive_loop.nodes.execution import MockToolExecutor

        executor = MockToolExecutor()

        wu = {
            "unit_id": "wu-1",
            "tool": "bank",
            "verb": "reconcile_account",
            "entities": {},
            "slots": {}
        }

        result = await executor.execute(wu)

        assert result["success"] == True
        assert "matched_items" in result["result"]
        assert "unmatched_items" in result["result"]
        assert "variance" in result["result"]


class TestMockToolExecutorDocuments:
    """Test documents mock executor operations."""

    @pytest.mark.asyncio
    async def test_extract_data(self):
        """Should extract data from document."""
        from src.cognitive_loop.nodes.execution import MockToolExecutor

        executor = MockToolExecutor()

        wu = {
            "unit_id": "wu-1",
            "tool": "documents",
            "verb": "extract_data",
            "entities": {},
            "slots": {"fields_to_extract": ["vendor", "amount", "date"]}
        }

        result = await executor.execute(wu)

        assert result["success"] == True
        assert "extracted_fields" in result["result"]
        assert result["result"]["confidence"] == 0.95

    @pytest.mark.asyncio
    async def test_validate_document(self):
        """Should validate document."""
        from src.cognitive_loop.nodes.execution import MockToolExecutor

        executor = MockToolExecutor()

        wu = {
            "unit_id": "wu-1",
            "tool": "documents",
            "verb": "validate_document",
            "entities": {},
            "slots": {}
        }

        result = await executor.execute(wu)

        assert result["success"] == True
        assert result["result"]["valid"] == True
        assert result["result"]["issues"] == []


class TestMockToolExecutorEmail:
    """Test email mock executor operations."""

    @pytest.mark.asyncio
    async def test_send_email(self):
        """Should send email."""
        from src.cognitive_loop.nodes.execution import MockToolExecutor

        executor = MockToolExecutor()

        wu = {
            "unit_id": "wu-1",
            "tool": "email",
            "verb": "send_notification",
            "entities": {"recipient_id": "user@example.com"},
            "slots": {}
        }

        result = await executor.execute(wu)

        assert result["success"] == True
        assert result["result"]["message_id"].startswith("MSG-")
        assert result["result"]["recipient"] == "user@example.com"


class TestMockToolExecutorWorkflow:
    """Test workflow mock executor operations."""

    @pytest.mark.asyncio
    async def test_approve_transaction(self):
        """Should approve transaction."""
        from src.cognitive_loop.nodes.execution import MockToolExecutor

        executor = MockToolExecutor()

        wu = {
            "unit_id": "wu-1",
            "tool": "workflow",
            "verb": "approve_transaction",
            "entities": {},
            "slots": {}
        }

        result = await executor.execute(wu)

        assert result["success"] == True
        assert result["result"]["approval_id"].startswith("APR-")
        assert result["result"]["status"] == "approved"

    @pytest.mark.asyncio
    async def test_escalate_issue(self):
        """Should escalate issue."""
        from src.cognitive_loop.nodes.execution import MockToolExecutor

        executor = MockToolExecutor()

        wu = {
            "unit_id": "wu-1",
            "tool": "workflow",
            "verb": "escalate_issue",
            "entities": {},
            "slots": {"severity": "high"}
        }

        result = await executor.execute(wu)

        assert result["success"] == True
        assert result["result"]["escalation_id"].startswith("ESC-")
        assert result["result"]["severity"] == "high"


class TestMockToolExecutorUnknown:
    """Test unknown tool handling."""

    @pytest.mark.asyncio
    async def test_unknown_tool_fails(self):
        """Unknown tool should return failure."""
        from src.cognitive_loop.nodes.execution import MockToolExecutor

        executor = MockToolExecutor()

        wu = {
            "unit_id": "wu-1",
            "tool": "unknown_tool",
            "verb": "do_something",
            "entities": {},
            "slots": {}
        }

        result = await executor.execute(wu)

        assert result["success"] == False
        assert "unknown tool" in result["message"].lower()


class TestGetExecutor:
    """Test singleton executor."""

    def test_get_executor_returns_same_instance(self):
        """get_executor should return same instance."""
        from src.cognitive_loop.nodes.execution import get_executor

        executor1 = get_executor()
        executor2 = get_executor()

        assert executor1 is executor2

    def test_executor_is_thread_safe(self):
        """Executor should be thread-safe."""
        import threading
        from src.cognitive_loop.nodes.execution import get_executor

        executors = []

        def get_and_store():
            executors.append(get_executor())

        threads = [threading.Thread(target=get_and_store) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All should be same instance
        assert len(set(id(e) for e in executors)) == 1


class TestProcessFunction:
    """Test the main process function."""

    @pytest.mark.asyncio
    async def test_no_selected_action(self, sample_state):
        """Should handle missing selected action."""
        from src.cognitive_loop.nodes.execution import process

        sample_state["selected_action"] = None

        result = await process(sample_state)

        assert len(result["execution_results"]) == 1
        assert result["execution_results"][0]["success"] == False
        assert "no action" in result["execution_results"][0]["message"].lower()

    @pytest.mark.asyncio
    async def test_no_work_units(self, sample_state):
        """Should handle empty work units."""
        from src.cognitive_loop.nodes.execution import process

        sample_state["selected_action"] = {
            "action_type": "test",
            "work_units": [],
            "requires_tools": [],
            "estimated_difficulty": 1
        }

        result = await process(sample_state)

        assert result["execution_results"][0]["success"] == True
        assert "no work units" in result["execution_results"][0]["message"].lower()

    @pytest.mark.asyncio
    async def test_executes_all_work_units(self, sample_state_with_action):
        """Should execute all work units."""
        from src.cognitive_loop.nodes.execution import process

        # Add second work unit
        sample_state_with_action["selected_action"]["work_units"].append({
            "unit_id": "wu-2",
            "tool": "bank",
            "verb": "process_payment",
            "entities": {},
            "slots": {}
        })

        result = await process(sample_state_with_action)

        assert len(result["execution_results"]) == 2
        assert all(r["success"] for r in result["execution_results"])

    @pytest.mark.asyncio
    async def test_stops_on_failure(self, sample_state_with_action):
        """Should stop execution on first failure."""
        from src.cognitive_loop.nodes.execution import process

        # Add unknown tool work unit first
        sample_state_with_action["selected_action"]["work_units"] = [
            {
                "unit_id": "wu-1",
                "tool": "unknown",
                "verb": "fail",
                "entities": {},
                "slots": {}
            },
            {
                "unit_id": "wu-2",
                "tool": "erp",
                "verb": "process_invoice",
                "entities": {},
                "slots": {}
            }
        ]

        result = await process(sample_state_with_action)

        # Should only have one result (stopped after failure)
        assert len(result["execution_results"]) == 1
        assert result["execution_results"][0]["success"] == False

    @pytest.mark.asyncio
    async def test_result_includes_unit_metadata(self, sample_state_with_action):
        """Results should include unit ID, tool, and verb."""
        from src.cognitive_loop.nodes.execution import process

        result = await process(sample_state_with_action)

        execution_result = result["execution_results"][0]
        assert "unit_id" in execution_result
        assert "tool" in execution_result
        assert "verb" in execution_result

    @pytest.mark.asyncio
    async def test_handles_execution_exception(self, sample_state_with_action):
        """Should handle exceptions during execution."""
        from src.cognitive_loop.nodes.execution import process, get_executor

        # Mock executor to raise exception
        with patch.object(get_executor(), 'execute', side_effect=Exception("Execution error")):
            result = await process(sample_state_with_action)

        assert result["execution_results"][0]["success"] == False
        assert "execution error" in result["execution_results"][0]["message"].lower()
