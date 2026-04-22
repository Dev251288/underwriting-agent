"""FastAPI application — Underwriter Decision Dashboard."""
from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI(title="Mortgage Underwriting Dashboard", version="2.0.0")

OUTPUTS_DIR   = Path(__file__).parent.parent.parent / "outputs"
TEMPLATES_DIR = Path(__file__).parent / "templates"

OUTPUTS_DIR.mkdir(exist_ok=True)

# ── Decision state machine ────────────────────────────────────────────────

INITIAL_DECISIONS: dict[str, str] = {
    "approve":                 "approved",
    "reject":                  "rejected",
    "request_info":            "customer_followup_required",
    "approve_with_conditions": "conditions_pending",
    "escalate_committee":      "committee_review",
}

DECISION_DEADLINES: dict[str, int] = {
    "request_info":            7,
    "approve_with_conditions": 7,
    "escalate_committee":      3,
}

DECISION_ACTION_TYPE: dict[str, str] = {
    "request_info":            "customer_followup",
    "approve_with_conditions": "conditions_verification",
    "escalate_committee":      "committee_review",
}

FOLLOW_UP_ACTIONS: dict[tuple[str, str], str] = {
    ("customer_followup_required", "finalise_approve"):     "approved",
    ("customer_followup_required", "finalise_reject"):      "rejected",
    ("customer_followup_required", "escalate_committee"):   "committee_review",
    ("conditions_pending",         "conditions_met"):        "approved",
    ("conditions_pending",         "finalise_reject"):       "rejected",
    ("conditions_pending",         "escalate_committee"):    "committee_review",
    ("committee_review",           "committee_approve"):     "approved",
    ("committee_review",           "committee_reject"):      "rejected",
}

CLOSED_STATUSES    = {"approved", "rejected"}
ACTIONABLE_STATUSES = {
    "pending_manager_decision",
    "customer_followup_required",
    "conditions_pending",
    "committee_review",
}


# ── Helpers ───────────────────────────────────────────────────────────────

# Keywords that classify a condition as pre-disbursement (Ops checklist), not a sanction blocker
_PREDISB_KW = [
    "noc", "encumbrance certificate", "title deed", "insurance",
    "original title", "possession letter", "ops", "society noc",
    "builder", "developer", "sub-registrar",
]


def split_conditions(conditions: list) -> tuple[list, list]:
    """Split conditions into (sanction-blocking, pre-disbursement Ops checklist).
    Handles both plain strings and {condition, options} dicts."""
    sanction, predisbursement = [], []
    for c in conditions:
        text = c["condition"] if isinstance(c, dict) else str(c)
        if any(kw in text.lower() for kw in _PREDISB_KW):
            predisbursement.append(c)
        else:
            sanction.append(c)
    return sanction, predisbursement


