"""Mortgage underwriting pipeline orchestrator."""
from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path

from src.agents.consistency_checker import ConsistencyCheckerAgent
from src.agents.customer_comms import CustomerCommsAgent
from src.agents.dashboard_compiler import DashboardCompilerAgent
from src.agents.document_authenticator import DocumentAuthenticatorAgent
from src.agents.document_collector import DocumentCollectorAgent
from src.agents.financial_verifier import FinancialVerifierAgent
from src.agents.kyc_verifier import KYCVerifierAgent
from src.agents.property_verifier import PropertyVerifierAgent
from src.models.application import ApplicationStatus, MortgageApplication
from src.models.documents import AuthenticationStatus, UploadedFile


class MortgageUnderwritingOrchestrator:
    """
    Manages the 7-agent underwriting pipeline.

    Pipeline order:
      1  DocumentCollector    — catalogue uploaded files
      2  DocumentAuthenticator — authenticate each document in isolation
      2b ConsistencyChecker   — cross-document check + cost gate
      3  KYCVerifier          — Aadhaar + PAN APIs (mock)
      4  FinancialVerifier    — CIBIL + Account Aggregator (mock)
      5  PropertyVerifier     — Land Registry + Field Report (mock)
      6  DashboardCompiler    — compile underwriter dashboard
      7  CustomerComms        — draft communications as needed

    The underwriting manager makes all final decisions.
    No autonomous credit decisions are made.
    """

    def __init__(self) -> None:
        self.document_collector = DocumentCollectorAgent()
        self.document_authenticator = DocumentAuthenticatorAgent()
        self.consistency_checker = ConsistencyCheckerAgent()
        self.kyc_verifier = KYCVerifierAgent()
        self.financial_verifier = FinancialVerifierAgent()
        self.property_verifier = PropertyVerifierAgent()
        self.dashboard_compiler = DashboardCompilerAgent()
        self.customer_comms = CustomerCommsAgent()

    def process_application(
        self,
        application: MortgageApplication,
        uploaded_files: list[UploadedFile],
    ) -> MortgageApplication:
        """
        Run the full underwriting pipeline for an application.
        Returns the updated application at whatever stage it reached.
        """
        print(f"\n{'='*60}")
        print(f"Processing application: {application.application_id}")
        print(f"Applicant: {application.applicant.full_name}")
        print(f"Loan: ₹{application.loan.loan_amount_requested:,.0f}")
        print(f"{'='*60}\n")

        try:
            application = self._step_collect_documents(application, uploaded_files)
            application = self._step_authenticate_documents(application)
            application = self._step_consistency_check(application)

            if not application.cost_gate_passed:
                application = self._step_customer_followup(application, "consistency_failure")
                return application

            application = self._step_kyc_verification(application)
            application = self._step_financial_verification(application)
            application = self._step_property_verification(application)
            application = self._step_compile_dashboard(application)

        except Exception as exc:
            application.pipeline_errors.append(f"Pipeline error: {exc}")
            print(f"[ERROR] Pipeline stopped: {exc}")

        return application

    # ------------------------------------------------------------------ #
    # Pipeline steps                                                       #
    # ------------------------------------------------------------------ #

    def _step_collect_documents(
        self,
        application: MortgageApplication,
        uploaded_files: list[UploadedFile],
    ) -> MortgageApplication:
        print("[Step 1] Collecting and cataloguing documents...")
        catalogue = self.document_collector.run(application.application_id, uploaded_files)
        application.document_catalogue = catalogue.model_dump()
        application.status = ApplicationStatus.DOCUMENTS_COLLECTED
        application.updated_at = datetime.utcnow()

        if catalogue.missing_required:
            print(f"  Missing required docs: {catalogue.missing_required}")

        print(f"  Catalogued {catalogue.total_count} documents.")
        return application

    def _step_authenticate_documents(
        self, application: MortgageApplication
    ) -> MortgageApplication:
        print("[Step 2] Authenticating documents...")
        catalogue_data = application.document_catalogue or {}
        docs_raw = catalogue_data.get("documents", [])

        from src.models.documents import Document

        authenticated = []
        for doc_data in docs_raw:
            doc = Document(**doc_data)
            doc = self.document_authenticator.authenticate(
                doc, application.applicant.full_name
            )
            result = {
                "doc_id": doc.doc_id,
                "doc_type": doc.doc_type.value,
                "filename": doc.filename,
                "file_path": doc.file_path,
                "file_size_bytes": doc.file_size_bytes,
                "upload_timestamp": doc.upload_timestamp,
                "auth_status": doc.auth_status.value,
                "auth_confidence": doc.auth_confidence,
                "extracted_data": doc.extracted_data,
                "auth_flags": doc.auth_flags,
                "auth_notes": doc.auth_notes,
            }
            authenticated.append(result)
            status_icon = "✓" if doc.auth_status == AuthenticationStatus.GENUINE else "⚠"
            print(
                f"  {status_icon} {doc.doc_type.value}: {doc.auth_status.value} "
                f"(confidence: {doc.auth_confidence:.2f})"
            )

        application.authentication_results = authenticated
        application.status = ApplicationStatus.DOCUMENTS_AUTHENTICATED
        application.updated_at = datetime.utcnow()
        return application

    def _step_consistency_check(
        self, application: MortgageApplication
    ) -> MortgageApplication:
        print("[Step 2b] Running cross-document consistency check (cost gate)...")
        from src.models.documents import Document

        docs = [
            Document(**d) for d in (application.authentication_results or [])
        ]

        result = self.consistency_checker.check(
            application_id=application.application_id,
            applicant_name=application.applicant.full_name,
            documents=docs,
            loan_amount=application.loan.loan_amount_requested,
        )

        application.consistency_report = result
        application.status = ApplicationStatus.CONSISTENCY_CHECKED
        application.updated_at = datetime.utcnow()

        decision = result.get("decision", "no_go")
        score = result.get("consistency_score", 0.0)
        discrepancies = result.get("discrepancies", [])

        print(f"  Decision: {decision.upper()} | Consistency score: {score:.2f}")
        if discrepancies:
            for d in discrepancies:
                print(f"  [{d.get('severity','?').upper()}] {d.get('field')}: {d.get('description')}")

        application.cost_gate_passed = decision == "go"
        return application

    def _step_kyc_verification(
        self, application: MortgageApplication
    ) -> MortgageApplication:
        print("[Step 3] KYC verification (Aadhaar + PAN)...")
        applicant = application.applicant

        result = self.kyc_verifier.verify(
            applicant_name=applicant.full_name,
            aadhaar_number=applicant.aadhaar_number or "",
            pan_number=applicant.pan_number or "",
            declared_dob=applicant.date_of_birth,
        )

        application.kyc_result = result
        application.status = ApplicationStatus.KYC_VERIFIED
        application.updated_at = datetime.utcnow()
        print(f"  KYC status: {result.get('status')} | Flags: {result.get('risk_flags', [])}")
        return application

    def _step_financial_verification(
        self, application: MortgageApplication
    ) -> MortgageApplication:
        print("[Step 4] Financial verification (CIBIL + Account Aggregator)...")

        # Pull monthly income from extracted data if available, else use a default
        declared_income = self._extract_declared_income(application)

        result = self.financial_verifier.verify(
            pan_number=application.applicant.pan_number or "",
            declared_monthly_income=declared_income,
            loan_amount_requested=application.loan.loan_amount_requested,
            loan_tenure_years=application.loan.loan_tenure_years or 20,
        )

        application.financial_result = result
        application.status = ApplicationStatus.FINANCIALS_VERIFIED
        application.updated_at = datetime.utcnow()
        score = result.get("cibil_score", "N/A")
        foir = result.get("foir")
        foir_str = f"{foir:.1%}" if foir else "N/A"
        print(f"  CIBIL: {score} | FOIR: {foir_str} | Flags: {result.get('risk_flags', [])}")
        return application

    def _step_property_verification(
        self, application: MortgageApplication
    ) -> MortgageApplication:
        print("[Step 5] Property verification (Land Registry + Field Report)...")

        # Use a mock property ID derived from the application
        property_id = f"PROP-{application.application_id[:8].upper()}"

        result = self.property_verifier.verify(
            property_id=property_id,
            applicant_name=application.applicant.full_name,
            loan_amount_requested=application.loan.loan_amount_requested,
            declared_property_value=application.loan.property_value,
        )

        application.property_result = result
        application.status = ApplicationStatus.PROPERTY_VERIFIED
        application.updated_at = datetime.utcnow()
        ltv = result.get("ltv_ratio")
        ltv_str = f"{ltv:.1%}" if ltv else "N/A"
        print(
            f"  Title clear: {result.get('title_clear')} | "
            f"LTV: {ltv_str} | Flags: {result.get('risk_flags', [])}"
        )
        return application

    def _step_compile_dashboard(
        self, application: MortgageApplication
    ) -> MortgageApplication:
        print("[Step 6] Compiling underwriter dashboard...")
        dashboard = self.dashboard_compiler.compile(application)
        application.underwriter_dashboard = dashboard
        application.status = ApplicationStatus.PENDING_MANAGER_DECISION
        application.updated_at = datetime.utcnow()
        print(
            f"  Risk: {dashboard.get('overall_risk_level')} | "
            f"Recommendation: {dashboard.get('recommendation')}"
        )
        print(f"\n  Executive summary:\n  {dashboard.get('executive_summary')}")
        return application

    def _step_customer_followup(
        self,
        application: MortgageApplication,
        reason: str,
    ) -> MortgageApplication:
        print(f"[Step 7] Drafting customer communication ({reason})...")

        issues: list[str] = []
        if reason == "consistency_failure" and application.consistency_report:
            issues = [
                d.get("description", "")
                for d in application.consistency_report.get("discrepancies", [])
            ]

        comm = self.customer_comms.draft_communication(
            application=application,
            comm_reason=reason,
            specific_issues=issues or None,
        )

        application.customer_communications.append(comm)
        application.status = ApplicationStatus.CUSTOMER_FOLLOWUP_REQUIRED
        application.updated_at = datetime.utcnow()
        print(f"  Subject: {comm.get('subject_line')}")
        print(f"  SMS: {comm.get('sms_message')}")
        return application

    # ------------------------------------------------------------------ #
    # Helpers                                                              #
    # ------------------------------------------------------------------ #

    def _extract_declared_income(self, application: MortgageApplication) -> float:
        """Best-effort extraction of monthly income from authenticated documents."""
        for doc in application.authentication_results or []:
            extracted = doc.get("extracted_data", {})
            if extracted.get("monthly_income"):
                return float(extracted["monthly_income"])
            if extracted.get("monthly_gross"):
                return float(extracted["monthly_gross"])
        # Rough estimate: assume EMI should be ~40% of income, targeting 20yr tenure
        # ₹725 per lakh per month → income = loan / 100000 * 725 / 0.40
        return (application.loan.loan_amount_requested / 100_000) * 725 / 0.40


