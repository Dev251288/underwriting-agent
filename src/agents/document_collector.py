"""Agent 1 — Document Collector and Cataloguer."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from src.agents.base_agent import BaseAgent
from src.models.documents import (
    AuthenticationStatus,
    Document,
    DocumentCatalogue,
    DocumentType,
    UploadedFile,
)

_SYSTEM_PROMPT = """You are a mortgage document collection specialist at an Indian retail bank.
Your role is to:
1. Examine a list of uploaded files submitted by a loan applicant.
2. Classify each file into the correct document category (Aadhaar, PAN, salary slip, bank statement, property papers, etc.).
3. Identify any required documents that are missing for a home loan application in India.
4. Create a structured catalogue of all documents.

Required documents for a standard salaried home loan application:
- Aadhaar card (identity + address proof)
- PAN card (tax identity)
- Last 3 months' salary slips
- Last 6 months' bank statements (primary salary account)
- Form 16 or ITR for last 2 years
- Property papers / sale agreement
- Photograph and signature

Classify document types based on filename patterns, extensions, and obvious naming conventions.
Flag any documents that appear to be duplicates or potentially irrelevant.
"""

_TOOL_SCHEMA = {
    "type": "object",
    "properties": {
        "documents": {
            "type": "array",
            "description": "Classified documents",
            "items": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string"},
                    "doc_type": {
                        "type": "string",
                        "enum": [dt.value for dt in DocumentType],
                    },
                    "notes": {"type": "string", "description": "Any observations about this document"},
                },
                "required": ["filename", "doc_type"],
            },
        },
        "missing_required": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of required document types that appear to be missing",
        },
        "catalogue_notes": {
            "type": "string",
            "description": "Overall notes about the document set",
        },
    },
    "required": ["documents", "missing_required", "catalogue_notes"],
}


class DocumentCollectorAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__("DocumentCollector", _SYSTEM_PROMPT)

    def run(self, application_id: str, uploaded_files: list[UploadedFile]) -> DocumentCatalogue:
        file_descriptions = "\n".join(
            f"- {f.filename} ({f.mime_type or 'unknown type'}, {f.file_size_bytes or 'unknown'} bytes)"
            for f in uploaded_files
        )
        user_message = (
            f"Application ID: {application_id}\n\n"
            f"The following files have been uploaded by the applicant:\n{file_descriptions}\n\n"
            "Please classify each document and identify any missing required documents."
        )

        result = self._call_structured(
            user_message=user_message,
            tool_name="catalogue_documents",
            tool_description="Classify uploaded files and create a document catalogue",
            tool_schema=_TOOL_SCHEMA,
        )

        # Build Document objects from the LLM's classification
        file_map = {f.filename: f for f in uploaded_files}
        documents: list[Document] = []
        now = datetime.utcnow().isoformat()

        for doc_info in result.get("documents", []):
            fname = doc_info["filename"]
            source_file = file_map.get(fname)
            doc = Document(
                doc_id=str(uuid.uuid4()),
                doc_type=DocumentType(doc_info["doc_type"]),
                filename=fname,
                file_path=source_file.file_path if source_file else fname,
                file_size_bytes=source_file.file_size_bytes if source_file else None,
                upload_timestamp=now,
                auth_status=AuthenticationStatus.INCONCLUSIVE,
            )
            if doc_info.get("notes"):
                doc.auth_flags.append(doc_info["notes"])
            documents.append(doc)

        return DocumentCatalogue(
            application_id=application_id,
            documents=documents,
            total_count=len(documents),
            missing_required=result.get("missing_required", []),
            catalogue_notes=result.get("catalogue_notes", ""),
        )
