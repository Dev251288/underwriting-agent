# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
pip install -e ".[dev]"

# Run demo pipeline (requires ANTHROPIC_API_KEY in .env)
python main.py demo

# Run all tests (no API key needed — agents are mocked)
pytest

# Run a single test file
pytest tests/test_mocks/test_mock_apis.py -v

# Run a single test
pytest tests/test_agents/test_document_collector.py::test_catalogue_count -v
```

Copy `.env.example` to `.env` and set `ANTHROPIC_API_KEY` before running the live pipeline.

## Architecture

A sequential 7-agent pipeline managed by `MortgageUnderwritingOrchestrator` (`src/orchestrator.py`). **No agent makes autonomous credit decisions** — all outputs feed a human underwriting manager's dashboard.

### Pipeline order

```
UploadedFiles
    │
    ▼
[1] DocumentCollector       — classify & catalogue uploaded files
    │
    ▼
[2] DocumentAuthenticator   — authenticate each document in isolation (loop)
    │
    ▼
[2b] ConsistencyChecker     — cross-document checks; COST GATE
    │  go ──────────────────────────────────────────────────────┐
    │  no_go → [7] CustomerComms (document_request)             │
                                                                 ▼
                                              [3] KYCVerifier (Aadhaar + PAN)
                                                                 │
                                                                 ▼
                                              [4] FinancialVerifier (CIBIL + AA)
                                                                 │
                                                                 ▼
                                              [5] PropertyVerifier (Registry + Valuation)
                                                                 │
                                                                 ▼
                                              [6] DashboardCompiler → underwriter dashboard
                                                                 │
                                                         (status: PENDING_MANAGER_DECISION)
```

Agent 2b is the **cost gate**: it runs before any external API calls (Agents 3–5) to avoid paying for verifications on applications with fundamental document inconsistencies.

### Key design patterns

**Structured tool-forced output** — every agent calls Claude with `tool_choice={"type": "tool", "name": "..."}` forcing a single tool call. The tool's `input_schema` defines the exact output shape. See `BaseAgent._call_structured()` in `src/agents/base_agent.py`.

**Prompt caching** — every agent's system prompt is marked `cache_control: {"type": "ephemeral"}`. Since each agent type is re-used across many applications, system prompts are served from cache after the first request within the 5-minute TTL. Verify via `usage.cache_read_input_tokens` in response.

**Mock APIs** — all external calls in Agents 3, 4, 5 route through mock modules in `src/mocks/`. Known PAN numbers (`ABCPS1234D`, `BVNPV5678F`, `CDQMK9012G`) and Aadhaar numbers (`123456789012`, `234567890123`, `987654321098`) return realistic test data. Replace mock functions with real HTTP clients when integrating production APIs.

### Module map

| Path | Purpose |
|------|---------|
| `src/orchestrator.py` | Pipeline coordinator; owns application state transitions |
| `src/agents/base_agent.py` | `BaseAgent` class; `_call_structured()` wraps every Claude call |
| `src/agents/*.py` | One file per agent; each has a `run()` / `verify()` / `authenticate()` / `compile()` method |
| `src/models/application.py` | `MortgageApplication` Pydantic model; `ApplicationStatus` enum |
| `src/models/documents.py` | `Document`, `DocumentCatalogue`, `DocumentType`, `AuthenticationStatus` |
| `src/models/decisions.py` | `KYCResult`, `FinancialResult`, `PropertyResult`, `UnderwriterDashboard` |
| `src/mocks/*.py` | Mock Aadhaar, PAN, CIBIL, Account Aggregator, Land Registry APIs |
| `tests/test_mocks/` | Pure unit tests for mock APIs (no Claude calls) |
| `tests/test_agents/` | Agent tests with `@patch` on `_call_structured` (no Claude calls) |
| `main.py` | CLI entry point; `python main.py demo` runs sample application |

### Application state

`MortgageApplication` (`src/models/application.py`) is the single source of truth. The orchestrator mutates it at each step and returns the final state. Each step stores its output in a dedicated field:

| Field | Populated by |
|-------|-------------|
| `document_catalogue` | Agent 1 |
| `authentication_results` | Agent 2 |
| `consistency_report` + `cost_gate_passed` | Agent 2b |
| `kyc_result` | Agent 3 |
| `financial_result` | Agent 4 |
| `property_result` | Agent 5 |
| `underwriter_dashboard` | Agent 6 |
| `customer_communications` | Agent 7 |

### Adding a new agent

1. Create `src/agents/your_agent.py` inheriting `BaseAgent`.
2. Define a system prompt string and a `_TOOL_SCHEMA` dict.
3. Implement a public method that calls `self._call_structured(...)`.
4. Add the agent to `MortgageUnderwritingOrchestrator.__init__` and call it from a new `_step_*` method.
5. Add a new `ApplicationStatus` variant and update the relevant `_step_*` to set it.

### Indian regulatory context baked into agent prompts

- **KYC**: RBI KYC Master Directions; Aadhaar OTP e-KYC; PAN–Aadhaar linking mandate
- **Credit**: CIBIL score thresholds (650 minimum, 700+ preferred); FOIR ≤ 50% (RBI guideline)
- **Property LTV**: RBI circular — ≤90% for loans ≤₹30L; ≤80% for ₹30–75L; ≤75% above ₹75L
- **Documents**: Income Tax Form 16, ITR; RERA-registered agreements; sub-registrar records
