from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class ApplicationStatus(str, Enum):
    INITIATED = "initiated"
    DOCUMENTS_COLLECTED = "documents_collected"
    DOCUMENTS_AUTHENTICATED = "documents_authenticated"
    CONSISTENCY_CHECKED = "consistency_checked"
    KYC_VERIFIED = "kyc_verified"
    FINANCIALS_VERIFIED = "financials_verified"
    PROPERTY_VERIFIED = "property_verified"
    DASHBOARD_COMPILED = "dashboard_compiled"
    PENDING_MANAGER_DECISION = "pending_manager_decision"
    APPROVED = "approved"
    REJECTED = "rejected"
    REFERRED = "referred"
    CUSTOMER_FOLLOWUP_REQUIRED = "customer_followup_required"


class ApplicantDetails(BaseModel):
    full_name: str
    date_of_birth: Optional[str] = None
    aadhaar_number: Optional[str] = None
    pan_number: Optional[str] = None
    mobile: Optional[str] = None
    email: Optional[str] = None
    current_address: Optional[str] = None
    employment_type: Optional[str] = None  # salaried, self_employed, business
    employer_name: Optional[str] = None
    years_in_current_job: Optional[float] = None


class LoanDetails(BaseModel):
    loan_amount_requested: float
    property_value: Optional[float] = None
    loan_tenure_years: Optional[int] = None
    loan_purpose: Optional[str] = None  # purchase, construction, refinance, top_up
    property_type: Optional[str] = None  # apartment, villa, plot, commercial
    property_address: Optional[str] = None
    property_state: Optional[str] = None


class MortgageApplication(BaseModel):
    application_id: str
    status: ApplicationStatus = ApplicationStatus.INITIATED
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    applicant: ApplicantDetails
    loan: LoanDetails

    # Populated sequentially by the pipeline
    document_catalogue: Optional[dict[str, Any]] = None
    authentication_results: list[dict[str, Any]] = Field(default_factory=list)
    consistency_report: Optional[dict[str, Any]] = None
    kyc_result: Optional[dict[str, Any]] = None
    financial_result: Optional[dict[str, Any]] = None
    property_result: Optional[dict[str, Any]] = None
    underwriter_dashboard: Optional[dict[str, Any]] = None
    customer_communications: list[dict[str, Any]] = Field(default_factory=list)

    # Pipeline control
    cost_gate_passed: bool = False
    pipeline_errors: list[str] = Field(default_factory=list)
    manager_notes: Optional[str] = None
