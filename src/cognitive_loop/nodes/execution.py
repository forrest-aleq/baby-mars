"""
Execution Node
===============

Executes work units via MCP servers or tools.
Implements the PTD Driver layer (Paper #20).

For Baby MARS MVP, this is a mock implementation that
simulates tool execution. Replace with real MCP integration.
"""

import asyncio
from datetime import datetime
from typing import Any, Optional
import uuid

from ...state.schema import (
    BabyMARSState,
    WorkUnit,
)


# ============================================================
# MOCK TOOL EXECUTORS
# ============================================================

class MockToolExecutor:
    """
    Mock executor for development/testing.
    
    Replace with real MCP server connections:
    - QuickBooks MCP
    - NetSuite MCP
    - Bank MCP
    - Document MCP
    """
    
    async def execute(self, work_unit: WorkUnit) -> dict:
        """Execute a work unit and return result"""
        tool = work_unit.get("tool", "unknown")
        verb = work_unit.get("verb", "unknown")
        
        # Route to appropriate mock handler
        handlers = {
            "erp": self._execute_erp,
            "bank": self._execute_bank,
            "documents": self._execute_documents,
            "email": self._execute_email,
            "workflow": self._execute_workflow,
        }
        
        handler = handlers.get(tool, self._execute_unknown)
        return await handler(work_unit)
    
    async def _execute_erp(self, wu: WorkUnit) -> dict:
        """Mock ERP operations"""
        verb = wu.get("verb", "")
        entities = wu.get("entities", {})
        slots = wu.get("slots", {})
        
        # Simulate processing time
        await asyncio.sleep(0.1)
        
        if verb == "process_invoice":
            return {
                "success": True,
                "result": {
                    "invoice_id": entities.get("invoice_id", "INV-MOCK-001"),
                    "status": "processed",
                    "gl_code": slots.get("gl_code", "5000"),
                    "amount": slots.get("amount", 0),
                    "posted_at": datetime.now().isoformat()
                },
                "message": "Invoice processed successfully"
            }
        
        elif verb == "create_record":
            return {
                "success": True,
                "result": {
                    "record_id": f"REC-{uuid.uuid4().hex[:8].upper()}",
                    "record_type": entities.get("record_type", "unknown"),
                    "created_at": datetime.now().isoformat()
                },
                "message": "Record created"
            }
        
        elif verb == "query_records":
            return {
                "success": True,
                "result": {
                    "records": [],
                    "count": 0,
                    "query": slots.get("filters", {})
                },
                "message": "Query executed"
            }
        
        elif verb == "post_journal_entry":
            return {
                "success": True,
                "result": {
                    "entry_id": f"JE-{uuid.uuid4().hex[:8].upper()}",
                    "debits_total": sum(d.get("amount", 0) for d in slots.get("debits", [])),
                    "credits_total": sum(c.get("amount", 0) for c in slots.get("credits", [])),
                    "posted_at": datetime.now().isoformat()
                },
                "message": "Journal entry posted"
            }
        
        else:
            return {
                "success": True,
                "result": {"verb": verb, "entities": entities},
                "message": f"ERP operation '{verb}' completed"
            }
    
    async def _execute_bank(self, wu: WorkUnit) -> dict:
        """Mock bank operations"""
        verb = wu.get("verb", "")
        
        await asyncio.sleep(0.1)
        
        if verb == "process_payment":
            return {
                "success": True,
                "result": {
                    "payment_id": f"PMT-{uuid.uuid4().hex[:8].upper()}",
                    "status": "pending",
                    "scheduled_date": wu.get("slots", {}).get("payment_date", datetime.now().isoformat())
                },
                "message": "Payment scheduled"
            }
        
        elif verb == "reconcile_account":
            return {
                "success": True,
                "result": {
                    "matched_items": 0,
                    "unmatched_items": 0,
                    "variance": 0.0
                },
                "message": "Reconciliation completed"
            }
        
        else:
            return {
                "success": True,
                "result": {"verb": verb},
                "message": f"Bank operation '{verb}' completed"
            }
    
    async def _execute_documents(self, wu: WorkUnit) -> dict:
        """Mock document operations"""
        verb = wu.get("verb", "")
        
        await asyncio.sleep(0.05)
        
        if verb == "extract_data":
            return {
                "success": True,
                "result": {
                    "extracted_fields": wu.get("slots", {}).get("fields_to_extract", []),
                    "confidence": 0.95
                },
                "message": "Data extracted"
            }
        
        elif verb == "validate_document":
            return {
                "success": True,
                "result": {
                    "valid": True,
                    "issues": []
                },
                "message": "Document validated"
            }
        
        else:
            return {
                "success": True,
                "result": {"verb": verb},
                "message": f"Document operation '{verb}' completed"
            }
    
    async def _execute_email(self, wu: WorkUnit) -> dict:
        """Mock email operations"""
        verb = wu.get("verb", "")
        
        await asyncio.sleep(0.05)
        
        return {
            "success": True,
            "result": {
                "message_id": f"MSG-{uuid.uuid4().hex[:8].upper()}",
                "recipient": wu.get("entities", {}).get("recipient_id", "unknown"),
                "sent_at": datetime.now().isoformat()
            },
            "message": f"Email operation '{verb}' completed"
        }
    
    async def _execute_workflow(self, wu: WorkUnit) -> dict:
        """Mock workflow operations"""
        verb = wu.get("verb", "")
        
        await asyncio.sleep(0.05)
        
        if verb == "approve_transaction":
            return {
                "success": True,
                "result": {
                    "approval_id": f"APR-{uuid.uuid4().hex[:8].upper()}",
                    "status": "approved",
                    "approved_at": datetime.now().isoformat()
                },
                "message": "Transaction approved"
            }
        
        elif verb == "escalate_issue":
            return {
                "success": True,
                "result": {
                    "escalation_id": f"ESC-{uuid.uuid4().hex[:8].upper()}",
                    "severity": wu.get("slots", {}).get("severity", "medium"),
                    "escalated_at": datetime.now().isoformat()
                },
                "message": "Issue escalated"
            }
        
        else:
            return {
                "success": True,
                "result": {"verb": verb},
                "message": f"Workflow operation '{verb}' completed"
            }
    
    async def _execute_unknown(self, wu: WorkUnit) -> dict:
        """Handler for unknown tools"""
        return {
            "success": False,
            "result": None,
            "message": f"Unknown tool: {wu.get('tool', 'unknown')}"
        }


