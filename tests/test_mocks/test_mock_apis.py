"""Tests for all mock API modules."""
import pytest

from src.mocks.aadhaar_api import verify_aadhaar
from src.mocks.account_aggregator import fetch_account_data
from src.mocks.cibil_api import fetch_cibil_report
from src.mocks.land_registry import fetch_field_valuation, fetch_land_registry
from src.mocks.pan_api import verify_pan


class TestAadhaarAPI:
    def test_known_record_returns_correct_name(self):
        resp = verify_aadhaar("123456789012")
        assert resp.success is True
        assert "Rajesh" in resp.name

    def test_invalid_length_fails(self):
        resp = verify_aadhaar("12345")
        assert resp.success is False
        assert resp.error_code == "INVALID_AADHAAR"

    def test_non_digit_fails(self):
        resp = verify_aadhaar("12345678901A")
        assert resp.success is False

    def test_wrong_otp_fails(self):
        resp = verify_aadhaar("123456789012", otp="000000")
        assert resp.success is False
        assert resp.error_code == "INVALID_OTP"

    def test_unknown_aadhaar_returns_mock_data(self):
        resp = verify_aadhaar("111122223333")
        assert resp.success is True
        assert resp.name is not None


class TestPANAPI:
    def test_known_valid_pan(self):
        resp = verify_pan("ABCPS1234D")
        assert resp.success is True
        assert resp.pan_status == "VALID"
        assert resp.aadhaar_linked is True

    def test_known_fake_pan(self):
        resp = verify_pan("ZZZPX0000Z")
        assert resp.pan_status == "FAKE"

    def test_short_pan_fails(self):
        resp = verify_pan("ABC")
        assert resp.success is False
        assert resp.error_code == "INVALID_PAN_FORMAT"

    def test_lowercase_normalised(self):
        resp = verify_pan("abcps1234d")
        assert resp.pan_number == "ABCPS1234D"

    def test_unknown_pan_returns_mock_data(self):
        resp = verify_pan("QQQQQ9999Q")
        assert resp.success is True
        assert resp.pan_status == "VALID"


class TestCIBILAPI:
    def test_high_score_profile(self):
        resp = fetch_cibil_report("BVNPV5678F")
        assert resp.success is True
        assert resp.cibil_score >= 800
        assert resp.overdue_accounts == 0

    def test_low_score_profile(self):
        resp = fetch_cibil_report("CDQMK9012G")
        assert resp.success is True
        assert resp.cibil_score < 700
        assert resp.overdue_accounts > 0

    def test_score_within_valid_range(self):
        resp = fetch_cibil_report("ABCPS1234D")
        assert 300 <= resp.cibil_score <= 900

    def test_unknown_pan_returns_default(self):
        resp = fetch_cibil_report("QQQQQ9999Q")
        assert resp.success is True
        assert resp.cibil_score is not None


class TestAccountAggregator:
    def test_high_income_profile(self):
        resp = fetch_account_data("ABCPS1234D")
        assert resp.success is True
        assert resp.consent_given is True
        assert resp.total_monthly_income_estimated > 100_000
        assert len(resp.accounts) > 0

    def test_income_stability_score_in_range(self):
        resp = fetch_account_data("BVNPV5678F")
        assert 0.0 <= resp.income_stability_score <= 1.0

    def test_unknown_pan_returns_default(self):
        resp = fetch_account_data("QQQQQ9999Q")
        assert resp.success is True
        assert resp.total_monthly_income_estimated > 0


class TestLandRegistry:
    def test_known_clear_title(self):
        resp = fetch_land_registry("PROP-KA-001", "Rajesh Kumar Sharma")
        assert resp.success is True
        assert resp.title_clear is True
        assert len(resp.encumbrances) == 0

    def test_known_encumbered_property(self):
        resp = fetch_land_registry("PROP-MH-002", "Devendra Patil")
        assert resp.title_clear is False
        assert len(resp.encumbrances) > 0

    def test_valuation_market_value_positive(self):
        resp = fetch_field_valuation("PROP-KA-001")
        assert resp.success is True
        assert resp.market_value > 0
        assert resp.distress_value < resp.market_value

    def test_valuation_risk_observations(self):
        resp = fetch_field_valuation("PROP-MH-002")
        assert len(resp.risk_observations) > 0

    def test_unknown_property_returns_default(self):
        resp = fetch_land_registry("PROP-UNKNOWN-999", "Test Person")
        assert resp.success is True
        assert resp.owner_name == "Test Person"