def compute_tier(data: dict) -> dict:
    """Return tier dict: 1=hard reject, 2=credit committee, 3=manager approval."""
    fin   = data.get("financial_result") or {}
    prop  = data.get("property_result") or {}
    loan  = data.get("loan") or {}
    auth  = data.get("authentication_results") or []
    cr    = data.get("consistency_report") or {}
    kyc   = data.get("kyc_result") or {}

    cibil       = fin.get("cibil_score") or 999
    ltv         = prop.get("ltv_ratio") or 0
    foir        = fin.get("foir") or 0
    loan_amount = loan.get("loan_amount_requested") or 0
    prop_age    = prop.get("property_age_years") or 0
    cap         = rbi_ltv_cap(loan_amount)

    tier1, tier2, tier3 = [], [], []

    # ── Tier 1: Hard reject ──────────────────────────────────────────────────
    for doc in auth:
        if doc.get("auth_status") == "rejected":
            tier1.append(f"Document fraud/tamper detected: {doc.get('doc_type', 'unknown')} — no override possible")

    if cibil < 600:
        tier1.append(f"CIBIL {cibil} below 600 — absolute minimum; no Credit Committee route available")

    if ltv > cap + 0.05:
        tier1.append(
            f"LTV {round(ltv*100,1)}% exceeds RBI cap {round(cap*100)}% by more than 5 percentage points — hard reject"
        )

    for disc in cr.get("discrepancies") or []:
        desc = disc.get("description") or ""
        m = re.search(r"(\d+)%", desc)
        field = (disc.get("field") or "").lower()
        if m and int(m.group(1)) > 25 and ("income" in field or "salary" in field or "income" in desc.lower()):
            tier1.append(f"Income mismatch {m.group(1)}% exceeds 25% — not acceptable without documentary proof")

    # ── Tier 2: Credit Committee ──────────────────────────────────────────────
    if 600 <= cibil < 650:
        tier2.append(f"CIBIL {cibil} is in 600–650 band — exception; Credit Committee approval required")

    if cap < ltv <= cap + 0.05:
        tier2.append(
            f"LTV {round(ltv*100,1)}% is within 5pp of RBI cap {round(cap*100)}% — Credit Committee with independent valuer justification"
        )

    if foir > 0.50:
        tier2.append(f"Existing FOIR {round(foir*100)}% exceeds 50% policy cap — Credit Committee review required")

    if prop_age > 25:
        tier2.append(f"Property age {prop_age} years exceeds 25-year limit — Credit Committee review required")

    eligible = fin.get("eligible_loan_amount") or 0
    if eligible > 0 and loan_amount > eligible * 1.20:
        pct_over = round((loan_amount / eligible - 1) * 100)
        tier2.append(
            f"Loan amount exceeds verified eligibility by {pct_over}% "
            f"(requested {round(loan_amount/100000)}L vs eligible {round(eligible/100000)}L on verified income) — Credit Committee required"
        )

    for disc in cr.get("discrepancies") or []:
        desc = disc.get("description") or ""
        m = re.search(r"(\d+)%", desc)
        field = (disc.get("field") or "").lower()
        if m and 15 <= int(m.group(1)) <= 25 and ("income" in field or "salary" in field or "income" in desc.lower()):
            tier2.append(f"Income mismatch {m.group(1)}% is in 15–25% range — Credit Committee with documentary explanation")

    # ── Tier 3: Manager approval with noted condition ─────────────────────────
    for doc in auth:
        if doc.get("auth_status") == "inconclusive":
            tier3.append(
                f"Inconclusive authentication on {doc.get('doc_type','document')} — "
                "legal re-vetting required before disbursement"
            )

    missing = (data.get("document_catalogue") or {}).get("missing_required") or []
    for m_doc in missing:
        tier3.append(f"Missing document: {m_doc} — must be submitted before sanction")

    if kyc.get("address_match") is False:
        tier3.append("Address mismatch on Aadhaar — acceptable if current address proof submitted; note in sanction letter")

    # Final decision
    if tier1:
        return {"tier": 1, "tier_label": "Hard Reject", "tier_color": "red",
                "can_approve": False, "can_cc": False, "reasons": tier1}
    if tier2:
        return {"tier": 2, "tier_label": "Credit Committee Required", "tier_color": "purple",
                "can_approve": False, "can_cc": True, "reasons": tier2}
    return {"tier": 3, "tier_label": "Manager Approval", "tier_color": "green",
            "can_approve": True, "can_cc": False, "reasons": tier3}


def rbi_ltv_cap(loan_amount: float) -> float:
    """RBI LTV caps: ≤₹30L → 90%, ₹30-75L → 80%, >₹75L → 75%."""
    if loan_amount <= 3_000_000:
        return 0.90
    if loan_amount <= 7_500_000:
        return 0.80
    return 0.75


def indicative_rate(cibil_score) -> str | None:
    """Indicative interest rate band from CIBIL score."""
    if cibil_score is None:
        return None
    if cibil_score >= 750:
        return "8.50% p.a."
    if cibil_score >= 700:
        return "9.00% p.a."
    if cibil_score >= 650:
        return "9.50% p.a."
    return "10.50% p.a."


def is_exception_case(data: dict) -> bool:
    """True only for Tier 2 cases (Credit Committee required). Tier 1 = hard reject, not CC."""
    tier = compute_tier(data)
    return tier["tier"] == 2


