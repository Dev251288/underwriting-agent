"""Agent 7 — Customer Follow-up Communications."""
from __future__ import annotations

from src.agents.base_agent import BaseAgent
from src.models.application import ApplicationStatus, MortgageApplication

_SYSTEM_PROMPT = """You are a customer relationship specialist at an Indian retail bank's
home loan division. You draft professional, empathetic customer communications in English.

Communication types:
- DOCUMENT_REQUEST: Politely request missing or corrected documents
- CONSISTENCY_FAILURE: Inform customer of discrepancies that need resolution
- KYC_QUERY: Request KYC clarification without alarming the customer
- STATUS_UPDATE: Provide a status update on their application
- APPROVAL_CONDITIONAL: Inform of conditional approval with conditions
- REJECTION: Inform of rejection sensitively, explaining reasons without revealing all risk logic
- DISBURSEMENT_PENDING: Request documents/actions needed before disbursement

Tone guidelines:
- Professional but warm
- Clear about what action is required and by when
- Do not reveal internal risk scores or policy thresholds
- For rejections, offer to discuss alternatives (smaller loan, co-applicant, etc.)
- Include the applicant's name, application reference, and a specific deadline for action items
- Indian context: address as 'Dear Mr./Ms. [Surname]', sign as 'Home Loans Team'

Always include:
1. Subject line (for email)
2. SMS version (max 160 characters)
3. Full email body
"""

_TOOL_SCHEMA = {
    "type": "object",
    "properties": {
        "comm_type": {
            "type": "string",
            "enum": [
                "document_request",
                "consistency_failure",
                "kyc_query",
                "status_update",
                "approval_conditional",
                "rejection",
                "disbursement_pending",
            ],
        },
        "subject_line": {"type": "string", "description": "Email subject line"},
        "sms_message": {
            "type": "string",
            "description": "SMS version (max 160 chars)",
            "maxLength": 160,
        },
        "email_body": {"type": "string", "description": "Full email body in plain text"},
        "action_items": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Specific actions the customer needs to take",
        },
        "deadline_days": {
            "type": "integer",
            "description": "Number of calendar days the customer has to respond",
        },
    },
    "required": ["comm_type", "subject_line", "sms_message", "email_body", "action_items"],
}

_COMM_CONTEXT = {
    ApplicationStatus.CUSTOMER_FOLLOWUP_REQUIRED: "consistency_failure",
    ApplicationStatus.APPROVED: "status_update",
    ApplicationStatus.REJECTED: "rejection",
    ApplicationStatus.REFERRED: "approval_conditional",
}


class CustomerCommsAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__("CustomerComms", _SYSTEM_PROMPT)

    def draft_communication(
        self,
        application: MortgageApplication,
        comm_reason: str,
        specific_issues: list[str] | None = None,
        specific_conditions: list[str] | None = None,
    ) -> dict:
        issues_text = ""
        if specific_issues:
            issues_text = "\nIssues to address:\n" + "\n".join(f"- {i}" for i in specific_issues)

        conditions_text = ""
        if specific_conditions:
            conditions_text = "\nConditions:\n" + "\n".join(f"- {c}" for c in specific_conditions)

        user_message = (
            f"Draft a customer communication for:\n"
            f"Applicant: {application.applicant.full_name}\n"
            f"Application ID: {application.application_id}\n"
            f"Application status: {application.status.value}\n"
            f"Communication reason: {comm_reason}\n"
            f"Loan amount: {self._format_currency(application.loan.loan_amount_requested)}\n"
            f"Email: {application.applicant.email or 'not provided'}\n"
            f"Mobile: {application.applicant.mobile or 'not provided'}"
            + issues_text
            + conditions_text
        )

        return self._call_structured(
            user_message=user_message,
            tool_name="draft_communication",
            tool_description="Draft customer communication for a mortgage application event",
            tool_schema=_TOOL_SCHEMA,
            max_tokens=2048,
        )
