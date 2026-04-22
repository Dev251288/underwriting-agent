"""Agent 2b — Cross-Document Consistency Checker (cost gate before external APIs)."""
from __future__ import annotations

from src.agents.base_agent import BaseAgent
from src.models.documents import Document

_SYSTEM_PROMPT = """You are a senior document review analyst at an Indian retail bank.
Your role is to perform cross-document consistency checks BEFORE expensive external API calls
(CIBIL, Aadhaar, PAN verification). You act as a cost gate — flagging applications that have
fundamental inconsistencies so they can be returned to the customer before incurring API costs.

Cross-document consistency checks:
1. NAME CONSISTENCY: Is the applicant's name spelled consistently across all documents?
   (Allow for minor variations: initials vs full name, surname order)
2. DATE OF BIRTH: Does DOB match across Aadhaar, PAN, salary slips?
3. ADDRESS: Is the address consistent across Aadhaar, salary slip, bank statement?
4. EMPLOYER/INCOME: Do salary slips, bank credits, and Form 16 show consistent income?
   (Allow ±10% variation for bonuses/deductions)
5. PAN–AADHAAR NUMBERS: Are the numbers internally formatted correctly?
6. EMPLOYMENT TENURE: Are the salary slip dates consistent with employment letter?
7. BANK ACCOUNT: Is the salary account number on the bank statement the one credited on salary slips?

Severity levels:
- CRITICAL: Fabrication suspected (name completely different, DOB off by years)
- HIGH: Significant discrepancy requiring explanation (income varies >30%, address mismatch)
- MEDIUM: Minor inconsistency requiring clarification
- LOW: Cosmetic difference (middle name on one doc but not another)

Return a go/no-go decision:
- go: Proceed to external API calls
- no_go: Return to customer with list of corrections needed
"""

_TOOL_SCHEMA = {
    "type": "object",
    "properties": {
        "decision": {
            "type": "string",
            "enum": ["go", "no_go"],
            "description": "Whether to proceed with external API calls",
        },
        "consistency_score": {
            "type": "number",
            "description": "Overall consistency score 0.0 to 1.0",
        },
        "discrepancies": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "field": {"type": "string"},
                    "severity": {"type": "string", "enum": ["critical", "high", "medium", "low"]},
                    "description": {"type": "string"},
                    "doc_types_involved": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["field", "severity", "description"],
            },
            "description": "List of identified discrepancies",
        },
        "customer_queries": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Specific questions to ask the customer if decision is no_go",
        },
        "notes": {"type": "string"},
    },
    "required": ["decision", "consistency_score", "discrepancies", "customer_queries", "notes"],
}


class ConsistencyCheckerAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__("ConsistencyChecker", _SYSTEM_PROMPT)

    def check(
        self,
        application_id: str,
        applicant_name: str,
        documents: list[Document],
        loan_amount: float,
    ) -> dict:
        doc_summaries = []
        for doc in documents:
            summary = (
                f"  - {doc.doc_type.value} ({doc.filename}): "
                f"status={doc.auth_status.value}, "
                f"extracted={doc.extracted_data}"
            )
            doc_summaries.append(summary)

        user_message = (
            f"Application ID: {application_id}\n"
            f"Applicant name (from application form): {applicant_name}\n"
            f"Loan amount requested: {self._format_currency(loan_amount)}\n\n"
            f"Authenticated documents and extracted data:\n"
            + "\n".join(doc_summaries)
            + "\n\nPerform cross-document consistency checks and return your verdict."
        )

        return self._call_structured(
            user_message=user_message,
            tool_name="check_consistency",
            tool_description="Cross-document consistency check and go/no-go decision",
            tool_schema=_TOOL_SCHEMA,
        )
