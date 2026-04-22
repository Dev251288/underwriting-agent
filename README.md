# IndiaBank Mortgage Underwriting Agent

An AI-powered retail mortgage underwriting system that processes home loan applications through a sequential 7-agent pipeline and surfaces findings to a human underwriting manager via a decision dashboard. The system automates document collection, authentication, KYC verification, credit assessment, and property evaluation — work that typically takes days — while keeping every credit decision in the hands of a qualified underwriter. No agent approves or rejects a loan autonomously.

---

## Agent Architecture

The pipeline is managed by `MortgageUnderwritingOrchestrator` and runs agents in fixed sequence. All agent outputs feed the underwriter dashboard; none trigger automatic decisions.

| # | Agent | Role |
|---|-------|------|
| 1 | **DocumentCollector** | Classifies and catalogues uploaded files; identifies missing required documents |
| 2 | **DocumentAuthenticator** | Authenticates each document individually — stamps, watermarks, field consistency |
| 2b | **ConsistencyChecker** | Cross-document verification and cost gate; blocks external API calls if the file has fundamental inconsistencies |
| 3 | **KYCVerifier** | Verifies identity against Aadhaar and PAN; checks name/DOB match and PAN–Aadhaar linkage |
| 4 | **FinancialVerifier** | Pulls CIBIL score, calculates FOIR, verifies income via Account Aggregator |
| 5 | **PropertyVerifier** | Confirms title clarity, LTV ratio, and valuation via sub-registrar records |
| 6 | **DashboardCompiler** | Synthesises all agent outputs into a structured underwriter dashboard with risk rating and conditions |
| 7 | **CustomerComms** | Drafts and routes customer-facing communications (document requests, conditional approvals, status updates) |

Agent 2b is a **cost gate**: if cross-document consistency fails, the pipeline routes directly to Agent 7 to request corrected documents, skipping the paid external API calls in Agents 3–5.

---

## Setup and Demo

**Prerequisites:** Python 3.11+, an Anthropic API key.

```bash
# 1. Clone and install
git clone <repo-url>
cd underwriting-agent
pip install -e ".[dev]"

# 2. Configure environment
cp .env.example .env
# Edit .env and set ANTHROPIC_API_KEY=your_key_here

# 3. Seed the work queue with five demo applications
python main.py seed

# 4. Start the underwriter dashboard
python main.py serve
# Open http://127.0.0.1:8000
```

To run the full AI pipeline against a sample application (requires API key):

```bash
python main.py demo
```

To run tests without an API key (all agent calls are mocked):

```bash
pytest
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| AI agents | [Anthropic Claude](https://docs.anthropic.com) via `anthropic` Python SDK — structured tool-forced outputs, prompt caching |
| API server | [FastAPI](https://fastapi.tiangolo.com) + [Uvicorn](https://www.uvicorn.org) |
| Dashboard | Single-page HTML + Tailwind CSS (CDN) + vanilla JS — no build step |
| Data models | [Pydantic](https://docs.pydantic.dev) v2 |
| Storage | Per-application JSON files in `outputs/` |

Every agent calls Claude with `tool_choice={"type": "tool", "name": "..."}`, forcing a single structured tool call whose `input_schema` defines the exact output shape. System prompts use `cache_control: {"type": "ephemeral"}` for prompt caching across repeated runs.

---

## External API Mocks

All third-party data calls in Agents 3, 4, and 5 route through mock modules in `src/mocks/`. The following return realistic deterministic test data:

- **UIDAI Aadhaar API** — identity and address verification
- **NSDL PAN API** — PAN validity and PAN–Aadhaar link status
- **TransUnion CIBIL** — credit score and repayment history
- **RBI Account Aggregator** — income and bank statement verification
- **State Sub-Registrar / Land Registry** — title records and encumbrance certificates

To integrate production APIs, replace the mock functions in `src/mocks/` with real HTTP clients. No other code changes are required.

---

## Indian Regulatory Context

Agent prompts and decision logic are calibrated to Indian retail mortgage policy:

- **KYC**: RBI KYC Master Directions; mandatory Aadhaar OTP e-KYC; PAN–Aadhaar linking as per Income Tax Act
- **Credit eligibility**: CIBIL score minimum 650; scores 600–649 require Credit Committee approval; below 600 is a hard reject
- **FOIR**: Fixed Obligation to Income Ratio must not exceed 50% (RBI guideline); breaches above 50% are flagged as policy exceptions
- **LTV caps (RBI circular)**: ≤90% for loans up to ₹30L · ≤80% for ₹30L–₹75L · ≤75% above ₹75L; breaches within 5pp of cap require Credit Committee; breaches beyond 5pp are hard rejects
- **Documents**: Form 16 / ITR (two years), RERA-registered sale agreements, sub-registrar title records
- **Exception escalation**: Cases with genuine policy exceptions (CIBIL band, LTV proximity, FOIR breach, or loan-to-eligibility ratio) are routed to Credit Committee with a full audit log
