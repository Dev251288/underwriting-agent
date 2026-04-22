# Project Summary: Mortgage Underwriting Dashboard

## Overview
Building a multi-agent retail mortgage underwriting system for the Indian market. The system includes 7 AI agents that process applications through a pipeline, with a senior underwriting manager retaining all final decision authority.

---

## What We've Built

### 1. **Multi-Agent Pipeline Architecture**
- **7 specialized agents** managed by a central orchestrator
- **Agents:** Document Collector → Document Authenticator → Consistency Checker (cost gate) → KYC Verifier → Financial Verifier → Property Verifier → Dashboard Compiler → Customer Comms
- **Key principle:** No autonomous credit decisions — all outputs feed the human manager's dashboard
- **Tech stack:** Python 3.11+, Anthropic SDK, Pydantic v2, FastAPI, Tailwind CSS

### 2. **Document Processing**
- Generated **9 synthetic but realistic PDF documents** for demo applicant (Rajesh Kumar Sharma, ₹85L loan, Koramangala property)
  - Aadhaar card, PAN card, 3 salary slips (Jan-Mar 2026)
  - 6-month HDFC bank statement
  - Form 16 (FY2024), Sale agreement, Property title deed
- **Deliberate income mismatch:** Salary slips show gross ₹1,54,062 but bank statement shows ₹1,25,000 salary credit (net after deductions)
- All documents saved to `/uploads/` directory with actual file sizes for realistic testing

### 3. **Underwriter Dashboard UI (MVP)**
- **FastAPI + Tailwind CSS (CDN)** — no build tools needed
- **Routes:**
  - `GET /` → Serve dashboard HTML
  - `GET /api/application` → Load application JSON
  - `POST /api/decision` → Record manager decision (approve/reject/refer/approve_with_conditions)
- **Dashboard sections:**
  - Header (sticky) with app ID, status badge, timestamp
  - Borrower & loan summary strip
  - AI recommendation banner (risk level + recommendation)
  - 3 verification cards (KYC, Financials, Property) with gauges and progress bars
  - Document authentication table (9 documents, auth status, confidence %)
  - Consistency report (score bar, discrepancies)
  - Key Positives vs Key Concerns
  - Conditions for Approval + Data Gaps
  - Decision panel with 4 CTAs + notes textarea
- **Data visualization:**
  - CIBIL score ring gauge (762 = green)
  - FOIR progress bar (18% = green, cap at 50%)
  - LTV progress bar with RBI 75% cap marker
  - Document auth badges (genuine=green, inconclusive=amber, suspect=red)
  - Risk level color coding (low=green, medium=amber, high=red, critical=dark red)

### 4. **Mock APIs with Realistic Data**
- **5 mock API modules** returning hardcoded test data for known PAN/Aadhaar numbers
- **ABCPS1234D (Rajesh):**
  - Aadhaar: 123456789012
  - CIBIL: 762 (excellent)
  - Monthly salary: ₹1,25,000 verified (₹1,54,062 declared = 19% mismatch)
  - Existing EMI: ₹22,500
  - Eligible loan: ₹50L (on verified income)
  - Property: Clear title, LTV 73.9% (within RBI 75% cap)

### 5. **Test Coverage**
- Unit tests for mock APIs (no API key needed)
- Agent tests with mocked Claude calls
- Full pipeline end-to-end demo: `python main.py demo` generates `output_application.json`

---

## Current Gaps Identified (To Be Fixed)

### Gap 1: Request More Information Workflow
**Problem:** "Approve with Conditions" requires verification but system has no mechanism for underwriter to re-review after customer submits docs.
**Solution:** Add "Request More Information" CTA with **fixed 7-day deadline**. Customer submits docs → underwriter re-verifies → final decision.

### Gap 2: History & Work Queue
**Problem:** Only single `output_application.json` exists. No history of decisions, no way to track actionable items.
**Solution:** Save each application to `outputs/<app_id>.json`. Build landing page with **work queue** showing:
- **Actionable items** (new applications, waiting for customer docs, pending condition verification, escalated)
- **Closed cases** (view-only: approved, rejected)
- Sorted by urgency (overdue first, then by days remaining)

