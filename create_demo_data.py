"""Seed demo applications into outputs/ for work queue testing."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path


OUTPUTS_DIR = Path(__file__).parent / "outputs"


def iso(dt: datetime) -> str:
    return dt.isoformat()


def now_utc() -> datetime:
    return datetime.now(tz=timezone.utc)


def _docs(names_types: list[tuple[str, str]], status: str = "genuine", confidence: float = 0.88) -> list[dict]:
    base_ts = iso(now_utc() - timedelta(days=10))
    return [
        {
            "doc_id": f"demo-{i:04d}",
            "doc_type": dtype,
            "filename": fname,
            "file_path": f"/uploads/{fname}",
            "file_size_bytes": 150000,
            "upload_timestamp": base_ts,
            "auth_status": status,
            "auth_confidence": confidence,
            "auth_flags": [],
            "auth_notes": "",
            "extracted_data": {},
        }
        for i, (fname, dtype) in enumerate(names_types)
    ]


def case_rajesh() -> dict:
    """C07D230C — Rajesh Kumar Sharma, pending_manager_decision. Tier 3."""
    now = now_utc()
    return {
        "application_id": "C07D230C",
        "status": "pending_manager_decision",
        "created_at": iso(now - timedelta(days=3)),
        "updated_at": iso(now - timedelta(days=1)),
        "applicant": {
            "full_name": "Rajesh Kumar Sharma",
            "date_of_birth": "1985-03-14",
            "aadhaar_number": "123456789012",
            "pan_number": "ABCPS1234D",
            "mobile": "+91-9810011223",
            "email": "rajesh.sharma@email.com",
            "current_address": "B-47, Sector 21, Noida - 201301",
            "employment_type": "salaried",
            "employer_name": "Infosys Limited",
            "years_in_current_job": 7.0,
        },
        "loan": {
            "loan_amount_requested": 11500000.0,
            "property_value": 15560000.0,
            "loan_tenure_years": 20,
            "loan_purpose": "purchase",
            "property_type": "apartment",
            "property_address": "Flat 12B, Lotus Heights, Sector 62, Noida - 201309",
            "property_state": "Uttar Pradesh",
        },
        "document_catalogue": {
            "application_id": "C07D230C",
            "documents": _docs([
                ("aadhaar_rajesh.pdf", "aadhaar"),
                ("pan_rajesh.pdf", "pan"),
                ("salary_jan.pdf", "salary_slip"),
                ("salary_feb.pdf", "salary_slip"),
                ("salary_mar.pdf", "salary_slip"),
                ("hdfc_stmt_6m.pdf", "bank_statement"),
                ("form16_fy24.pdf", "form_16"),
                ("sale_agreement_noida.pdf", "sale_agreement"),
                ("property_papers_noida.pdf", "property_papers"),
            ]),
            "total_count": 9,
            "missing_required": [
                "Form 16 / ITR for FY 2022-23 (second year required)",
                "Specimen signature on IndiaBank-prescribed format",
            ],
            "catalogue_notes": "Two required items outstanding. Sale agreement and property papers flagged inconclusive.",
        },
        "authentication_results": [
            {**d, "auth_status": "genuine", "auth_confidence": 0.89}
            for d in _docs([
                ("aadhaar_rajesh.pdf", "aadhaar"),
                ("pan_rajesh.pdf", "pan"),
                ("salary_jan.pdf", "salary_slip"),
                ("salary_feb.pdf", "salary_slip"),
                ("salary_mar.pdf", "salary_slip"),
                ("hdfc_stmt_6m.pdf", "bank_statement"),
                ("form16_fy24.pdf", "form_16"),
            ])
        ] + [
            {**d, "auth_status": "inconclusive", "auth_confidence": 0.61,
             "auth_flags": ["Stamp/seal clarity insufficient for final determination"],
             "auth_notes": "Legal re-vetting recommended before disbursement."}
            for d in _docs([
                ("sale_agreement_noida.pdf", "sale_agreement"),
                ("property_papers_noida.pdf", "property_papers"),
            ])
        ],
        "consistency_report": {
            "consistency_score": 0.78,
            "decision": "go",
            "discrepancies": [
                {
                    "severity": "medium",
                    "field": "income",
                    "description": (
                        "Declared monthly salary Rs.1,54,062 per salary slips; "
                        "bank credits show Rs.1,25,000 per month. "
                        "Variance requires written explanation."
                    ),
                }
            ],
        },
        "cost_gate_passed": True,
        "kyc_result": {
            "status": "verified",
            "aadhaar_verified": True,
            "pan_verified": True,
            "name_match_aadhaar": True,
            "name_match_pan": True,
            "dob_match": True,
            "address_match": True,
            "pan_aadhaar_linked": True,
            "risk_flags": [],
        },
        "financial_result": {
            "status": "partially_verified",
            "cibil_score": 762,
            "foir": 0.14,
            "monthly_net_income": 125000.0,
            "monthly_gross_income": 154062.0,
            "existing_emi_obligations": 17500.0,
            "eligible_loan_amount": 5000000.0,
            "average_bank_balance": 185000.0,
            "account_aggregator_verified": True,
            "risk_flags": [
                "income_mismatch_declared_vs_verified",
                "requested_amount_exceeds_eligibility_on_verified_income",
            ],
        },
        "property_result": {
            "status": "partially_verified",
            "ltv_ratio": 0.739,
            "title_clear": True,
            "market_value": 15560000.0,
            "distress_value": 13200000.0,
            "property_age_years": 6,
            "encumbrance_clear": True,
            "registry_verified": True,
            "approved_plan_available": True,
            "risk_flags": ["authentication_inconclusive_sale_agreement", "authentication_inconclusive_property_papers"],
        },
        "underwriter_dashboard": {
            "overall_risk_level": "medium",
            "recommendation": "approve_with_conditions",
            "executive_summary": (
                "Application can proceed subject to resolution of income variance and document gaps. "
                "CIBIL 762 is strong. LTV 73.9% is within RBI cap of 75% for loans above Rs.75L. "
                "Primary concern: loan of Rs.1.15 Cr is not supportable on bank-verified income of "
                "Rs.1.25L/month — eligibility on verified income is Rs.50L, not Rs.1.15 Cr. Applicant "
                "must substantiate declared income of Rs.1.54L/month or accept loan restructuring. "
                "Two documents also require re-authentication."
            ),
            "key_positives": [
                "CIBIL 762 — strong credit history, no defaults",
                "LTV 73.9% within RBI cap of 75%",
                "7 years at Infosys — stable employment",
                "Account Aggregator verified",
            ],
            "key_concerns": [
                "Loan Rs.1.15 Cr exceeds eligibility of Rs.50L on verified income of Rs.1.25L/month",
                "19% variance between declared salary slips (Rs.1.54L) and bank credits (Rs.1.25L)",
                "Sale agreement and property papers authentication inconclusive — legal re-vetting needed",
                "Form 16 for FY2022-23 not submitted",
                "Specimen signature missing",
            ],
            "conditions_for_approval": [
                {
                    "condition": "Loan amount of Rs.1,15,00,000 is not supportable on verified income of Rs.1,25,000/month (proposed FOIR 91%)",
                    "options": [
                        "Option A — Reduce loan quantum to Rs.50,00,000 (eligible on verified income of Rs.1,25,000/month at 50% FOIR)",
                        "Option B — Substantiate declared income of Rs.1,54,062/month with CA-certified financials",
                        "Option C — Add a co-applicant with verified net income of Rs.60,000/month or more",
                        "Option D — Extend tenure to 25 years (reduces monthly EMI to approximately Rs.1,03,000)",
                    ],
                },
                "Provide Form 16 or ITR-3 for FY 2022-23 (second year of two-year requirement)",
                "Submit specimen signature on IndiaBank-prescribed format for document verification",
                "Obtain legal re-vetting report for sale agreement and property papers (inconclusive authentication)",
            ],
            "data_gaps": [
                "Form 16 / ITR FY2022-23 missing",
                "Explanation for income variance between declared and bank-credited amounts",
            ],
            "generated_at": iso(now - timedelta(days=3)),
        },
        "pipeline_errors": [],
    }


def case_priya() -> dict:
    """A1B2C3D4 — Priya Venkataraman, conditions_pending, 5 days left."""
    now = now_utc()
    issued  = now - timedelta(days=2)
    deadline = now + timedelta(days=5)

    return {
        "application_id": "A1B2C3D4",
        "status": "conditions_pending",
        "created_at": iso(now - timedelta(days=5)),
        "updated_at": iso(issued),
        "applicant": {
            "full_name": "Priya Venkataraman",
            "date_of_birth": "1990-07-22",
            "aadhaar_number": "234567890123",
            "pan_number": "BVNPV5678F",
            "mobile": "+91-9845001122",
            "email": "priya.v@email.com",
            "current_address": "12A, Rainbow Residency, Velachery, Chennai - 600042",
            "employment_type": "salaried",
            "employer_name": "Tata Consultancy Services",
            "years_in_current_job": 6.0,
        },
        "loan": {
            "loan_amount_requested": 3500000.0,
            "property_value": 4900000.0,
            "loan_tenure_years": 15,
            "loan_purpose": "purchase",
            "property_type": "apartment",
            "property_address": "Flat 2C, Rainbow Residency, Velachery, Chennai - 600042",
            "property_state": "Tamil Nadu",
        },
        "document_catalogue": {
            "application_id": "A1B2C3D4",
            "documents": _docs([
                ("aadhaar_priya.pdf", "aadhaar"),
                ("pan_priya.pdf", "pan"),
                ("salary_slip_jan.pdf", "salary_slip"),
                ("salary_slip_feb.pdf", "salary_slip"),
                ("hdfc_stmt_6m.pdf", "bank_statement"),
                ("form16_2024.pdf", "form_16"),
                ("sale_agreement_velachery.pdf", "sale_agreement"),
            ]),
            "total_count": 7,
            "missing_required": [],
            "catalogue_notes": "All required documents present.",
        },
        "authentication_results": _docs([
            ("aadhaar_priya.pdf", "aadhaar"),
            ("pan_priya.pdf", "pan"),
            ("salary_slip_jan.pdf", "salary_slip"),
            ("salary_slip_feb.pdf", "salary_slip"),
            ("hdfc_stmt_6m.pdf", "bank_statement"),
            ("form16_2024.pdf", "form_16"),
            ("sale_agreement_velachery.pdf", "sale_agreement"),
        ], status="genuine", confidence=0.91),
        "consistency_report": {
            "consistency_score": 0.94,
            "decision": "go",
            "discrepancies": [],
        },
        "cost_gate_passed": True,
        "kyc_result": {
            "status": "verified",
            "aadhaar_verified": True,
            "pan_verified": True,
            "name_match_aadhaar": True,
            "name_match_pan": True,
            "dob_match": True,
            "address_match": True,
            "pan_aadhaar_linked": True,
            "risk_flags": [],
        },
        "financial_result": {
            "status": "verified",
            "cibil_score": 810,
            "foir": 0.14,
            "monthly_net_income": 115000.0,
            "monthly_gross_income": 140000.0,
            "existing_emi_obligations": 16000.0,
            "eligible_loan_amount": 4500000.0,
            "average_bank_balance": 210000.0,
            "account_aggregator_verified": True,
            "risk_flags": [],
        },
        "property_result": {
            "status": "verified",
            "ltv_ratio": 0.714,
            "title_clear": True,
            "market_value": 4900000.0,
            "distress_value": 4200000.0,
            "property_age_years": 3,
            "encumbrance_clear": True,
            "registry_verified": True,
            "approved_plan_available": True,
            "risk_flags": [],
        },
        "underwriter_dashboard": {
            "overall_risk_level": "low",
            "recommendation": "approve_with_conditions",
            "executive_summary": (
                "Strong application. Priya Venkataraman has an excellent CIBIL score of 810, "
                "verified income of Rs.1.15L/month from TCS, and clean KYC. LTV of 71.4% is "
                "within RBI norms. Loan approved with conditions: NOC from builder and EC required."
            ),
            "key_positives": [
                "CIBIL 810 — excellent credit history",
                "LTV 71.4% well within RBI 75% cap",
                "Consistent income verified via Account Aggregator",
                "All documents authentic and complete",
            ],
            "key_concerns": [
                "NOC from builder not yet submitted",
                "Encumbrance certificate pending for last 13 years",
            ],
            "conditions_for_approval": [
                "Submit NOC from builder/developer",
                "Provide Encumbrance Certificate (EC) for last 13 years",
            ],
            "data_gaps": [],
            "generated_at": iso(now - timedelta(days=5)),
        },
        "manager_decision": "approve_with_conditions",
        "manager_notes": "Good profile. Approve once builder NOC and EC are submitted.",
        "manager_decision_at": iso(issued),
        "action_deadline": iso(deadline),
        "action_issued_at": iso(issued),
        "action_type": "conditions_verification",
    }


def case_mohammed() -> dict:
    """E5F6G7H8 — Mohammed Iqbal Khan, customer_followup_required, OVERDUE."""
    now = now_utc()
    issued   = now - timedelta(days=8)
    deadline = now - timedelta(days=1)  # overdue

    return {
        "application_id": "E5F6G7H8",
        "status": "customer_followup_required",
        "created_at": iso(now - timedelta(days=12)),
        "updated_at": iso(issued),
        "applicant": {
            "full_name": "Mohammed Iqbal Khan",
            "date_of_birth": "1982-11-05",
            "aadhaar_number": "345678901234",
            "pan_number": "CDQMK9012G",
            "mobile": "+91-9900112233",
            "email": "miqbal.khan@email.com",
            "current_address": "Plot 7, Jubilee Hills, Hyderabad - 500033",
            "employment_type": "salaried",
            "employer_name": "Wipro Technologies",
            "years_in_current_job": 3.5,
        },
        "loan": {
            "loan_amount_requested": 5500000.0,
            "property_value": 7100000.0,
            "loan_tenure_years": 20,
            "loan_purpose": "purchase",
            "property_type": "apartment",
            "property_address": "Flat 9A, Jubilee Towers, Jubilee Hills, Hyderabad - 500033",
            "property_state": "Telangana",
        },
        "document_catalogue": {
            "application_id": "E5F6G7H8",
            "documents": _docs([
                ("aadhaar_khan.pdf", "aadhaar"),
                ("pan_khan.pdf", "pan"),
                ("salary_slip_jan.pdf", "salary_slip"),
                ("bank_stmt_4m.pdf", "bank_statement"),
            ]),
            "total_count": 4,
            "missing_required": ["salary_slip (Feb, Mar)", "form_16 or ITR (2 years)"],
            "catalogue_notes": "Incomplete document set — salary slips and Form 16 missing.",
        },
        "authentication_results": _docs([
            ("aadhaar_khan.pdf", "aadhaar"),
            ("pan_khan.pdf", "pan"),
            ("salary_slip_jan.pdf", "salary_slip"),
            ("bank_stmt_4m.pdf", "bank_statement"),
        ], status="genuine", confidence=0.79),
        "consistency_report": {
            "consistency_score": 0.71,
            "decision": "go",
            "discrepancies": [
                {
                    "severity": "medium",
                    "field": "income",
                    "description": "Declared income Rs.1.1L/month; bank credits show Rs.88,000/month — 20% variance.",
                }
            ],
        },
        "cost_gate_passed": True,
        "kyc_result": {
            "status": "verified",
            "aadhaar_verified": True,
            "pan_verified": True,
            "name_match_aadhaar": True,
            "name_match_pan": True,
            "dob_match": True,
            "address_match": False,
            "pan_aadhaar_linked": True,
            "risk_flags": ["Address on Aadhaar does not match loan application address"],
        },
        "financial_result": {
            "status": "partially_verified",
            "cibil_score": 615,
            "foir": 0.31,
            "monthly_net_income": 88000.0,
            "monthly_gross_income": 110000.0,
            "existing_emi_obligations": 27000.0,
            "eligible_loan_amount": 3200000.0,
            "average_bank_balance": 45000.0,
            "account_aggregator_verified": False,
            "risk_flags": [
                "income_mismatch_declared_vs_verified",
                "cibil_below_minimum_threshold",
                "requested_amount_exceeds_eligibility",
            ],
        },
        "property_result": {
            "status": "verified",
            "ltv_ratio": 0.775,
            "title_clear": True,
            "market_value": 7100000.0,
            "distress_value": 6100000.0,
            "property_age_years": 8,
            "encumbrance_clear": True,
            "registry_verified": True,
            "approved_plan_available": True,
            "risk_flags": [],
        },
        "underwriter_dashboard": {
            "overall_risk_level": "medium",
            "recommendation": "refer",
            "executive_summary": (
                "Borderline application. CIBIL of 615 is below the 650 minimum threshold. "
                "Income mismatch of 20% between declared and bank-verified salary. "
                "Requested Rs.55L exceeds eligibility of Rs.32L on verified income. "
                "Additional income proof requested from applicant."
            ),
            "key_positives": [
                "Property title clear, encumbrance certificate available",
                "7.75% LTV within 80% RBI limit",
            ],
            "key_concerns": [
                "CIBIL 615 is below minimum 650 threshold — exception case",
                "20% income mismatch between salary slips and bank credits",
                "Requested amount Rs.55L exceeds eligibility Rs.32L",
                "Only 1 month salary slip provided; 3 required",
                "Form 16/ITR not submitted",
            ],
            "conditions_for_approval": [
                "Submit 3 months salary slips (Feb and Mar 2026)",
                "Submit Form 16 for last 2 financial years",
                "Explain income variance between salary slips and bank statement",
            ],
            "data_gaps": ["Form 16 / ITR for FY2024 and FY2023 missing"],
            "generated_at": iso(now - timedelta(days=12)),
        },
        "manager_decision": "request_info",
        "manager_notes": "CIBIL borderline. Request Feb-Mar slips and Form 16 before deciding.",
        "manager_decision_at": iso(issued),
        "action_deadline": iso(deadline),
        "action_issued_at": iso(issued),
        "action_type": "customer_followup",
        "customer_communications": [
            {
                "comm_type": "document_request",
                "subject_line": "Action Required: Additional Documents Needed — Home Loan Application E5F6G7H8",
                "sms_message": (
                    "IndiaBank: Home Loan E5F6G7H8 requires additional docs by "
                    + (now - timedelta(days=1)).strftime("%d-%b-%Y")
                    + ". Submit salary slips (Feb, Mar) & Form 16. Call 1800-209-4006. -Home Loans Team"
                ),
                "email_body": (
                    "Dear Mr. Khan,\n\n"
                    "Thank you for applying for a Home Loan with IndiaBank (Application ID: E5F6G7H8).\n\n"
                    "Our team has reviewed your initial application and requires additional documentation "
                    "to complete the assessment:\n\n"
                    "1. Salary slips for February 2026 and March 2026\n"
                    "2. Form 16 for FY 2024-25 and FY 2023-24 (or ITR acknowledgements)\n\n"
                    "Please submit these documents at your earliest convenience. Our team will resume "
                    "processing your application immediately upon receipt.\n\n"
                    "Note: A response is required within 7 days to keep your application active.\n\n"
                    "For any queries, please contact your relationship manager or call 1800-209-4006 "
                    "(toll-free, Mon-Sat 9 AM–6 PM).\n\n"
                    "Warm regards,\n"
                    "Home Loans Team\n"
                    "IndiaBank"
                ),
                "action_items": [
                    "Submit salary slips for February 2026 and March 2026",
                    "Submit Form 16 for FY 2024-25 and FY 2023-24 (or ITR acknowledgements)",
                ],
                "deadline_days": 7,
                "sent_at": iso(issued + timedelta(minutes=3)),
                "sent_via": ["email", "sms"],
                "agent": "CustomerComms",
            }
        ],
    }


def case_sunita() -> dict:
    """I9J0K1L2 — Sunita Mehta, approved (view-only)."""
    now = now_utc()
    return {
        "application_id": "I9J0K1L2",
        "status": "approved",
        "created_at": iso(now - timedelta(days=14)),
        "updated_at": iso(now - timedelta(days=7)),
        "applicant": {
            "full_name": "Sunita Mehta",
            "date_of_birth": "1988-04-30",
            "aadhaar_number": "456789012345",
            "pan_number": "EFRPM3456H",
            "mobile": "+91-9711223344",
            "email": "sunita.mehta@email.com",
            "current_address": "B-204, Silver Oak, Andheri West, Mumbai - 400058",
            "employment_type": "salaried",
            "employer_name": "HDFC Bank Ltd",
            "years_in_current_job": 8.0,
        },
        "loan": {
            "loan_amount_requested": 2500000.0,
            "property_value": 3900000.0,
            "loan_tenure_years": 15,
            "loan_purpose": "purchase",
            "property_type": "apartment",
            "property_address": "Flat 204B, Silver Oak CHS, Andheri West, Mumbai - 400058",
            "property_state": "Maharashtra",
        },
        "document_catalogue": {
            "application_id": "I9J0K1L2",
            "documents": _docs([
                ("aadhaar_sunita.pdf", "aadhaar"),
                ("pan_sunita.pdf", "pan"),
                ("salary_jan.pdf", "salary_slip"),
                ("salary_feb.pdf", "salary_slip"),
                ("salary_mar.pdf", "salary_slip"),
                ("axis_stmt_6m.pdf", "bank_statement"),
                ("form16_fy24.pdf", "form_16"),
                ("form16_fy23.pdf", "form_16"),
                ("sale_agreement.pdf", "sale_agreement"),
                ("title_deed.pdf", "property_papers"),
            ]),
            "total_count": 10,
            "missing_required": [],
            "catalogue_notes": "Complete document set.",
        },
        "authentication_results": _docs([
            ("aadhaar_sunita.pdf", "aadhaar"),
            ("pan_sunita.pdf", "pan"),
            ("salary_jan.pdf", "salary_slip"),
            ("salary_feb.pdf", "salary_slip"),
            ("salary_mar.pdf", "salary_slip"),
            ("axis_stmt_6m.pdf", "bank_statement"),
            ("form16_fy24.pdf", "form_16"),
            ("form16_fy23.pdf", "form_16"),
            ("sale_agreement.pdf", "sale_agreement"),
            ("title_deed.pdf", "property_papers"),
        ], status="genuine", confidence=0.93),
        "consistency_report": {
            "consistency_score": 0.97,
            "decision": "go",
            "discrepancies": [],
        },
        "cost_gate_passed": True,
        "kyc_result": {
            "status": "verified",
            "aadhaar_verified": True,
            "pan_verified": True,
            "name_match_aadhaar": True,
            "name_match_pan": True,
            "dob_match": True,
            "address_match": True,
            "pan_aadhaar_linked": True,
            "risk_flags": [],
        },
        "financial_result": {
            "status": "verified",
            "cibil_score": 780,
            "foir": 0.12,
            "monthly_net_income": 95000.0,
            "monthly_gross_income": 115000.0,
            "existing_emi_obligations": 11000.0,
            "eligible_loan_amount": 4200000.0,
            "average_bank_balance": 280000.0,
            "account_aggregator_verified": True,
            "risk_flags": [],
        },
        "property_result": {
            "status": "verified",
            "ltv_ratio": 0.641,
            "title_clear": True,
            "market_value": 3900000.0,
            "distress_value": 3400000.0,
            "property_age_years": 5,
            "encumbrance_clear": True,
            "registry_verified": True,
            "approved_plan_available": True,
            "risk_flags": [],
        },
        "underwriter_dashboard": {
            "overall_risk_level": "low",
            "recommendation": "approve",
            "executive_summary": (
                "Clean application. Sunita Mehta has a CIBIL of 780, stable HDFC Bank employment "
                "of 8 years, and verified income of Rs.95K/month. LTV of 64.1% is well within "
                "RBI limits. All documents authentic, no discrepancies. Recommended for approval."
            ),
            "key_positives": [
                "CIBIL 780 — strong credit profile",
                "LTV 64.1% significantly below RBI cap",
                "8 years at HDFC Bank — excellent employment stability",
                "Complete document set, all authenticated",
                "FOIR 12% well within 50% policy cap",
            ],
            "key_concerns": [],
            "conditions_for_approval": [],
            "data_gaps": [],
            "generated_at": iso(now - timedelta(days=14)),
        },
        "manager_decision": "approve",
        "manager_notes": "Clean profile. Approve.",
        "manager_decision_at": iso(now - timedelta(days=7)),
    }


def case_ramesh() -> dict:
    """M3N4O5P6 — Ramesh Patil, rejected (view-only)."""
    now = now_utc()
    return {
        "application_id": "M3N4O5P6",
        "status": "rejected",
        "created_at": iso(now - timedelta(days=20)),
        "updated_at": iso(now - timedelta(days=10)),
        "applicant": {
            "full_name": "Ramesh Patil",
            "date_of_birth": "1975-08-12",
            "aadhaar_number": "567890123456",
            "pan_number": "FGSRP7890J",
            "mobile": "+91-9833445566",
            "email": "ramesh.patil@email.com",
            "current_address": "Shop 3, Laxmi Market, Hadapsar, Pune - 411028",
            "employment_type": "self_employed",
            "employer_name": "Patil Enterprises",
            "years_in_current_job": 12.0,
        },
        "loan": {
            "loan_amount_requested": 7500000.0,
            "property_value": 8500000.0,
            "loan_tenure_years": 20,
            "loan_purpose": "purchase",
            "property_type": "villa",
            "property_address": "Plot 22, Baner Road, Pune - 411045",
            "property_state": "Maharashtra",
        },
        "document_catalogue": {
            "application_id": "M3N4O5P6",
            "documents": _docs([
                ("aadhaar_ramesh.pdf", "aadhaar"),
                ("pan_ramesh.pdf", "pan"),
                ("itr_fy24.pdf", "itr"),
                ("gst_returns.pdf", "bank_statement"),
            ]),
            "total_count": 4,
            "missing_required": ["bank_statement (6 months)", "property_papers"],
            "catalogue_notes": "Incomplete — bank statement and property papers missing.",
        },
        "authentication_results": _docs([
            ("aadhaar_ramesh.pdf", "aadhaar"),
            ("pan_ramesh.pdf", "pan"),
            ("itr_fy24.pdf", "itr"),
            ("gst_returns.pdf", "bank_statement"),
        ], status="genuine", confidence=0.72),
        "consistency_report": {
            "consistency_score": 0.58,
            "decision": "go",
            "discrepancies": [
                {
                    "severity": "high",
                    "field": "income",
                    "description": "ITR shows net profit Rs.45,000/month; GST returns imply turnover inconsistent with claimed business income.",
                },
                {
                    "severity": "high",
                    "field": "loan_amount",
                    "description": "Requested Rs.75L against verified monthly income of Rs.45K — FOIR would exceed 70%.",
                },
            ],
        },
        "cost_gate_passed": True,
        "kyc_result": {
            "status": "verified",
            "aadhaar_verified": True,
            "pan_verified": True,
            "name_match_aadhaar": True,
            "name_match_pan": True,
            "dob_match": True,
            "address_match": True,
            "pan_aadhaar_linked": True,
            "risk_flags": [],
        },
        "financial_result": {
            "status": "partially_verified",
            "cibil_score": 580,
            "foir": 0.22,
            "monthly_net_income": 45000.0,
            "monthly_gross_income": 55000.0,
            "existing_emi_obligations": 10000.0,
            "eligible_loan_amount": 1800000.0,
            "average_bank_balance": 32000.0,
            "account_aggregator_verified": False,
            "risk_flags": [
                "cibil_below_minimum_threshold",
                "requested_amount_exceeds_eligibility",
                "proposed_foir_exceeds_limit",
                "income_unverifiable_self_employed",
            ],
        },
        "property_result": {
            "status": "partially_verified",
            "ltv_ratio": 0.882,
            "title_clear": False,
            "market_value": 8500000.0,
            "distress_value": 6800000.0,
            "property_age_years": 15,
            "encumbrance_clear": False,
            "registry_verified": False,
            "approved_plan_available": False,
            "risk_flags": [
                "title_not_clear",
                "encumbrance_pending",
                "ltv_exceeds_rbi_cap_80pct",
            ],
        },
        "underwriter_dashboard": {
            "overall_risk_level": "high",
            "recommendation": "reject",
            "executive_summary": (
                "Application declined. CIBIL of 580 is significantly below the 650 minimum. "
                "LTV of 88.2% violates RBI cap of 80% for loans above Rs.30L. "
                "Self-employed income unverifiable — ITR shows only Rs.45K/month against "
                "Rs.75L requested (FOIR would exceed 70%). Property title not clear."
            ),
            "key_positives": ["Applicant has 12 years in business"],
            "key_concerns": [
                "CIBIL 580 — well below minimum 650 threshold",
                "LTV 88.2% exceeds RBI maximum of 80%",
                "Proposed FOIR would be 72% — far above 50% policy cap",
                "Property title not clear; encumbrance certificate pending",
                "Eligible loan Rs.18L vs requested Rs.75L",
                "No bank statement or property papers submitted",
            ],
            "conditions_for_approval": [],
            "data_gaps": [
                "6-month bank statement missing",
                "Property title deed and EC missing",
            ],
            "generated_at": iso(now - timedelta(days=20)),
        },
        "manager_decision": "reject",
        "manager_notes": (
            "Cannot proceed — CIBIL 580, LTV 88%, title not clear. "
            "Fundamental eligibility failure on multiple parameters."
        ),
        "manager_decision_at": iso(now - timedelta(days=10)),
    }


def main() -> None:
    OUTPUTS_DIR.mkdir(exist_ok=True)

    for case_fn in [case_rajesh, case_priya, case_mohammed, case_sunita, case_ramesh]:
        data = case_fn()
        app_id = data["application_id"]
        path = OUTPUTS_DIR / f"{app_id}.json"
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Created -> {path}  [{data['status']}]")

    print(f"\nSeeded 5 applications into {OUTPUTS_DIR}")
    print("Run 'python main.py serve' and open http://127.0.0.1:8000")


if __name__ == "__main__":
    main()
