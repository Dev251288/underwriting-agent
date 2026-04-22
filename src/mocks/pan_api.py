"""Mock PAN verification API (Income Tax Department / NSDL)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class PANVerificationResponse:
    success: bool
    pan_number: str
    name: Optional[str] = None
    date_of_birth: Optional[str] = None
    pan_status: Optional[str] = None  # "VALID", "INACTIVE", "FAKE"
    pan_category: Optional[str] = None  # "P" = individual, "C" = company
    aadhaar_linked: bool = False
    name_on_pan: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None


_MOCK_RECORDS: dict[str, dict] = {
    "ABCPS1234D": {
        "name": "Rajesh Kumar Sharma",
        "date_of_birth": "1985-03-15",
        "pan_status": "VALID",
        "pan_category": "P",
        "aadhaar_linked": True,
        "name_on_pan": "RAJESH KUMAR SHARMA",
    },
    "BVNPV5678F": {
        "name": "Priya Venkataraman",
        "date_of_birth": "1990-07-22",
        "pan_status": "VALID",
        "pan_category": "P",
        "aadhaar_linked": True,
        "name_on_pan": "PRIYA VENKATARAMAN",
    },
    "CDQMK9012G": {
        "name": "Mohammed Iqbal Khan",
        "date_of_birth": "1978-11-30",
        "pan_status": "VALID",
        "pan_category": "P",
        "aadhaar_linked": False,
        "name_on_pan": "MOHAMMED IQBAL KHAN",
    },
    "ZZZPX0000Z": {
        "name": "Fake Person",
        "date_of_birth": "2000-01-01",
        "pan_status": "FAKE",
        "pan_category": "P",
        "aadhaar_linked": False,
        "name_on_pan": "FAKE PERSON",
    },
}


def verify_pan(pan_number: str) -> PANVerificationResponse:
    """Mock PAN verification."""
    pan_number = pan_number.upper().strip()

    if len(pan_number) != 10:
        return PANVerificationResponse(
            success=False,
            pan_number=pan_number,
            error_code="INVALID_PAN_FORMAT",
            error_message="PAN must be 10 characters (e.g. ABCDE1234F)",
        )

    record = _MOCK_RECORDS.get(pan_number)
    if record:
        return PANVerificationResponse(
            success=True,
            pan_number=pan_number,
            **record,
        )

    # Default mock for unknown PANs
    return PANVerificationResponse(
        success=True,
        pan_number=pan_number,
        name="Test Applicant",
        date_of_birth="1987-06-10",
        pan_status="VALID",
        pan_category="P",
        aadhaar_linked=True,
        name_on_pan="TEST APPLICANT",
    )
