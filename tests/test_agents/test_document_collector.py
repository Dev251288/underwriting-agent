"""Unit tests for DocumentCollectorAgent (mocks the Claude API call)."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.agents.document_collector import DocumentCollectorAgent
from src.models.documents import DocumentType, UploadedFile


MOCK_TOOL_RESPONSE = {
    "documents": [
        {"filename": "aadhaar_card.pdf", "doc_type": "aadhaar", "notes": ""},
        {"filename": "pan_card.jpg", "doc_type": "pan", "notes": ""},
        {"filename": "salary_slip_mar2025.pdf", "doc_type": "salary_slip", "notes": ""},
        {"filename": "bank_statement_hdfc.pdf", "doc_type": "bank_statement", "notes": ""},
        {"filename": "property_deed.pdf", "doc_type": "property_papers", "notes": ""},
    ],
    "missing_required": ["form_16", "photograph"],
    "catalogue_notes": "Core documents present. Form 16 and photograph missing.",
}


@pytest.fixture
def sample_files() -> list[UploadedFile]:
    return [
        UploadedFile(filename="aadhaar_card.pdf", file_path="/uploads/aadhaar_card.pdf",
                     file_size_bytes=250000, mime_type="application/pdf"),
        UploadedFile(filename="pan_card.jpg", file_path="/uploads/pan_card.jpg",
                     file_size_bytes=80000, mime_type="image/jpeg"),
        UploadedFile(filename="salary_slip_mar2025.pdf", file_path="/uploads/salary_slip_mar2025.pdf",
                     file_size_bytes=130000, mime_type="application/pdf"),
        UploadedFile(filename="bank_statement_hdfc.pdf",
                     file_path="/uploads/bank_statement_hdfc.pdf",
                     file_size_bytes=900000, mime_type="application/pdf"),
        UploadedFile(filename="property_deed.pdf", file_path="/uploads/property_deed.pdf",
                     file_size_bytes=1500000, mime_type="application/pdf"),
    ]


@patch.object(DocumentCollectorAgent, "_call_structured", return_value=MOCK_TOOL_RESPONSE)
def test_catalogue_count(mock_call, sample_files):
    agent = DocumentCollectorAgent()
    catalogue = agent.run("APP-001", sample_files)
    assert catalogue.total_count == 5
    assert len(catalogue.documents) == 5


@patch.object(DocumentCollectorAgent, "_call_structured", return_value=MOCK_TOOL_RESPONSE)
def test_document_types_assigned(mock_call, sample_files):
    agent = DocumentCollectorAgent()
    catalogue = agent.run("APP-001", sample_files)
    types = {doc.doc_type for doc in catalogue.documents}
    assert DocumentType.AADHAAR in types
    assert DocumentType.PAN in types
    assert DocumentType.BANK_STATEMENT in types


@patch.object(DocumentCollectorAgent, "_call_structured", return_value=MOCK_TOOL_RESPONSE)
def test_missing_required_reported(mock_call, sample_files):
    agent = DocumentCollectorAgent()
    catalogue = agent.run("APP-001", sample_files)
    assert "form_16" in catalogue.missing_required
    assert "photograph" in catalogue.missing_required


@patch.object(DocumentCollectorAgent, "_call_structured", return_value=MOCK_TOOL_RESPONSE)
def test_file_metadata_preserved(mock_call, sample_files):
    agent = DocumentCollectorAgent()
    catalogue = agent.run("APP-001", sample_files)
    aadhaar = next(d for d in catalogue.documents if d.doc_type == DocumentType.AADHAAR)
    assert aadhaar.file_size_bytes == 250000
    assert aadhaar.file_path == "/uploads/aadhaar_card.pdf"


@patch.object(DocumentCollectorAgent, "_call_structured", return_value=MOCK_TOOL_RESPONSE)
def test_application_id_in_catalogue(mock_call, sample_files):
    agent = DocumentCollectorAgent()
    catalogue = agent.run("APP-XYZ", sample_files)
    assert catalogue.application_id == "APP-XYZ"


@patch.object(DocumentCollectorAgent, "_call_structured", return_value={
    "documents": [],
    "missing_required": ["aadhaar", "pan", "salary_slip", "bank_statement", "property_papers"],
    "catalogue_notes": "No documents uploaded.",
})
def test_empty_upload(mock_call):
    agent = DocumentCollectorAgent()
    catalogue = agent.run("APP-002", [])
    assert catalogue.total_count == 0
    assert len(catalogue.missing_required) == 5
