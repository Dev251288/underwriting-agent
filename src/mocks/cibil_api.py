"""Mock CIBIL (TransUnion) credit bureau API."""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CIBILAccountSummary:
    account_type: str  # "home_loan", "personal_loan", "credit_card", "auto_loan"
    lender_name: str
    sanctioned_amount: float
    outstanding_balance: float
    emi_amount: float
    status: str  # "active", "closed", "written_off", "settled"
    days_past_due: int = 0


@dataclass
class CIBILResponse:
    success: bool
    pan_number: str
    cibil_score: Optional[int] = None
    score_version: str = "CIBIL Score V3"
    total_accounts: int = 0
    active_accounts: int = 0
    closed_accounts: int = 0
    overdue_accounts: int = 0
    total_outstanding: float = 0.0
    total_emi_obligations: float = 0.0
    accounts: list[CIBILAccountSummary] = field(default_factory=list)
    written_off_amount: float = 0.0
    settled_amount: float = 0.0
    enquiries_last_6_months: int = 0
    error_code: Optional[str] = None
    error_message: Optional[str] = None


_MOCK_RECORDS: dict[str, dict] = {
    "ABCPS1234D": {
        "cibil_score": 762,
        "total_accounts": 3,
        "active_accounts": 2,
        "closed_accounts": 1,
        "overdue_accounts": 0,
        "total_outstanding": 850000.0,
        "total_emi_obligations": 22500.0,
        "written_off_amount": 0.0,
        "settled_amount": 0.0,
        "enquiries_last_6_months": 1,
        "accounts": [
            CIBILAccountSummary("personal_loan", "HDFC Bank", 300000, 180000, 9000, "active"),
            CIBILAccountSummary("credit_card", "ICICI Bank", 150000, 42000, 8000, "active", days_past_due=0),
            CIBILAccountSummary("auto_loan", "Kotak Bank", 550000, 0, 0, "closed"),
        ],
    },
    "BVNPV5678F": {
        "cibil_score": 810,
        "total_accounts": 2,
        "active_accounts": 1,
        "closed_accounts": 1,
        "overdue_accounts": 0,
        "total_outstanding": 200000.0,
        "total_emi_obligations": 8000.0,
        "written_off_amount": 0.0,
        "settled_amount": 0.0,
        "enquiries_last_6_months": 0,
        "accounts": [
            CIBILAccountSummary("credit_card", "SBI", 200000, 45000, 8000, "active"),
            CIBILAccountSummary("personal_loan", "Axis Bank", 100000, 0, 0, "closed"),
        ],
    },
    "CDQMK9012G": {
        "cibil_score": 615,
        "total_accounts": 4,
        "active_accounts": 3,
        "closed_accounts": 1,
        "overdue_accounts": 1,
        "total_outstanding": 1200000.0,
        "total_emi_obligations": 38000.0,
        "written_off_amount": 0.0,
        "settled_amount": 25000.0,
        "enquiries_last_6_months": 4,
        "accounts": [
            CIBILAccountSummary("personal_loan", "Bajaj Finance", 400000, 310000, 14000, "active", days_past_due=45),
            CIBILAccountSummary("credit_card", "HSBC", 100000, 95000, 12000, "active"),
            CIBILAccountSummary("auto_loan", "Mahindra Finance", 600000, 480000, 12000, "active"),
            CIBILAccountSummary("personal_loan", "Fullerton", 150000, 0, 0, "settled"),
        ],
    },
}


def fetch_cibil_report(pan_number: str) -> CIBILResponse:
    """Fetch mock CIBIL credit report."""
    pan_number = pan_number.upper().strip()

    record = _MOCK_RECORDS.get(pan_number)
    if record:
        r = CIBILResponse(success=True, pan_number=pan_number)
        for k, v in record.items():
            setattr(r, k, v)
        return r

    # Default mock with average profile
    return CIBILResponse(
        success=True,
        pan_number=pan_number,
        cibil_score=random.randint(650, 780),
        total_accounts=2,
        active_accounts=1,
        closed_accounts=1,
        overdue_accounts=0,
        total_outstanding=500000.0,
        total_emi_obligations=15000.0,
        enquiries_last_6_months=1,
    )
