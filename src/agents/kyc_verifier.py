"""Agent 3 — KYC Verifier (Aadhaar + PAN APIs)."""
from __future__ import annotations

import dataclasses

from src.agents.base_agent import BaseAgent
from src.mocks.aadhaar_api import verify_aadhaar
from src.mocks.pan_api import verify_pan

_SYSTEM_PROMPT = """You are a KYC (Know Your Customer) verification analyst at an Indian retail bank.
You receive the results of Aadhaar e-KYC and PAN verification API calls and must:

1. Assess whether KYC is complete and satisfactory for a home loan.
2. Check name matching between Aadhaar and PAN (minor spelling variations are acceptable).
3. Verify DOB consistency across both documents.
4. Flag if PAN–Aadhaar are not linked (mandatory per RBI and Income Tax guidelines).
5. Identify any risk signals such as:
   - Name mismatch > minor variation
   - Aadhaar mobile not linked
   - PAN status other than VALID
   - Address in Aadhaar being in a different state from the property

Return a structured KYC assessment for the underwriter dashboard.
"""

_TOOL_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {
            "type": "string",
            "enum": ["verified", "partially_verified", "failed", "pending"],
        },
        "aadhaar_verified": {"type": "boolean"},
        "pan_verified": {"type": "boolean"},
        "name_match_aadhaar": {"type": "boolean"},
        "name_match_pan": {"type": "boolean"},
        "dob_match": {"type": "boolean"},
        "address_match": {"type": "boolean"},
        "pan_aadhaar_linked": {"type": "boolean"},
        "risk_flags": {"type": "array", "items": {"type": "string"}},
        "notes": {"type": "string"},
    },
    "required": ["status", "aadhaar_verified", "pan_verified", "risk_flags", "notes"],
}


class KYCVerifierAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__("KYCVerifier", _SYSTEM_PROMPT)

    def verify(
        self,
        applicant_name: str,
        aadhaar_number: str,
        pan_number: str,
        declared_dob: str | None = None,
    ) -> dict:
        aadhaar_resp = verify_aadhaar(aadhaar_number)
        pan_resp = verify_pan(pan_number)

        aadhaar_data = dataclasses.asdict(aadhaar_resp)
        pan_data = dataclasses.asdict(pan_resp)

        user_message = (
            f"Applicant name (declared): {applicant_name}\n"
            f"Declared DOB: {declared_dob or 'not provided'}\n\n"
            f"AADHAAR API RESPONSE:\n{aadhaar_data}\n\n"
            f"PAN API RESPONSE:\n{pan_data}\n\n"
            "Perform KYC verification and return your structured assessment."
        )

        return self._call_structured(
            user_message=user_message,
            tool_name="verify_kyc",
            tool_description="KYC verification result based on Aadhaar and PAN API responses",
            tool_schema=_TOOL_SCHEMA,
        )
