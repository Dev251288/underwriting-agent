"""Agent 6 — Underwriter Dashboard Compiler."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from src.agents.base_agent import BaseAgent
from src.models.application import MortgageApplication

_SYSTEM_PROMPT = """You are a senior mortgage underwriter assistant compiling a decision dashboard.
You receive all verification outputs from the pipeline and must synthesise them into a clear,
structured dashboard for the human underwriting manager who makes the final lending decision.

The dashboard must:
1. Present a clear summary of each verification domain (KYC, financials, property)
2. Highlight key positives that support the loan approval
3. Highlight key concerns that the manager must weigh
4. Suggest conditions under which the loan may be approved (e.g., reduced amount, additional security)
5. Provide an overall risk assessment (low / medium / high / critical)
6. Make a preliminary recommendation (approve / reject / refer / conditional_approve)
   — this is NOT a final decision; the manager retains full authority

IMPORTANT: You must NOT make autonomous credit decisions. Your role is to synthesise
information and present it clearly for the human manager's decision.

Indian mortgage context:
- Highlight if CIBIL score < 700 (borderline), < 650 (high risk)
- Flag if FOIR > 45% (borderline), > 50% (exceeds policy)
- Flag any KYC failures or document authentication issues
- Highlight LTV ratio vs RBI limits
- Note any encumbrances or legal issues with property
"""

_TOOL_SCHEMA = {
    "type": "object",
    "properties": {
        "overall_risk_level": {
            "type": "string",
            "enum": ["low", "medium", "high", "critical"],
        },
        "recommendation": {
            "type": "string",
            "enum": ["approve", "conditional_approve", "refer", "reject"],
            "description": "Preliminary recommendation for manager's consideration",
        },
        "key_positives": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Strengths of this application",
        },
        "key_concerns": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Risks and issues the manager should weigh",
        },
        "conditions_for_approval": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Conditions under which conditional_approve is suggested",
        },
        "executive_summary": {
            "type": "string",
            "description": "2–3 sentence narrative summary for the underwriter",
        },
        "data_gaps": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Any information still missing that manager should note",
        },
    },
    "required": [
        "overall_risk_level",
        "recommendation",
        "key_positives",
        "key_concerns",
        "conditions_for_approval",
        "executive_summary",
    ],
}


class DashboardCompilerAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__("DashboardCompiler", _SYSTEM_PROMPT)

    def compile(self, application: MortgageApplication) -> dict[str, Any]:
        user_message = (
            f"Application ID: {application.application_id}\n"
            f"Applicant: {application.applicant.full_name}\n"
            f"Loan requested: {self._format_currency(application.loan.loan_amount_requested)}\n"
            f"Property: {application.loan.property_address or 'not specified'}\n"
            f"Loan purpose: {application.loan.loan_purpose or 'purchase'}\n"
            f"Tenure: {application.loan.loan_tenure_years or 20} years\n\n"
            f"DOCUMENT CATALOGUE:\n{application.document_catalogue}\n\n"
            f"CONSISTENCY REPORT:\n{application.consistency_report}\n\n"
            f"KYC RESULT:\n{application.kyc_result}\n\n"
            f"FINANCIAL RESULT:\n{application.financial_result}\n\n"
            f"PROPERTY RESULT:\n{application.property_result}\n\n"
            "Compile the underwriter dashboard. Remember: the human manager makes the final decision."
        )

        result = self._call_structured(
            user_message=user_message,
            tool_name="compile_dashboard",
            tool_description="Compile a structured underwriter decision dashboard",
            tool_schema=_TOOL_SCHEMA,
            max_tokens=8192,
        )

        result["application_id"] = application.application_id
        result["applicant_name"] = application.applicant.full_name
        result["loan_amount_requested"] = application.loan.loan_amount_requested
        result["property_address"] = application.loan.property_address
        result["generated_at"] = datetime.utcnow().isoformat()

        return result