# Singleton executor
_executor: Optional[MockToolExecutor] = None

def get_executor() -> MockToolExecutor:
    global _executor
    if _executor is None:
        _executor = MockToolExecutor()
    return _executor


# ============================================================
# MAIN PROCESS FUNCTION
# ============================================================

async def process(state: BabyMARSState) -> dict:
    """
    Execution Node
    
    Executes work units from the selected action:
    1. Validate work units
    2. Execute each work unit in sequence
    3. Collect results
    4. Handle errors gracefully
    """
    
    selected_action = state.get("selected_action")
    
    if not selected_action:
        return {
            "execution_results": [{
                "success": False,
                "message": "No action selected for execution"
            }]
        }
    
    work_units = selected_action.get("work_units", [])
    
    if not work_units:
        return {
            "execution_results": [{
                "success": True,
                "message": "No work units to execute"
            }]
        }
    
    executor = get_executor()
    results = []
    
    for wu in work_units:
        try:
            result = await executor.execute(wu)
            results.append({
                "unit_id": wu.get("unit_id", "unknown"),
                "tool": wu.get("tool", "unknown"),
                "verb": wu.get("verb", "unknown"),
                **result
            })
            
            # Stop on failure
            if not result.get("success", False):
                break
                
        except Exception as e:
            results.append({
                "unit_id": wu.get("unit_id", "unknown"),
                "tool": wu.get("tool", "unknown"),
                "verb": wu.get("verb", "unknown"),
                "success": False,
                "result": None,
                "message": f"Execution error: {str(e)}"
            })
            break
    
    return {
        "execution_results": results
    }