def _is_customer_action(text: str) -> bool:
    return bool(re.search(
        r"not submitted|missing|not provided|not yet|only \d+ month|one month|"
        r"mismatch|variance|discrepan|inconsist|explain|clarif|submit|provide",
        text.lower()
    ))


def _is_underwriter_action(text: str) -> bool:
    return bool(re.search(
        r"re.vet|legal|obtain|bank to verify|registry|encumbrance|title deed|"
        r"authentication inconclusive|independent valuer",
        text.lower()
    ))


# Domain categories for checklist deduplication — items in the same category are merged
_DEDUP_CATEGORIES: list[tuple[str, list[str]]] = [
    ("form16_itr",      ["form 16", "form16", "form-16", " itr ", "itr-", r"itr\)", "income tax return"]),
    ("salary_slip",     ["salary slip", "salary_slip", "payslip", "pay slip"]),
    ("specimen_sig",    ["specimen signature", "specimen sign", "signature on bank", "signature on india"]),
    ("income_variance", ["income variance", "income mismatch", "variance between", "declared.*bank", "declared.*verif",
                         "income gap", "discrepan", "mismatch.*income", "mismatch.*salary"]),
    ("legal_revet",     ["legal re", "re-vetting", "re vet", "inconclusive auth", "authentication inconclus",
                         "sale agreement.*inconclus", "property papers.*inconclus"]),
    ("encumbrance",     ["encumbrance certificate", "encumbrance cert", " ec "]),
    ("noc",             [" noc ", "society noc", "builder noc", "noc from"]),
    ("bank_statement",  ["bank statement", "bank_statement", "bank stmt"]),
]


def _item_category(text: str) -> str | None:
    t = text.lower().replace("_", " ")
    for cat, patterns in _DEDUP_CATEGORIES:
        for pat in patterns:
            if re.search(pat, t):
                return cat
    return None


def compute_cc_checklist(data: dict) -> list[dict]:
    """Build dynamic outstanding-items checklist for CC escalation gate.
    Pulls from missing docs, Customer Action Required concerns, and sanction conditions.
    Grouped condition objects (policy analysis) are excluded — only actionable items."""
    items: list[dict] = []
    seen_cats: set[str] = set()
    seen_texts: list[str] = []

    comms = data.get("customer_communications") or []
    latest_resp = (comms[-1] if comms else {}).get("customer_response_status", "pending")
    customer_responded = latest_resp == "received"

    def _status(is_uw: bool) -> str:
        if is_uw:
            return "Pending Underwriter Action"
        return "Received — Awaiting Verification" if customer_responded else "Pending Customer Submission"

    def _add(description: str, status: str, source: str) -> None:
        cat = _item_category(description)
        if cat is not None:
            if cat in seen_cats:
                return
            seen_cats.add(cat)
        else:
            # No domain category — fall back to prefix dedup
            key = description.lower().strip()[:50]
            if any(key in t or t in key for t in seen_texts):
                return
            seen_texts.append(key)
        items.append({"description": description, "status": status, "source": source})

    db    = data.get("underwriter_dashboard") or {}
    fin   = data.get("financial_result") or {}
    gross = fin.get("monthly_gross_income")
    net   = fin.get("monthly_net_income")

    # 1. Missing documents
    missing = (data.get("document_catalogue") or {}).get("missing_required") or []
    for doc in missing:
        _add(doc, _status(False), "missing_doc")

    # 2. Customer Action Required concerns — enrich income variance with exact figures
    for concern in (db.get("key_concerns") or []):
        if _is_customer_action(concern):
            if ("mismatch" in concern.lower() or "variance" in concern.lower()) and gross and net and gross > net:
                pct  = round((gross - net) / gross * 100)
                desc = (
                    f"Income variance explanation required: "
                    f"declared ₹{int(gross):,}/month vs bank-verified "
                    f"₹{int(net):,}/month ({pct}% gap)"
                )
            else:
                desc = concern
            _add(desc, _status(False), "concern")

    # 3. Sanction conditions — plain strings only (skip grouped dicts which are policy analysis)
    all_conds = db.get("conditions_for_approval") or []
    sanction_conds, _ = split_conditions(all_conds)
    for c in sanction_conds:
        if isinstance(c, dict):
            continue   # grouped condition = policy analysis, not an outstanding action item
        text  = str(c)
        is_uw = _is_underwriter_action(text)
        _add(text, _status(is_uw), "condition")

    return items


