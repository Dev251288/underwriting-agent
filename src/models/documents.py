from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    AADHAAR = "aadhaar"
    PAN = "pan"
    SALARY_SLIP = "salary_slip"
    BANK_STATEMENT = "bank_statement"
    FORM_16 = "form_16"
    ITR = "itr"
    PROPERTY_PAPERS = "property_papers"
    SALE_AGREEMENT = "sale_agreement"
    ENCUMBRANCE_CERTIFICATE = "encumbrance_certificate"
    NOC = "noc"
    EMPLOYMENT_LETTER = "employment_letter"
    OFFER_LETTER = "offer_letter"
    PHOTOGRAPH = "photograph"
    SIGNATURE = "signature"
    OTHER = "other"


class AuthenticationStatus(str, Enum):
    GENUINE = "genuine"
    SUSPECT = "suspect"
    REJECTED = "rejected"
    INCONCLUSIVE = "inconclusive"


class UploadedFile(BaseModel):
    filename: str
    file_path: str
    file_size_bytes: Optional[int] = None
    mime_type: Optional[str] = None


class Document(BaseModel):
    doc_id: str
    doc_type: DocumentType
    filename: str
    file_path: str
    file_size_bytes: Optional[int] = None
    upload_timestamp: str
    auth_status: AuthenticationStatus = AuthenticationStatus.INCONCLUSIVE
    extracted_data: dict[str, Any] = Field(default_factory=dict)
    auth_confidence: float = 0.0  # 0.0 to 1.0
    auth_flags: list[str] = Field(default_factory=list)
    auth_notes: str = ""


class DocumentCatalogue(BaseModel):
    application_id: str
    documents: list[Document] = Field(default_factory=list)
    total_count: int = 0
    missing_required: list[str] = Field(default_factory=list)
    catalogue_notes: str = ""

    REQUIRED_DOCS: list[str] = Field(
        default=[
            DocumentType.AADHAAR,
            DocumentType.PAN,
            DocumentType.BANK_STATEMENT,
            DocumentType.SALARY_SLIP,
            DocumentType.PROPERTY_PAPERS,
        ],
        exclude=True,
    )
