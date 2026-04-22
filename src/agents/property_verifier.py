"""Agent 5 — Property Verifier (Land Registry + Field Valuation)."""
from __future__ import annotations

import dataclasses

from src.agents.base_agent import BaseAgent
from src.mocks.land_registry import fetch_field_valuation, fetch_land_registry

_SYSTEM_PROMPT = """You are a property and legal analyst at an Indian retail bank's home loan division.
You assess property eligibility for mortgage security based on land registry records and
field valuation reports.

Indian home loan property guidelines:
- LTV (Loan-to-Value) ratio limits per RBI:
  * Loans ≤ ₹30 lakhs: max 90% LTV
  * Loans ₹30–75 lakhs: max 80% LTV
  * Loans > ₹75 lakhs: max 75% LTV
- LTV is calculated on the lower of market value or agreement value
- Title must be clear — no encumbrances, disputes, or litigation
- Properties older than 30 years require additional legal opinion
- Unapproved constructions / deviation from sanctioned plan = risk flag
- Occupation Certificate is mandatory for completed constructions
- Properties in flood-prone, seismic zone IV/V areas require higher haircut

Key checks:
1. Owner name on registry matches applicant name
2. No encumbrances or existing mortgages (or if present, will be released on disbursement)
3. LTV ratio within RBI limits
4. Field valuation consistent with market (distress value ≥ loan amount is ideal)
5. Approved plan available and OC obtained
6. Property age and construction quality acceptable

Return a structured property verification result.
"""

_TOOL_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {
            "type": "string",
            "enum": ["verified", "partially_verified", "failed", "pending"],
        },
        "title_clear": {"type": "boolean"},
        "encumbrance_clear": {"type": "boolean"},
        "market_value": {"type": "number"},
        "distress_value": {"type": "number"},
        "registry_verified": {"type": "boolean"},
        "field_report_clear": {"type": "boolean"},
        "ltv_ratio": {
            "type": "number",
            "description": "Loan-to-Value ratio (loan_amount / property_value)",
        },
        "ltv_within_rbi_limits": {"type": "boolean"},
        "property_age_years": {"type": "integer"},
        "approved_plan_available": {"type": "boolean"},
        "risk_flags": {"type": "array", "items": {"type": "string"}},
        "notes": {"type": "string"},
    },
    "required": ["status", "title_clear", "registry_verified", "risk_flags", "notes"],
}


class PropertyVerifierAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__("PropertyVerifier", _SYSTEM_PROMPT)

    def verify(
        self,
        property_id: str,
        applicant_name: str,
        loan_amount_requested: float,
        declared_property_value: float | None = None,
    ) -> dict:
        registry_resp = fetch_land_registry(property_id, applicant_name)
        valuation_resp = fetch_field_valuation(property_id)

        user_message = (
            f"Applicant name: {applicant_name}\n"
            f"Property ID: {property_id}\n"
            f"Loan amount requested: {self._format_currency(loan_amount_requested)}\n"
            f"Declared property value: "
            f"{self._format_currency(declared_property_value) if declared_property_value else 'not provided'}\n\n"
            f"LAND REGISTRY RECORD:\n{dataclasses.asdict(registry_resp)}\n\n"
            f"FIELD VALUATION REPORT:\n{dataclasses.asdict(valuation_resp)}\n\n"
            "Assess property eligibility and LTV compliance. Return structured result."
        )

        return self._call_structured(
            user_message=user_message,
            tool_name="verify_property",
            tool_description="Property verification result based on land registry and field valuation",
            tool_schema=_TOOL_SCHEMA,
        )
