from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class VerificationStatus(str, Enum):
    VERIFIED = "verified"
    PARTIALLY_VERIFIED = "partially_verified"
    FAILED = "failed"
    PENDING = "pending"


class KYCResult(BaseModel):
    status: VerificationStatus
    aadhaar_verified: bool = False
    pan_verified: bool = False
    name_match_aadhaar: bool = False
    name_match_pan: bool = False
    dob_match: bool = False
    address_match: bool = False
    pan_aadhaar_linked: bool = False
    risk_flags: list[str] = Field(default_factory=list)
    notes: str = ""


class FinancialResult(BaseModel):
    status: VerificationStatus
    cibil_score: Optional[int] = None
    cibil_verified: bool = False
    income_verified: bool = False
    monthly_gross_income: Optional[float] = None
    monthly_net_income: Optional[float] = None
    existing_emi_obligations: Optional[float] = None
    foir: Optional[float] = None  # Fixed Obligations to Income Ratio
    eligible_loan_amount: Optional[float] = None
    account_aggregator_verified: bool = False
    average_bank_balance: Optional[float] = None
    risk_flags: list[str] = Field(default_factory=list)
    notes: str = ""


class PropertyResult(BaseModel):
    status: VerificationStatus
    title_clear: bool = False
    encumbrance_clear: bool = False
    market_value: Optional[float] = None
    distress_value: Optional[float] = None
    registry_verified: bool = False
    field_report_clear: bool = False
    ltv_ratio: Optional[float] = None  # Loan-to-Value Ratio
    property_age_years: Optional[int] = None
    approved_plan_available: bool = False
    risk_flags: list[str] = Field(default_factory=list)
    notes: str = ""


class UnderwriterDashboard(BaseModel):
    application_id: str
    applicant_name: str
    loan_amount_requested: float
    property_address: Optional[str] = None

    kyc_summary: Optional[KYCResult] = None
    financial_summary: Optional[FinancialResult] = None
    property_summary: Optional[PropertyResult] = None

    overall_risk_level: RiskLevel = RiskLevel.MEDIUM
    recommendation: str = ""  # "approve", "reject", "refer", "conditional_approve"
    key_concerns: list[str] = Field(default_factory=list)
    key_positives: list[str] = Field(default_factory=list)
    conditions_for_approval: list[str] = Field(default_factory=list)
    generated_at: str = ""
