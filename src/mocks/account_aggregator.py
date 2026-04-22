"""Mock Account Aggregator (AA) API — RBI-regulated financial data sharing."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class MonthlyTransaction:
    month: str  # "2024-12", "2025-01", etc.
    total_credits: float
    total_debits: float
    closing_balance: float
    emi_debits: float = 0.0
    salary_credits: float = 0.0


@dataclass
class BankAccountData:
    bank_name: str
    account_type: str  # "savings", "current"
    account_number_masked: str  # last 4 digits only
    ifsc_code: str
    average_monthly_balance: float
    min_balance_last_6m: float
    max_balance_last_6m: float
    salary_credits_per_month: float
    other_credits_per_month: float
    monthly_transactions: list[MonthlyTransaction] = field(default_factory=list)


@dataclass
class AccountAggregatorResponse:
    success: bool
    pan_number: str
    consent_given: bool = False
    accounts: list[BankAccountData] = field(default_factory=list)
    total_monthly_income_estimated: float = 0.0
    income_stability_score: float = 0.0  # 0.0 to 1.0
    error_code: Optional[str] = None
    error_message: Optional[str] = None


_MOCK_RECORDS: dict[str, dict] = {
    "ABCPS1234D": {
        "consent_given": True,
        "total_monthly_income_estimated": 125000.0,
        "income_stability_score": 0.92,
        "accounts": [
            BankAccountData(
                bank_name="HDFC Bank",
                account_type="savings",
                account_number_masked="XXXX4521",
                ifsc_code="HDFC0001234",
                average_monthly_balance=280000.0,
                min_balance_last_6m=95000.0,
                max_balance_last_6m=520000.0,
                salary_credits_per_month=125000.0,
                other_credits_per_month=8000.0,
                monthly_transactions=[
                    MonthlyTransaction("2025-03", 138000, 112000, 310000, 22500, 125000),
                    MonthlyTransaction("2025-02", 127000, 105000, 284000, 22500, 125000),
                    MonthlyTransaction("2025-01", 125000, 98000, 262000, 22500, 125000),
                ],
            )
        ],
    },
    "BVNPV5678F": {
        "consent_given": True,
        "total_monthly_income_estimated": 85000.0,
        "income_stability_score": 0.95,
        "accounts": [
            BankAccountData(
                bank_name="SBI",
                account_type="savings",
                account_number_masked="XXXX7823",
                ifsc_code="SBIN0001452",
                average_monthly_balance=195000.0,
                min_balance_last_6m=82000.0,
                max_balance_last_6m=340000.0,
                salary_credits_per_month=85000.0,
                other_credits_per_month=3000.0,
            )
        ],
    },
    "CDQMK9012G": {
        "consent_given": True,
        "total_monthly_income_estimated": 65000.0,
        "income_stability_score": 0.55,
        "accounts": [
            BankAccountData(
                bank_name="Axis Bank",
                account_type="savings",
                account_number_masked="XXXX3391",
                ifsc_code="UTIB0002345",
                average_monthly_balance=42000.0,
                min_balance_last_6m=8500.0,
                max_balance_last_6m=98000.0,
                salary_credits_per_month=65000.0,
                other_credits_per_month=12000.0,
            )
        ],
    },
}


def fetch_account_data(pan_number: str) -> AccountAggregatorResponse:
    """Fetch mock account aggregator data."""
    pan_number = pan_number.upper().strip()

    record = _MOCK_RECORDS.get(pan_number)
    if record:
        r = AccountAggregatorResponse(success=True, pan_number=pan_number)
        for k, v in record.items():
            setattr(r, k, v)
        return r

    return AccountAggregatorResponse(
        success=True,
        pan_number=pan_number,
        consent_given=True,
        total_monthly_income_estimated=75000.0,
        income_stability_score=0.75,
        accounts=[
            BankAccountData(
                bank_name="ICICI Bank",
                account_type="savings",
                account_number_masked="XXXX9900",
                ifsc_code="ICIC0003456",
                average_monthly_balance=120000.0,
                min_balance_last_6m=35000.0,
                max_balance_last_6m=250000.0,
                salary_credits_per_month=75000.0,
                other_credits_per_month=5000.0,
            )
        ],
    )
