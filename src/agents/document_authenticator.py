"""Agent 2 — Document Authenticator (runs in isolation per document)."""
from __future__ import annotations

from src.agents.base_agent import BaseAgent
from src.models.documents import AuthenticationStatus, Document

_SYSTEM_PROMPT = """You are a document fraud detection specialist at an Indian retail bank.
Your task is to authenticate individual loan application documents.

For each document, assess:
1. FORMAT VALIDITY: Does the document appear to be of the correct format for its type?
   - Aadhaar: 12-digit number, QR code mention, UIDAI branding
   - PAN: 10-character alphanumeric, Income Tax Dept branding
   - Salary slips: Company letterhead, PF deduction, TDS, CTC breakup
   - Bank statements: Bank letterhead, IFSC, account number, debit/credit columns
   - Property papers: Registration number, stamp duty, sub-registrar details

2. CONSISTENCY CHECKS:
   - Does the name on the document match what was provided in the application?
   - Are dates plausible (not future-dated, not expired beyond limits)?
   - Are amounts internally consistent?

3. TAMPERING INDICATORS:
   - Signs of digital editing (inconsistent fonts, pixel artifacts)
   - Missing standard elements
   - Implausible figures

Since you only have file metadata (not the actual document content in this system),
base your assessment on what can be inferred from the filename, file type, and
any provided applicant details. Flag uncertainties rather than making unfounded
assumptions.

Return a confidence score from 0.0 (definitely fake) to 1.0 (definitely genuine).
Scores below 0.4 = REJECTED, 0.4–0.65 = SUSPECT, 0.65–0.85 = GENUINE with flags,
0.85+ = GENUINE.
"""

_TOOL_SCHEMA = {
    "type": "object",
    "properties": {
        "auth_status": {
            "type": "string",
            "enum": ["genuine", "suspect", "rejected", "inconclusive"],
            "description": "Authentication verdict",
        },
        "confidence": {
            "type": "number",
            "description": "Confidence score 0.0 to 1.0",
        },
        "extracted_data": {
            "type": "object",
            "description": "Key data points extracted or inferred from the document",
            "additionalProperties": True,
        },
        "flags": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Specific concerns or observations",
        },
        "notes": {
            "type": "string",
            "description": "Detailed reasoning for the authentication verdict",
        },
    },
    "required": ["auth_status", "confidence", "extracted_data", "flags", "notes"],
}


class DocumentAuthenticatorAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__("DocumentAuthenticator", _SYSTEM_PROMPT)

    def authenticate(self, document: Document, applicant_name: str) -> Document:
        """Authenticate a single document. Mutates and returns the document."""
        user_message = (
            f"Authenticate the following document for applicant '{applicant_name}':\n\n"
            f"Document type: {document.doc_type.value}\n"
            f"Filename: {document.filename}\n"
            f"File size: {document.file_size_bytes or 'unknown'} bytes\n"
            f"Upload timestamp: {document.upload_timestamp}\n"
            f"Existing flags: {', '.join(document.auth_flags) if document.auth_flags else 'none'}\n\n"
            "Assess authenticity based on available metadata and document type expectations."
        )

        result = self._call_structured(
            user_message=user_message,
            tool_name="authenticate_document",
            tool_description="Authenticate a document and return verdict with extracted data",
            tool_schema=_TOOL_SCHEMA,
        )

        document.auth_status = AuthenticationStatus(result.get("auth_status", "inconclusive"))
        document.auth_confidence = float(result.get("confidence", 0.5))
        document.extracted_data = result.get("extracted_data", {})
        document.auth_flags = result.get("flags", [])
        document.auth_notes = result.get("notes", "")

        return document
