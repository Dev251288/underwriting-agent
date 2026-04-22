"""Agent 4 — Financial Verifier (CIBIL + Account Aggregator)."""
from __future__ import annotations

import dataclasses

from src.agents.base_agent import BaseAgent
from src.mocks.account_aggregator import fetch_account_data
from src.mocks.cibil_api import fetch_cibil_report

_SYSTEM_PROMPT = """You are a credit and financial analysis officer at an Indian retail bank.
You receive CIBIL credit report data and Account Aggregator bank data, and must assess
financial eligibility for a home loan.

Indian home loan underwriting guidelines:
- Minimum CIBIL score: 650 (preferred 700+, excellent 750+)
- FOIR (Fixed Obligations to Income Ratio): Maximum 50% (preferred <45%)
- FOIR = (existing EMI obligations + proposed new EMI) / net monthly income
- Standard EMI thumb-rule: ₹700–750 per lakh borrowed per month (at 8.5–9% for 20 years)
- Loan eligibility = typically 60× net monthly salary (varies by bank policy)
- Negative markers: 30+ DPD (days past due) in last 12 months = immediate flag
- Written-off or settled accounts = significant risk flag
- Multiple enquiries in 6 months (>3) = credit hunger flag

Bank statement analysis:
- Verify salary credits are regular and consistent with declared income
- Check for large unexplained debits
- Assess average monthly balance adequacy (should cover 3× monthly EMI)
- Income stability score from Account Aggregator is a key signal

Return a structured financial verification result with eligibility assessment.
"""

_TOOL_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {
            "type": "string",
            "enum": ["verified", "partially_verified", "failed", "pending"],
        },
        "cibil_score": {"type": "integer"},
        "cibil_verified": {"type": "boolean"},
        "income_verified": {"type": "boolean"},
        "monthly_gross_income": {"type": "number"},
        "monthly_net_income": {"type": "number"},
        "existing_emi_obligations": {"type": "number"},
        "foir": {"type": "number", "description": "Existing FOIR without the proposed loan"},
        "eligible_loan_amount": {
            "type": "number",
            "description": "Estimated maximum eligible loan amount in INR",
        },
        "account_aggregator_verified": {"type": "boolean"},
        "average_bank_balance": {"type": "number"},
        "risk_flags": {"type": "array", "items": {"type": "string"}},
        "notes": {"type": "string"},
    },
    "required": ["status", "cibil_verified", "income_verified", "risk_flags", "notes"],
}


class FinancialVerifierAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__("FinancialVerifier", _SYSTEM_PROMPT)

    def verify(
        self,
        pan_number: str,
        declared_monthly_income: float,
        loan_amount_requested: float,
        loan_tenure_years: int = 20,
    ) -> dict:
        cibil_resp = fetch_cibil_report(pan_number)
        aa_resp = fetch_account_data(pan_number)

        # Estimate proposed EMI for FOIR calculation
        proposed_emi = (loan_amount_requested / 100_000) * 725  # ~₹725 per lakh at 8.75% 20yr

        user_message = (
            f"Declared monthly income: {self._format_currency(declared_monthly_income)}\n"
            f"Loan amount requested: {self._format_currency(loan_amount_requested)}\n"
            f"Loan tenure: {loan_tenure_years} years\n"
            f"Estimated proposed EMI: {self._format_currency(proposed_emi)}\n\n"
            f"CIBIL REPORT:\n{dataclasses.asdict(cibil_resp)}\n\n"
            f"ACCOUNT AGGREGATOR DATA:\n{dataclasses.asdict(aa_resp)}\n\n"
            "Assess financial eligibility and return structured result."
        )

        return self._call_structured(
            user_message=user_message,
            tool_name="verify_financials",
            tool_description="Financial eligibility assessment based on CIBIL and AA data",
            tool_schema=_TOOL_SCHEMA,
        )
