"""Mock Land Registry and field valuation report APIs."""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class LandRegistryResponse:
    success: bool
    property_id: str
    owner_name: Optional[str] = None
    co_owner_names: list[str] = field(default_factory=list)
    survey_number: Optional[str] = None
    registered_area_sqft: Optional[float] = None
    registration_date: Optional[str] = None
    registration_number: Optional[str] = None
    encumbrances: list[str] = field(default_factory=list)  # list of outstanding liens/charges
    title_clear: bool = False
    property_type: Optional[str] = None
    locality: Optional[str] = None
    circle_rate_per_sqft: Optional[float] = None  # government guidance value
    error_code: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class FieldValuationReport:
    success: bool
    property_id: str
    market_value: Optional[float] = None
    distress_value: Optional[float] = None  # ~80% of market value
    construction_quality: Optional[str] = None  # "excellent", "good", "average", "poor"
    property_age_years: Optional[int] = None
    floor: Optional[str] = None
    total_floors: Optional[int] = None
    area_sqft: Optional[float] = None
    approved_plan_verified: bool = False
    occupation_certificate: bool = False
    locality_appreciation_trend: Optional[str] = None  # "rising", "stable", "declining"
    field_visit_date: Optional[str] = None
    valuer_name: Optional[str] = None
    risk_observations: list[str] = field(default_factory=list)
    error_code: Optional[str] = None


_REGISTRY_RECORDS: dict[str, dict] = {
    "PROP-KA-001": {
        "owner_name": "Rajesh Kumar Sharma",
        "survey_number": "34/2B",
        "registered_area_sqft": 1250.0,
        "registration_date": "2015-08-10",
        "registration_number": "KA-BLR-2015-45672",
        "encumbrances": [],
        "title_clear": True,
        "property_type": "apartment",
        "locality": "Koramangala, Bengaluru",
        "circle_rate_per_sqft": 8500.0,
    },
    "PROP-MH-002": {
        "owner_name": "Devendra Patil",
        "survey_number": "78/4A",
        "registered_area_sqft": 950.0,
        "registration_date": "2010-03-22",
        "registration_number": "MH-MUM-2010-12890",
        "encumbrances": ["Home loan mortgage with SBI (outstanding: ₹12,00,000)"],
        "title_clear": False,
        "property_type": "apartment",
        "locality": "Andheri West, Mumbai",
        "circle_rate_per_sqft": 22000.0,
    },
}

_VALUATION_RECORDS: dict[str, dict] = {
    "PROP-KA-001": {
        "market_value": 11500000.0,
        "distress_value": 9200000.0,
        "construction_quality": "good",
        "property_age_years": 9,
        "floor": "4th",
        "total_floors": 8,
        "area_sqft": 1250.0,
        "approved_plan_verified": True,
        "occupation_certificate": True,
        "locality_appreciation_trend": "rising",
        "field_visit_date": "2025-03-15",
        "valuer_name": "S. Krishnamurthy, RICS",
        "risk_observations": [],
    },
    "PROP-MH-002": {
        "market_value": 25000000.0,
        "distress_value": 20000000.0,
        "construction_quality": "average",
        "property_age_years": 14,
        "floor": "2nd",
        "total_floors": 6,
        "area_sqft": 950.0,
        "approved_plan_verified": True,
        "occupation_certificate": False,
        "locality_appreciation_trend": "stable",
        "field_visit_date": "2025-03-20",
        "valuer_name": "R. Mehta & Associates",
        "risk_observations": ["Occupation Certificate not obtained", "Existing mortgage lien present"],
    },
}


def fetch_land_registry(property_id: str, applicant_name: str) -> LandRegistryResponse:
    """Fetch mock land registry records."""
    record = _REGISTRY_RECORDS.get(property_id)
    if record:
        resp = LandRegistryResponse(success=True, property_id=property_id)
        for k, v in record.items():
            setattr(resp, k, v)
        return resp

    return LandRegistryResponse(
        success=True,
        property_id=property_id,
        owner_name=applicant_name,
        registered_area_sqft=round(random.uniform(600, 2000), 0),
        registration_date="2018-06-01",
        encumbrances=[],
        title_clear=True,
        property_type="apartment",
        locality="Unknown",
        circle_rate_per_sqft=round(random.uniform(5000, 15000), 0),
    )


def fetch_field_valuation(property_id: str) -> FieldValuationReport:
    """Fetch mock field valuation report."""
    record = _VALUATION_RECORDS.get(property_id)
    if record:
        resp = FieldValuationReport(success=True, property_id=property_id)
        for k, v in record.items():
            setattr(resp, k, v)
        return resp

    market_value = round(random.uniform(5_000_000, 25_000_000), 0)
    return FieldValuationReport(
        success=True,
        property_id=property_id,
        market_value=market_value,
        distress_value=round(market_value * 0.8, 0),
        construction_quality="good",
        property_age_years=random.randint(3, 15),
        approved_plan_verified=True,
        occupation_certificate=True,
        locality_appreciation_trend="stable",
        field_visit_date="2025-03-25",
        valuer_name="Mock Valuer & Associates",
    )