### Gap 3: Credit Committee Should Be Exception-Only
**Problem:** "Refer to Credit Committee" is shown for all cases, but it should only be for genuine exceptions.
**Solution:** Show CTA only when exception thresholds met:
- CIBIL < 650
- LTV > 80%
- Risk level = critical
- Loan > ₹2Cr
- Document fraud flags

### Gap 4: Dashboard Has Duplicate Information
**Problem:** Raw numbers shown in 3 cards + repeated in concerns/conditions sections.
**Solution:** Redesign with **expandable scorecard** (4 rows: KYC, Financials, Property, Documents). Default view shows 1-line summary + status badge. Click to expand for details.

---

## Implementation Status

### Completed
✅ Multi-agent pipeline (7 agents)  
✅ Document generation (9 PDFs)  
✅ Dashboard UI MVP (basic version working)  
✅ Mock APIs with realistic data  
✅ Unit tests  
✅ End-to-end demo  

### In Progress / Planned (4 Gaps)
🔄 **Gap 1:** Request More Information workflow + 7-day deadline  
🔄 **Gap 2:** History/work queue landing page + case navigation  
🔄 **Gap 3:** Credit Committee escalation (exceptions only)  
🔄 **Gap 4:** Dashboard redesign (less duplication, expandable scorecard)  

---

## File Structure

```
underwriting-agent/
├── main.py                              # CLI: demo, serve commands
├── pyproject.toml                       # Dependencies (anthropic, pydantic, fastapi, uvicorn)
├── output_application.json              # Latest application JSON (gets updated per demo run)
├── generate_docs.py                     # Generates 9 synthetic PDFs
├── outputs/                             # (To be added) Historical applications
├── uploads/                             # 9 synthetic PDF documents
├── src/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── app.py                       # FastAPI routes (GET /, /api/application, POST /api/decision)
│   │   └── templates/
│   │       ├── index.html               # (To be added) Work queue landing page
│   │       └── dashboard.html           # Dashboard UI (to be redesigned)
│   ├── orchestrator.py                  # Pipeline orchestrator (7 agents)
│   ├── agents/                          # 7 agent implementations
│   ├── mocks/                           # 5 mock API modules
│   └── models/                          # Pydantic models
├── tests/
│   ├── test_mocks/
│   └── test_agents/
└── CLAUDE.md                            # (To be created) Guidance for future Claude sessions
```

---

## How to Run

### Demo (Pipeline)
```bash
pip install -e .
python main.py demo
# Generates output_application.json with Rajesh's case
```

### Dashboard (Web UI)
```bash
python main.py serve
# Open http://127.0.0.1:8000
# Click a CTA button, submit decision, see confirmation
```

---

## Key Design Decisions

1. **No autonomous credit decisions** — underwriter manager is always in control
2. **Cost gate at step 2b** — consistency check before calling expensive external APIs
3. **Fixed deadlines (not user input)** — 7 days for customer actions, 3 days for internal escalations
4. **Actionable vs view-only cases** — work queue distinguishes what needs action vs what's closed
5. **Mock APIs with known test data** — realistic for demo without requiring real integrations

---

## Next Steps (Pending Plan Approval)

Implement all 4 gaps:
1. Rework decision CTAs: Approve → Request More Info → Approve with Conditions → Reject → Credit Committee (conditional)
2. Change storage: single JSON → `outputs/<app_id>.json` + work queue landing page
3. Add deadline tracking: 7 days for customer, 3 days for internal
4. Redesign dashboard: scorecard, less duplication, action-required banners
5. Add history tracking: status transitions, decision audit trail

---

## Contact & Decisions

**Underwriting Manager Authority:** All final decisions rest with the human manager. AI provides analysis only.  
**Deadline Logic:** Fixed (not user input) — 7 days standard, 3 days for exceptions.  
**Exception Criteria:** CIBIL<650, LTV>80%, critical risk, loan>₹2Cr, fraud flags.  
**Work Queue Priority:** Overdue → Urgent (≤3 days) → New → Active (>3 days) → Closed.

---

**Last Updated:** 20 April 2026  
**Estimated Effort:** 4-6 hours to implement all gaps