def create_sample_application() -> tuple[MortgageApplication, list[UploadedFile]]:  # noqa: E501
    """Create a sample application for demo/testing purposes."""
    from src.models.application import ApplicantDetails, LoanDetails

    application = MortgageApplication(
        application_id=str(uuid.uuid4())[:8].upper(),
        applicant=ApplicantDetails(
            full_name="Rajesh Kumar Sharma",
            date_of_birth="1985-03-15",
            aadhaar_number="123456789012",
            pan_number="ABCPS1234D",
            mobile="+91-9876543210",
            email="rajesh.sharma@email.com",
            current_address="Flat 4B, Sunrise Apartments, Koramangala, Bengaluru",
            employment_type="salaried",
            employer_name="Infosys Ltd",
            years_in_current_job=5.5,
        ),
        loan=LoanDetails(
            loan_amount_requested=8_500_000,  # ₹85 lakhs
            property_value=11_500_000,         # ₹1.15 crore
            loan_tenure_years=20,
            loan_purpose="purchase",
            property_type="apartment",
            property_address="Flat 4B, Sunrise Apartments, Koramangala, Bengaluru - 560034",
            property_state="Karnataka",
        ),
    )

    _base = Path(__file__).parent.parent / "uploads"

    def _up(fname: str) -> UploadedFile:
        p = _base / fname
        return UploadedFile(
            filename=fname,
            file_path=str(p),
            file_size_bytes=p.stat().st_size if p.exists() else None,
            mime_type="application/pdf",
        )

    uploaded_files = [
        _up("aadhaar_rajesh.pdf"),
        _up("pan_card_rajesh.pdf"),
        _up("salary_slip_jan2026.pdf"),
        _up("salary_slip_feb2026.pdf"),
        _up("salary_slip_mar2026.pdf"),
        _up("hdfc_bank_statement_6m.pdf"),
        _up("form16_fy2024.pdf"),
        _up("sale_agreement_koramangala.pdf"),
        _up("property_title_deed.pdf"),
    ]

    return application, uploaded_files
