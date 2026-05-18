"""
Aarna GTM Pipeline — LangGraph Workflow  (recursion-safe)
7-Stage End-to-End Supply Partner Lifecycle Automation

Key design principle: NO self-loops. Every node runs exactly once.
Loops were replaced by baking all logic into node functions.
Outreach channels are all sent in a single node pass.

Install: pip install langgraph langchain-core
Run:     python aarna_gtm_pipeline.py
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import Literal, TypedDict

# ─────────────────────────────────────────────────────────────────────────────
# STATE SCHEMA
# ─────────────────────────────────────────────────────────────────────────────

class LeadState(TypedDict):
    # ── Identity ──────────────────────────────────────────────────────────────
    lead_id: str
    company_name: str
    contact_name: str
    email: str
    phone: str
    linkedin: str
    instagram: str
    website: str
    emirate: str
    supply_category: str        # "experience_provider" | "service_provider"
    business_address: str

    # ── Entry metadata ────────────────────────────────────────────────────────
    entry_source: Literal[
        "bot_discovered", "referral", "event_card", "website_form", "social_inbound"
    ]
    intent_level: Literal["high", "medium", "low"]
    digitisation_level: Literal["digitised", "semi_digitised", "undigitised"]
    lead_score: Literal["HIGH", "MED", "LOW"]

    # ── Enrichment ────────────────────────────────────────────────────────────
    enrichment_complete: bool
    missing_fields: list[str]

    # ── Outreach ──────────────────────────────────────────────────────────────
    outreach_channels_sent: list[str]   # all channels dispatched in one pass
    partner_responded: bool
    partner_interested: bool
    partner_reply_text: str

    # ── Onboarding ────────────────────────────────────────────────────────────
    onboarding_complete: bool
    onboarding_gaps: list[str]          # sections still missing
    experience_name: str
    experience_description: str
    duration_minutes: int
    max_group_size: int
    pricing_per_person_aed: float
    operating_days: list[str]
    media_submitted: bool
    bank_details_collected: bool
    trade_licence_number: str

    # ── Agreement ─────────────────────────────────────────────────────────────
    agreement_sent: bool
    agreement_signed: bool
    agreement_platform: str             # DocuSign | HelloSign | PandaDoc

    # ── Go Live ───────────────────────────────────────────────────────────────
    listing_approved: bool
    listing_live: bool
    live_timestamp: str
    quality_failures: list[str]

    # ── Human Escalation ──────────────────────────────────────────────────────
    escalate_to_human: bool
    escalation_reason: str
    assigned_team_member: str
    escalation_summary: str

    # ── Pipeline meta ─────────────────────────────────────────────────────────
    current_stage: str
    stage_history: list[str]
    errors: list[str]
    logs: list[str]


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _log(state: LeadState, msg: str) -> list[str]:
    ts = datetime.now().strftime("%H:%M:%S")
    return state.get("logs", []) + [f"[{ts}] {msg}"]

def _push_stage(state: LeadState, name: str) -> list[str]:
    return state.get("stage_history", []) + [name]


# ─────────────────────────────────────────────────────────────────────────────
# STAGE 1 — DISCOVERY & ENTRY
# ─────────────────────────────────────────────────────────────────────────────

def stage_discovery(state: LeadState) -> LeadState:
    """Tag intent from entry source; assign lead_id."""
    source = state.get("entry_source", "bot_discovered")
    intent_map = {
        "bot_discovered": "medium",
        "referral":       "medium",
        "event_card":     "medium",
        "website_form":   "high",
        "social_inbound": "high",
    }
    intent  = intent_map.get(source, "medium")
    lead_id = state.get("lead_id") or f"AARNA-{random.randint(10000, 99999)}"

    return {
        **state,
        "lead_id":       lead_id,
        "intent_level":  intent,
        "current_stage": "discovery",
        "stage_history": _push_stage(state, "discovery"),
        "logs": _log(state,
            f"[Stage 1 – Discovery] source={source}, intent={intent}, lead_id={lead_id}"),
    }


# ─────────────────────────────────────────────────────────────────────────────
# STAGE 2 — LEAD ENRICHMENT  (runs once, fills everything it can)
# ─────────────────────────────────────────────────────────────────────────────

_REQUIRED = ["email", "phone", "contact_name", "company_name", "emirate"]

def stage_enrichment(state: LeadState) -> LeadState:
    """
    Simulates Hunter.io / Apollo / Google Maps / OCR.
    All auto-resolvable gaps are filled in one pass.
    Remaining gaps are flagged — not looped.
    """
    enriched = dict(state)
    missing  = [f for f in _REQUIRED if not state.get(f)]

    if "email" in missing:
        domain = state.get("company_name", "partner").lower().replace(" ", "")
        enriched["email"] = f"info@{domain}.com"
        missing.remove("email")

    if "phone" in missing:
        enriched["phone"] = "WhatsApp request sent — awaiting reply"
        missing.remove("phone")

    if not state.get("business_address"):
        enriched["business_address"] = "Verified via Google Maps API"

    # After auto-enrichment, whatever remains is flagged but we still proceed
    # (real system would wait for webhook; here we treat remaining gaps as non-blocking)
    complete = len(missing) == 0

    logs = _log(state,
        f"[Stage 2 – Enrichment] complete={complete}, "
        f"auto_filled={[f for f in _REQUIRED if not state.get(f) and enriched.get(f)]}, "
        f"still_missing={missing}")

    return {
        **enriched,
        "enrichment_complete": complete,
        "missing_fields":      missing,
        "current_stage":       "enrichment",
        "stage_history":       _push_stage(state, "enrichment"),
        "logs":                logs,
    }


# ─────────────────────────────────────────────────────────────────────────────
# STAGE 3 — QUALIFICATION & SCORING
# ─────────────────────────────────────────────────────────────────────────────

_UAE_EMIRATES = {
    "Dubai", "Abu Dhabi", "Sharjah", "RAK", "Ajman", "Umm Al Quwain", "Fujairah"
}

def stage_qualification(state: LeadState) -> LeadState:
    """Score: HIGH / MED / LOW — determines downstream routing."""
    intent     = state.get("intent_level", "medium")
    supply_cat = state.get("supply_category", "")
    emirate    = state.get("emirate", "")
    enriched   = state.get("enrichment_complete", False)

    is_experience = supply_cat == "experience_provider"
    is_uae        = emirate in _UAE_EMIRATES

    if intent == "high" and enriched and is_uae and is_experience:
        score = "HIGH"
    elif intent in ("medium", "high") and is_experience:
        score = "MED"
    else:
        score = "LOW"

    return {
        **state,
        "lead_score":    score,
        "current_stage": "qualification",
        "stage_history": _push_stage(state, "qualification"),
        "logs": _log(state,
            f"[Stage 3 – Qualification] score={score} | "
            f"intent={intent}, uae={is_uae}, experience={is_experience}"),
    }


# ─────────────────────────────────────────────────────────────────────────────
# STAGE 4 — MULTI-CHANNEL OUTREACH  (single-pass: sends all relevant channels)
# ─────────────────────────────────────────────────────────────────────────────

_OUTREACH_CHANNELS = [
    "voice_call",
    "email",
    "follow_up_email",
    "whatsapp",
    "linkedin",
    "instagram_dm",
    "soft_close_email",
]

_CHANNEL_SCRIPTS = {
    "voice_call":       "AI voice call → pitch Abhee + MIRAEE + Mondee (65k agents) → commission-only, zero setup → request 10-min onboarding slot.",
    "email":            "Email: 'List on Aarna — reach corporate travellers, MICE delegates, UAE tourists.' Value prop + calendar link.",
    "follow_up_email":  "Follow-up: references live UAE demand signal (GITEX / MICE season / corporate offsite).",
    "whatsapp":         "WhatsApp Business API: short direct message referencing the specific experience category.",
    "linkedin":         "LinkedIn: connection request with note on experience + Mondee distribution network.",
    "instagram_dm":     "Instagram DM: brief warm message referencing experience and Aarna UAE focus.",
    "soft_close_email": "Soft close: 'If timing is not right, here is my calendar.' Self-serve onboarding link.",
}

def stage_outreach(state: LeadState) -> LeadState:
    """
    Dispatches the complete outreach sequence in one graph pass.
    In production each channel would trigger a webhook; partner_responded/interested
    is set externally before this node runs (or pre-set in state for simulation).
    """
    logs = list(state.get("logs", []))
    sent = []

    for ch in _OUTREACH_CHANNELS:
        ts  = datetime.now().strftime("%H:%M:%S")
        logs.append(f"[{ts}] [Stage 4 – Outreach] → {ch}: {_CHANNEL_SCRIPTS[ch]}")
        sent.append(ch)

    partner_status = (
        "responded + interested"
        if state.get("partner_responded") and state.get("partner_interested")
        else "no response / not interested → nurture"
    )
    
    reply_text = ""
    if state.get("partner_responded") and state.get("partner_interested"):
        reply_text = "Yes, we are interested in reaching corporate travellers. How do we proceed with the onboarding?"
        ts_reply = datetime.now().strftime("%H:%M:%S")
        logs.append(f"[{ts_reply}] [Stage 4 – Outreach] ✉️ Partner Email Reply: '{reply_text}'")

    ts = datetime.now().strftime("%H:%M:%S")
    logs.append(f"[{ts}] [Stage 4 – Outreach] partner_status={partner_status}")

    return {
        **state,
        "outreach_channels_sent": sent,
        "partner_reply_text":     reply_text,
        "current_stage":          "outreach",
        "stage_history":          _push_stage(state, "outreach"),
        "logs":                   logs,
    }


# ─────────────────────────────────────────────────────────────────────────────
# STAGE 5 — AI ONBOARDING  (single-pass validation)
# ─────────────────────────────────────────────────────────────────────────────

_ONBOARDING_CHECKS = [
    ("business_details",       lambda s: bool(s.get("trade_licence_number"))),
    ("experience_description", lambda s: bool(s.get("experience_description"))),
    ("pricing",                lambda s: bool(s.get("pricing_per_person_aed"))),
    ("availability",           lambda s: bool(s.get("operating_days"))),
    ("media",                  lambda s: s.get("media_submitted", False)),
    ("bank_details",           lambda s: s.get("bank_details_collected", False)),
]

def stage_onboarding(state: LeadState) -> LeadState:
    """
    Validates all onboarding sections in one pass.
    Gaps are recorded as onboarding_gaps; if any exist, the downstream
    router sends to human_escalation or go_live_blocked (not back here).
    """
    gaps    = [name for name, check in _ONBOARDING_CHECKS if not check(state)]
    complete = len(gaps) == 0

    return {
        **state,
        "onboarding_complete": complete,
        "onboarding_gaps":     gaps,
        "current_stage":       "onboarding",
        "stage_history":       _push_stage(state, "onboarding"),
        "logs": _log(state,
            f"[Stage 5 – Onboarding] complete={complete}, gaps={gaps}"),
    }


# ─────────────────────────────────────────────────────────────────────────────
# STAGE 6 — AGREEMENT & CONTRACT
# ─────────────────────────────────────────────────────────────────────────────

def stage_agreement(state: LeadState) -> LeadState:
    """
    Dispatches pre-filled agreement via e-signature platform.
    agreement_signed is set externally (webhook) before this node runs;
    if False, the downstream router moves to go_live_blocked, not back here.
    """
    platform = state.get("agreement_platform") or "DocuSign"
    signed   = state.get("agreement_signed", False)
    note     = "Signed ✓" if signed else "Pending — AI will follow up in 24 h"

    return {
        **state,
        "agreement_sent":    True,
        "agreement_platform": platform,
        "current_stage":     "agreement",
        "stage_history":     _push_stage(state, "agreement"),
        "logs": _log(state,
            f"[Stage 6 – Agreement] platform={platform}, status={note}"),
    }


# ─────────────────────────────────────────────────────────────────────────────
# STAGE 7 — GO LIVE
# ─────────────────────────────────────────────────────────────────────────────

def stage_go_live(state: LeadState) -> LeadState:
    """
    Quality review → publish → connect all demand channels.
    Target: live within 24 hours of content submission.
    """
    checks = {
        "photos_ok":            state.get("media_submitted", False),
        "description_complete": bool(state.get("experience_description")),
        "pricing_confirmed":    bool(state.get("pricing_per_person_aed")),
        "agreement_signed":     state.get("agreement_signed", False),
    }
    failures = [k for k, v in checks.items() if not v]
    approved  = not failures

    if approved:
        live_ts = (datetime.now() + timedelta(hours=2)).strftime("%Y-%m-%d %H:%M")
        return {
            **state,
            "listing_approved":  True,
            "listing_live":      True,
            "live_timestamp":    live_ts,
            "quality_failures":  [],
            "current_stage":     "live",
            "stage_history":     _push_stage(state, "go_live"),
            "logs": _log(state,
                f"[Stage 7 – Go Live] APPROVED ✓ | live_at={live_ts} | "
                "Channels: Aarna marketplace · Abhee (consumer) · MIRAEE (corporate) · Mondee 65k+ B2B agents"),
        }
    else:
        return {
            **state,
            "listing_approved": False,
            "listing_live":     False,
            "quality_failures": failures,
            "current_stage":    "go_live_blocked",
            "stage_history":    _push_stage(state, "go_live_blocked"),
            "errors":           state.get("errors", []) + [f"Quality checks failed: {failures}"],
            "logs": _log(state, f"[Stage 7 – Go Live] BLOCKED | failures={failures}"),
        }


# ─────────────────────────────────────────────────────────────────────────────
# HUMAN ESCALATION  (terminal node)
# ─────────────────────────────────────────────────────────────────────────────

_TEAM = ["Gautam", "Michelle", "Shadaab", "Neerzari", "Sneden", "Nikhil"]

def stage_human_escalation(state: LeadState) -> LeadState:
    """Immediate handoff with full summary. AI does not retry after this."""
    assigned = random.choice(_TEAM)
    dig      = state.get("digitisation_level", "semi_digitised")
    dig_note = (
        "\n⚠ Digitisation note: limited online presence — pre-meeting prep recommended."
        if dig != "digitised" else ""
    )
    summary = (
        f"HANDOFF SUMMARY — {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        f"Lead        : {state.get('company_name')} ({state.get('contact_name')})\n"
        f"Lead ID     : {state.get('lead_id')}\n"
        f"Source      : {state.get('entry_source')} | Score: {state.get('lead_score')}\n"
        f"Stage       : {state.get('current_stage')}\n"
        f"Reason      : {state.get('escalation_reason')}\n"
        f"Data ready  : {[k for k in ['email','phone','experience_description','pricing_per_person_aed'] if state.get(k)]}\n"
        f"Onboarding gaps: {state.get('onboarding_gaps', [])}\n"
        f"Assigned to : {assigned}{dig_note}"
    )
    return {
        **state,
        "assigned_team_member": assigned,
        "escalation_summary":   summary,
        "current_stage":        "escalated",
        "stage_history":        _push_stage(state, "human_escalation"),
        "logs": _log(state,
            f"[Human Escalation] → {assigned} | Reason: {state.get('escalation_reason')}"),
    }


# ─────────────────────────────────────────────────────────────────────────────
# NURTURE  (terminal node)
# ─────────────────────────────────────────────────────────────────────────────

def stage_nurture(state: LeadState) -> LeadState:
    return {
        **state,
        "current_stage": "nurture",
        "stage_history": _push_stage(state, "nurture"),
        "logs": _log(state,
            "[Nurture] Lead parked. Re-qualifies when intent signal rises."),
    }


# ─────────────────────────────────────────────────────────────────────────────
# ROUTING FUNCTIONS  — NO self-loops, every branch terminates
# ─────────────────────────────────────────────────────────────────────────────

def route_post_enrichment(state: LeadState) -> str:
    if state.get("escalate_to_human"):
        return "human_escalation"
    # Even with residual gaps we proceed — they will surface at onboarding/go_live
    return "qualification"


def route_post_qualification(state: LeadState) -> str:
    if state.get("escalate_to_human"):
        return "human_escalation"
    if state.get("lead_score") == "LOW":
        return "nurture"
    return "outreach"


def route_post_outreach(state: LeadState) -> str:
    if state.get("escalate_to_human"):
        return "human_escalation"
    if state.get("partner_responded") and state.get("partner_interested"):
        return "onboarding"
    return "nurture"            # no response after full sequence → nurture


def route_post_onboarding(state: LeadState) -> str:
    if state.get("escalate_to_human"):
        return "human_escalation"
    if not state.get("onboarding_complete"):
        # Gaps found — escalate so a human can chase missing info
        return "human_escalation"
    return "agreement"


def route_post_agreement(state: LeadState) -> str:
    if state.get("escalate_to_human"):
        return "human_escalation"
    if not state.get("agreement_signed"):
        # Agreement pending — escalate rather than loop
        return "human_escalation"
    return "go_live"


def route_post_go_live(state: LeadState) -> str:
    # go_live node sets listing_live=True on approval, False on failure
    # Either way we terminate — no loops
    return "end"


# ─────────────────────────────────────────────────────────────────────────────
# GRAPH CONSTRUCTION
# ─────────────────────────────────────────────────────────────────────────────

def build_aarna_graph():
    """
    Compiles the Aarna GTM LangGraph.
    All paths terminate at END without any self-loops.
    """
    from langgraph.graph import StateGraph, END

    g = StateGraph(LeadState)

    # ── Nodes ──────────────────────────────────────────────────────────────────
    g.add_node("discovery",        stage_discovery)
    g.add_node("enrichment",       stage_enrichment)
    g.add_node("qualification",    stage_qualification)
    g.add_node("outreach",         stage_outreach)
    g.add_node("onboarding",       stage_onboarding)
    g.add_node("agreement",        stage_agreement)
    g.add_node("go_live",          stage_go_live)
    g.add_node("human_escalation", stage_human_escalation)
    g.add_node("nurture",          stage_nurture)

    # ── Entry ──────────────────────────────────────────────────────────────────
    g.set_entry_point("discovery")
    g.add_edge("discovery", "enrichment")

    # ── Conditional edges (no self-loops) ──────────────────────────────────────
    g.add_conditional_edges("enrichment", route_post_enrichment, {
        "qualification":    "qualification",
        "human_escalation": "human_escalation",
    })
    g.add_conditional_edges("qualification", route_post_qualification, {
        "outreach":         "outreach",
        "nurture":          "nurture",
        "human_escalation": "human_escalation",
    })
    g.add_conditional_edges("outreach", route_post_outreach, {
        "onboarding":       "onboarding",
        "nurture":          "nurture",
        "human_escalation": "human_escalation",
    })
    g.add_conditional_edges("onboarding", route_post_onboarding, {
        "agreement":        "agreement",
        "human_escalation": "human_escalation",
    })
    g.add_conditional_edges("agreement", route_post_agreement, {
        "go_live":          "go_live",
        "human_escalation": "human_escalation",
    })
    g.add_conditional_edges("go_live", route_post_go_live, {
        "end": END,
    })

    # ── Terminal nodes ─────────────────────────────────────────────────────────
    g.add_edge("human_escalation", END)
    g.add_edge("nurture",          END)

    return g.compile()


# ─────────────────────────────────────────────────────────────────────────────
# DEMO STATE  (exported for Streamlit UI)
# ─────────────────────────────────────────────────────────────────────────────

DEMO_STATE: LeadState = {
    "lead_id":                "",
    "company_name":           "Desert Adventure Co",
    "contact_name":           "Ahmed Al Mansouri",
    "email":                  "",
    "phone":                  "+971501234567",
    "linkedin":               "",
    "instagram":              "@desertadventuruae",
    "website":                "desertadventure.ae",
    "emirate":                "Dubai",
    "supply_category":        "experience_provider",
    "business_address":       "",
    "entry_source":           "website_form",
    "intent_level":           "high",
    "digitisation_level":     "digitised",
    "lead_score":             "HIGH",
    "enrichment_complete":    False,
    "missing_fields":         [],
    "outreach_channels_sent": [],
    "partner_responded":      True,
    "partner_interested":     True,
    "partner_reply_text":     "",
    "onboarding_complete":    False,
    "onboarding_gaps":        [],
    "experience_name":        "Dune Bashing & Camel Safari",
    "experience_description": "4-hour desert safari: dune bashing, camel riding, BBQ dinner under the stars.",
    "duration_minutes":       240,
    "max_group_size":         20,
    "pricing_per_person_aed": 350.0,
    "operating_days":         ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
    "media_submitted":        True,
    "bank_details_collected": True,
    "trade_licence_number":   "DED-2024-98765",
    "agreement_sent":         False,
    "agreement_signed":       True,
    "agreement_platform":     "DocuSign",
    "listing_approved":       False,
    "listing_live":           False,
    "live_timestamp":         "",
    "quality_failures":       [],
    "escalate_to_human":      False,
    "escalation_reason":      "",
    "assigned_team_member":   "",
    "escalation_summary":     "",
    "current_stage":          "",
    "stage_history":          [],
    "errors":                 [],
    "logs":                   [],
}


# ─────────────────────────────────────────────────────────────────────────────
# CLI RUNNER
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    graph = build_aarna_graph()
    print("\n" + "=" * 64)
    print("  AARNA GTM PIPELINE  ·  LangGraph CLI Runner")
    print("=" * 64)

    final = graph.invoke(DEMO_STATE)

    print(f"\n  Final Stage  : {final['current_stage']}")
    print(f"  Stage Path   : {' → '.join(final['stage_history'])}")
    print(f"  Lead Score   : {final['lead_score']}")
    print(f"  Listing Live : {final['listing_live']}")
    if final.get("live_timestamp"):
        print(f"  Live At      : {final['live_timestamp']}")
    if final.get("escalation_summary"):
        print(f"\n{final['escalation_summary']}")
    print("\n  ── Execution Logs ──")
    for line in final["logs"]:
        print(f"  {line}")
    print()