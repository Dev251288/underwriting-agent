"""Mock Aadhaar OTP-based e-KYC API (UIDAI)."""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Optional


@dataclass
class AadhaarVerificationResponse:
    success: bool
    aadhaar_number: str
    name: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    mobile_linked: bool = False
    pan_linked: bool = False
    error_code: Optional[str] = None
    error_message: Optional[str] = None


_MOCK_RECORDS: dict[str, dict] = {
    "123456789012": {
        "name": "Rajesh Kumar Sharma",
        "date_of_birth": "1985-03-15",
        "gender": "M",
        "address": "Flat 4B, Sunrise Apartments, Koramangala, Bengaluru, Karnataka - 560034",
        "mobile_linked": True,
        "pan_linked": True,
    },
    "234567890123": {
        "name": "Priya Venkataraman",
        "date_of_birth": "1990-07-22",
        "gender": "F",
        "address": "12, Patel Nagar, Andheri West, Mumbai, Maharashtra - 400058",
        "mobile_linked": True,
        "pan_linked": True,
    },
    "987654321098": {
        "name": "Mohammed Iqbal Khan",
        "date_of_birth": "1978-11-30",
        "gender": "M",
        "address": "Plot 7, Sector 15, Gurgaon, Haryana - 122001",
        "mobile_linked": False,
        "pan_linked": False,
    },
}


def verify_aadhaar(aadhaar_number: str, otp: str = "123456") -> AadhaarVerificationResponse:
    """Mock Aadhaar verification. Returns synthetic data for known numbers."""
    aadhaar_number = aadhaar_number.replace(" ", "").strip()

    if len(aadhaar_number) != 12 or not aadhaar_number.isdigit():
        return AadhaarVerificationResponse(
            success=False,
            aadhaar_number=aadhaar_number,
            error_code="INVALID_AADHAAR",
            error_message="Aadhaar number must be 12 digits",
        )

    if otp != "123456":
        return AadhaarVerificationResponse(
            success=False,
            aadhaar_number=aadhaar_number,
            error_code="INVALID_OTP",
            error_message="OTP verification failed",
        )

    record = _MOCK_RECORDS.get(aadhaar_number)
    if record:
        return AadhaarVerificationResponse(
            success=True,
            aadhaar_number=aadhaar_number,
            **record,
        )

    # Generate plausible mock data for unknown numbers
    return AadhaarVerificationResponse(
        success=True,
        aadhaar_number=aadhaar_number,
        name="Test Applicant",
        date_of_birth="1987-06-10",
        gender="M",
        address="123 Main Street, New Delhi - 110001",
        mobile_linked=random.choice([True, False]),
        pan_linked=random.choice([True, True, False]),
    )