def compute_deadline_info(data: dict) -> dict | None:
    deadline_str = data.get("action_deadline")
    if not deadline_str:
        return None
    try:
        deadline = datetime.fromisoformat(deadline_str)
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)
        now = datetime.now(tz=timezone.utc)
        delta = deadline - now
        total_secs = delta.total_seconds()
        return {
            "deadline": deadline_str,
            "days_remaining": int(total_secs // 86400),
            "hours_remaining": int(total_secs // 3600),
            "is_overdue": total_secs < 0,
            "action_type": data.get("action_type", ""),
            "issued_at": data.get("action_issued_at", ""),
        }
    except (ValueError, TypeError):
        return None


def urgency_score(data: dict) -> int:
    """0=overdue, 1=urgent(≤3d), 2=new, 3=active(>3d), 4=closed."""
    status = (data.get("status") or "").lower()
    if status in CLOSED_STATUSES:
        return 4
    if status == "pending_manager_decision":
        return 2
    dl = compute_deadline_info(data)
    if dl is None:
        return 3
    if dl["is_overdue"]:
        return 0
    if dl["days_remaining"] <= 3:
        return 1
    return 3


def application_summary(data: dict) -> dict:
    applicant = data.get("applicant") or {}
    loan      = data.get("loan") or {}
    db        = data.get("underwriter_dashboard") or {}
    fin       = data.get("financial_result") or {}
    kyc       = data.get("kyc_result") or {}
    prop      = data.get("property_result") or {}
    status    = data.get("status", "unknown")
    return {
        "application_id":   data.get("application_id", "—"),
        "applicant_name":   applicant.get("full_name", "—"),
        "loan_amount":      loan.get("loan_amount_requested"),
        "loan_purpose":     loan.get("loan_purpose"),
        "status":           status,
        "risk_level":       db.get("overall_risk_level", ""),
        "cibil_score":      fin.get("cibil_score"),
        "kyc_status":       kyc.get("status"),
        "financial_status": fin.get("status"),
        "property_status":  prop.get("status"),
        "created_at":       data.get("created_at", ""),
        "updated_at":       data.get("updated_at", ""),
        "urgency_score":    urgency_score(data),
        "deadline_info":    compute_deadline_info(data),
        "is_exception":     is_exception_case(data),
    }


def _load(app_id: str) -> dict:
    path = OUTPUTS_DIR / f"{app_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Application '{app_id}' not found.")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _save(data: dict) -> None:
    app_id = data.get("application_id")
    if not app_id:
        raise HTTPException(status_code=500, detail="Application has no ID.")
    path = OUTPUTS_DIR / f"{app_id}.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _first_file() -> Path | None:
    files = sorted(OUTPUTS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


# ── Request models ────────────────────────────────────────────────────────

class DecisionRequest(BaseModel):
    decision: str
    notes: Optional[str] = None
    app_id: Optional[str] = None


class ActionRequest(BaseModel):
    action: str
    notes: Optional[str] = None
    checklist_state: Optional[list] = None   # passed by UI when escalating to CC


# ── Routes ────────────────────────────────────────────────────────────────

@app.get("/")
async def serve_index() -> FileResponse:
    tmpl = TEMPLATES_DIR / "index.html"
    if not tmpl.exists():
        raise HTTPException(status_code=500, detail="index.html not found.")
    return FileResponse(path=tmpl, media_type="text/html", headers={"Cache-Control": "no-store"})


@app.get("/case")
async def serve_case() -> FileResponse:
    tmpl = TEMPLATES_DIR / "dashboard.html"
    if not tmpl.exists():
        raise HTTPException(status_code=500, detail="dashboard.html not found.")
    return FileResponse(path=tmpl, media_type="text/html", headers={"Cache-Control": "no-store"})


@app.get("/api/applications")
async def list_applications() -> list[dict]:
    summaries: list[dict] = []
    for f in OUTPUTS_DIR.glob("*.json"):
        try:
            with f.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
            summaries.append(application_summary(data))
        except Exception:
            pass
    summaries.sort(key=lambda x: (
        x["urgency_score"],
        -(datetime.fromisoformat(
            (x.get("updated_at") or "2000-01-01T00:00:00").replace("Z", "+00:00")
        ).timestamp()),
    ))
    return summaries


def _enrich(data: dict) -> dict:
    """Inject computed fields used by the dashboard template."""
    loan_amount = (data.get("loan") or {}).get("loan_amount_requested") or 0
    cibil  = (data.get("financial_result") or {}).get("cibil_score")
    tier   = compute_tier(data)
    all_conds = (data.get("underwriter_dashboard") or {}).get("conditions_for_approval") or []
    sanction_conds, predisb_conds = split_conditions(all_conds)

    # Deadline overdue flag (Step 2b trigger for CC button)
    deadline_iso = data.get("action_deadline")
    deadline_overdue = False
    if deadline_iso:
        try:
            dl = datetime.fromisoformat(deadline_iso.replace("Z", ""))
            if dl.tzinfo is None:
                dl = dl.replace(tzinfo=timezone.utc)
            deadline_overdue = dl < datetime.now(tz=timezone.utc)
        except (ValueError, TypeError):
            pass

    is_exc = is_exception_case(data)
    data["_exception_case"]              = is_exc
    data["_deadline_info"]               = compute_deadline_info(data)
    data["_indicative_rate"]             = indicative_rate(cibil)
    data["_rbi_ltv_cap"]                 = rbi_ltv_cap(loan_amount)
    data["_tier"]                        = tier
    data["_sanction_conditions"]         = sanction_conds
    data["_predisbursement_conditions"]  = predisb_conds
    data["_cibil_mandatory_cc"]          = bool(cibil and 600 <= cibil <= 649)
    data["_deadline_overdue"]            = deadline_overdue
    data["_cc_checklist"]                = compute_cc_checklist(data) if is_exc else []
    return data


@app.get("/api/application/{app_id}")
async def get_application_by_id(app_id: str) -> dict:
    return _enrich(_load(app_id))


@app.get("/api/application")
async def get_application_fallback() -> dict:
    f = _first_file()
    if not f:
        raise HTTPException(
            status_code=404,
            detail="No applications found. Run 'python main.py demo' first.",
        )
    with f.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    return _enrich(data)


@app.post("/api/decision")
async def submit_decision(body: DecisionRequest) -> dict:
    if body.decision not in INITIAL_DECISIONS:
        raise HTTPException(
            status_code=422,
            detail=f"decision must be one of: {sorted(INITIAL_DECISIONS.keys())}",
        )

    if body.app_id:
        data = _load(body.app_id)
    else:
        f = _first_file()
        if not f:
            raise HTTPException(status_code=404, detail="No applications found.")
        with f.open("r", encoding="utf-8") as fh:
            data = json.load(fh)

    if data.get("status") != "pending_manager_decision":
        raise HTTPException(
            status_code=409,
            detail=f"Application is in status '{data.get('status')}' and cannot accept an initial decision.",
        )

    # Auto-route plain "approve" to "approve_with_conditions" when sanction conditions exist
    if body.decision == "approve":
        all_conds = (data.get("underwriter_dashboard") or {}).get("conditions_for_approval") or []
        sanction_conds, _ = split_conditions(all_conds)
        if sanction_conds:
            body.decision = "approve_with_conditions"

    if body.decision == "escalate_committee" and not is_exception_case(data):
        raise HTTPException(
            status_code=422,
            detail=(
                "Credit Committee escalation is only allowed for exception cases "
                "(CIBIL<650, LTV>80%, critical risk, loan>Rs.2Cr, or fraud/suspect documents)."
            ),
        )

    now     = datetime.now(tz=timezone.utc)
    now_iso = now.isoformat()
    new_status = INITIAL_DECISIONS[body.decision]

    data.update({
        "status":               new_status,
        "updated_at":           now_iso,
        "manager_decision":     body.decision,
        "manager_notes":        body.notes or "",
        "manager_decision_at":  now_iso,
    })

    deadline_days = DECISION_DEADLINES.get(body.decision)
    if deadline_days:
        data["action_deadline"]  = (now + timedelta(days=deadline_days)).isoformat()
        data["action_issued_at"] = now_iso
        data["action_type"]      = DECISION_ACTION_TYPE[body.decision]

    _save(data)
    return {
        "success":         True,
        "application_id":  data.get("application_id"),
        "decision":        body.decision,
        "status":          new_status,
        "decided_at":      now_iso,
        "action_deadline": data.get("action_deadline"),
    }


@app.post("/api/orchestrate/communicate/{app_id}")
async def orchestrate_communication(app_id: str) -> dict:
    """Orchestrator routes to Agent 7 (CustomerComms). Mocked for demo — no API key needed.
    Email and SMS content is fully dynamic — pulled from this application's specific data."""
    data = _load(app_id)
    status = data.get("status", "")
    valid = {"customer_followup_required", "conditions_pending", "committee_review"}
    if status not in valid:
        raise HTTPException(status_code=422, detail=f"Cannot send communication for status: {status}")

    applicant     = data.get("applicant") or {}
    name          = applicant.get("full_name", "Applicant")
    first_name    = name.split()[0] if name else "Applicant"
    app_id_str    = data.get("application_id", "")
    missing       = (data.get("document_catalogue") or {}).get("missing_required") or []
    discrepancies = (data.get("consistency_report") or {}).get("discrepancies") or []
    all_conds     = (data.get("underwriter_dashboard") or {}).get("conditions_for_approval") or []
    fin           = data.get("financial_result") or {}
    sanction_conds, _ = split_conditions(all_conds)

    # Extract plain text from conditions (handle both str and {condition, options} dict)
    def _cond_text(c) -> str:
        return c["condition"] if isinstance(c, dict) else str(c)

    sanction_texts = [_cond_text(c) for c in sanction_conds]

    now           = datetime.now(tz=timezone.utc)
    now_iso       = now.isoformat()
    deadline_date = (now + timedelta(days=7)).strftime("%d %b %Y")

    comm_type = {
        "customer_followup_required": "document_request",
        "conditions_pending":         "approval_conditional",
        "committee_review":           "status_update",
    }.get(status, "status_update")

    action_items: list[str] = []
    email_sections: list[str] = []

    if comm_type == "document_request":
        subject = f"Action Required: Outstanding Items — Home Loan {app_id_str}"

        # 1. Missing documents — list each one by name
        if missing:
            email_sections.append(
                "The following required documents have not been received:\n" +
                "\n".join(f"  {i+1}. {m}" for i, m in enumerate(missing))
            )
            action_items.extend([f"Submit: {m}" for m in missing])

        # 2. Income variance — quote exact figures when available
        income_disc = next(
            (d for d in discrepancies if "income" in (d.get("field") or "").lower()), None
        )
        gross  = fin.get("monthly_gross_income")
        net    = fin.get("monthly_net_income")
        if income_disc:
            if gross and net and gross > net * 1.05:
                variance_pct = round((gross - net) / gross * 100)
                variance_note = (
                    f"Income variance requires written explanation:\n"
                    f"  Declared income: ₹{int(gross):,}/month\n"
                    f"  Bank-verified credits: ₹{int(net):,}/month\n"
                    f"  Variance: {variance_pct}% — please provide CA-certified income proof or a written explanation."
                )
                action_items.append(
                    f"Explain income variance: declared ₹{int(gross):,}/month vs bank-verified ₹{int(net):,}/month ({variance_pct}%)"
                )
            else:
                variance_note = (
                    f"Income discrepancy requiring explanation:\n"
                    f"  {income_disc.get('description', 'Income mismatch noted — provide documentary proof.')}"
                )
                action_items.append("Provide documentary explanation for income discrepancy")
            email_sections.append(variance_note)

        # 3. Sanction conditions not covered by missing docs or income variance
        remaining_conds = [
            t for t in sanction_texts
            if not any(m.lower() in t.lower() for m in missing)
            and "income" not in t.lower() and "salary" not in t.lower() and "variance" not in t.lower()
        ]
        if remaining_conds and (not missing or not income_disc):
            email_sections.append(
                "The following outstanding conditions require resolution:\n" +
                "\n".join(f"  {i+1}. {c}" for i, c in enumerate(remaining_conds[:4]))
            )
            action_items.extend(remaining_conds[:4])

        if not action_items:
            action_items = ["Submit all requested documents and information as detailed in this letter"]

        sms_summary = action_items[0][:70] + ("…" if len(action_items[0]) > 70 else "")
        sms = (
            f"IndiaBank: Loan {app_id_str} — action required by {deadline_date}. "
            f"{sms_summary}. Reply or call 1800-209-4006."
        )[:160]

        body_detail = "\n\n".join(email_sections) if email_sections else (
            "Please submit all outstanding documents and information as requested by the Home Loans team."
        )

        email = (
            f"Dear {first_name},\n\n"
            f"Re: Home Loan Application — {app_id_str}\n\n"
            f"Our underwriting team has reviewed your application and the following items "
            f"remain outstanding before we can proceed:\n\n"
            f"{body_detail}\n\n"
            f"Please respond by {deadline_date}. If we do not receive a response by this date, "
            f"your application will be reviewed on the information currently available, "
            f"which may result in a revised loan amount or rejection.\n\n"
            f"To submit documents, visit your nearest IndiaBank branch or upload via the customer portal.\n"
            f"For queries: 1800-209-4006 (Mon–Sat, 9 AM–6 PM)\n\n"
            f"Regards,\nHome Loans Team | IndiaBank"
        )

    elif comm_type == "approval_conditional":
        subject = f"Conditional Sanction — Home Loan {app_id_str}"
        conds_display = sanction_texts[:5] if sanction_texts else [_cond_text(c) for c in all_conds[:5]]

        sms = (
            f"IndiaBank: Loan {app_id_str} conditionally sanctioned. "
            f"{len(conds_display)} condition(s) to fulfil before disbursement. "
            f"Deadline: {deadline_date}. Call 1800-209-4006."
        )[:160]

        email = (
            f"Dear {first_name},\n\n"
            f"Re: Home Loan Application — {app_id_str}\n\n"
            f"We are pleased to inform you that your Home Loan application has received a conditional sanction.\n\n"
            f"The following conditions must be fulfilled before disbursement can proceed:\n\n" +
            "\n".join(f"  {i+1}. {c}" for i, c in enumerate(conds_display)) +
            f"\n\nOur Ops team will contact you separately to complete the pre-disbursement checklist "
            f"(NOC, Encumbrance Certificate, insurance assignment, etc.).\n\n"
            f"Please confirm acceptance of sanction terms by {deadline_date}.\n\n"
            f"For queries: 1800-209-4006 (Mon–Sat, 9 AM–6 PM)\n\n"
            f"Regards,\nHome Loans Team | IndiaBank"
        )
        action_items = conds_display[:3] or ["Fulfil stated sanction conditions before disbursement"]

    else:  # committee_review / status_update
        subject = f"Status Update — Home Loan Application {app_id_str}"
        sms = (
            f"IndiaBank: Home Loan {app_id_str} is under Credit Committee review. "
            f"Decision expected within 3 working days. Call 1800-209-4006."
        )[:160]
        email = (
            f"Dear {first_name},\n\n"
            f"Re: Home Loan Application — {app_id_str}\n\n"
            f"Your application has been referred to our Credit Committee for review of an exception to standard policy. "
            f"You will receive a decision within 3 working days.\n\n"
            f"No action is required from you at this time. We will contact you once a decision is reached.\n\n"
            f"For queries: 1800-209-4006 (Mon–Sat, 9 AM–6 PM)\n\n"
            f"Regards,\nHome Loans Team | IndiaBank"
        )
        action_items = ["Await Credit Committee decision — expected within 3 working days"]

    comm_entry = {
        "comm_type":                comm_type,
        "subject_line":             subject,
        "sms_message":              sms,
        "email_body":               email,
        "action_items":             action_items,
        "deadline_days":            7 if comm_type == "document_request" else None,
        "sent_at":                  now_iso,
        "sent_via":                 ["sms", "email"],
        "customer_response_status": "pending",
        "orchestrated":             True,
        "routed_via":               "MortgageUnderwritingOrchestrator → CustomerCommsAgent",
    }

    comms = list(data.get("customer_communications") or [])
    comms.append(comm_entry)
    data["customer_communications"] = comms
    data["action_issued_at"] = now_iso
    data["updated_at"]       = now_iso
    _save(data)
    return {"success": True, "communication": comm_entry}


@app.post("/api/communicate/{app_id}")
async def draft_communication(app_id: str) -> dict:
    """Run Agent 7 (CustomerComms) to draft and save a customer communication."""
    import os
    data = _load(app_id)
    status = data.get("status", "")

    # Map application status to comm reason
    reason_map = {
        "customer_followup_required": "document_request",
        "conditions_pending":         "approval_conditional",
        "committee_review":           "status_update",
    }
    if status not in reason_map:
        raise HTTPException(
            status_code=422,
            detail=f"Communication can only be drafted for active follow-up states. Current: {status}",
        )

    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise HTTPException(
            status_code=503,
            detail="ANTHROPIC_API_KEY not set. Add it to .env and restart the server.",
        )

    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from src.agents.customer_comms import CustomerCommsAgent
        from src.models.application import MortgageApplication

        app_model = MortgageApplication(**{
            k: v for k, v in data.items()
            if not k.startswith("_")
        })
        agent  = CustomerCommsAgent()
        result = agent.draft_communication(
            application=app_model,
            comm_reason=reason_map[status],
            specific_issues=data.get("underwriter_dashboard", {}).get("data_gaps"),
            specific_conditions=data.get("underwriter_dashboard", {}).get("conditions_for_approval"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {e}")

    now_iso = datetime.now(tz=timezone.utc).isoformat()
    comm_entry = {**result, "sent_at": now_iso, "agent": "CustomerComms"}

    comms = data.get("customer_communications") or []
    comms.append(comm_entry)
    data["customer_communications"] = comms
    data["action_issued_at"] = now_iso
    data["updated_at"]       = now_iso
    _save(data)

    return {"success": True, "communication": comm_entry}


@app.post("/api/action/{app_id}")
async def submit_action(app_id: str, body: ActionRequest) -> dict:
    data = _load(app_id)
    current_status = data.get("status", "")
    key = (current_status, body.action)

    if key not in FOLLOW_UP_ACTIONS:
        valid = [a for (s, a) in FOLLOW_UP_ACTIONS if s == current_status]
        raise HTTPException(
            status_code=422,
            detail=f"Action '{body.action}' not valid for status '{current_status}'. Valid: {valid}",
        )

    if body.action == "escalate_committee" and not is_exception_case(data):
        raise HTTPException(
            status_code=422,
            detail="Credit Committee escalation requires: CIBIL<650, LTV breach, critical risk, loan>₹2Cr, or fraud/suspect documents.",
        )

    now_iso    = datetime.now(tz=timezone.utc).isoformat()
    new_status = FOLLOW_UP_ACTIONS[key]

    data.update({
        "status":           new_status,
        "updated_at":       now_iso,
        "follow_up_action": body.action,
        "follow_up_notes":  body.notes or "",
        "follow_up_at":     now_iso,
    })
    data.pop("action_deadline", None)
    data.pop("action_type", None)

    # Step 4: Log CC escalation audit for compliance
    if body.action == "escalate_committee":
        checklist = body.checklist_state or []
        pending   = [i for i in checklist if "Pending" in (i.get("status") or "")]
        received  = [i for i in checklist if "Received" in (i.get("status") or "")]
        data["cc_escalation_audit"] = {
            "escalated_at":           now_iso,
            "escalated_by":           "Ananya Krishnan",
            "acknowledged":           True,
            "total_items":            len(checklist),
            "pending_count":          len(pending),
            "received_count":         len(received),
            "pending_items":          [i.get("description") for i in pending],
            "received_items":         [i.get("description") for i in received],
            "checklist_at_escalation": checklist,
        }

    _save(data)
    return {
        "success":        True,
        "application_id": app_id,
        "action":         body.action,
        "status":         new_status,
        "action_at":      now_iso,
    }
