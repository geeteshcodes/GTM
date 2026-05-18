"""
Aarna GTM Pipeline — Streamlit UI
Run: streamlit run aarna_streamlit_ui.py

Requires: pip install streamlit langgraph langchain-core
Both files must be in the same directory.
"""

import streamlit as st

from aarna_gtm_pipeline import DEMO_STATE, LeadState, build_aarna_graph

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Aarna GTM Pipeline",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

[data-testid="stSidebar"] { background: #0f1117; border-right: 1px solid #1e2030; }
[data-testid="stSidebar"] * { color: #c8cce0 !important; }
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 { color: #ffffff !important; }

.main { background: #0b0d14; }
.block-container { padding: 2rem 2rem 4rem; max-width: 1200px; }

/* ── Pipeline diagram ── */
.pip-row {
    display: flex; align-items: center; gap: 0;
    flex-wrap: nowrap; overflow-x: auto; padding: 1rem 0;
}
.pip-node {
    flex-shrink: 0; width: 105px; text-align: center;
    padding: 0.55rem 0.3rem; border-radius: 8px;
    border: 1px solid #1e2235; background: #13151f;
    font-size: 0.7rem; color: #717891; font-weight: 500;
    white-space: nowrap;
}
.pip-node.visited   { background: #22c55e1a; color: #4ade80; border-color: #22c55e44; }
.pip-node.current   { background: #4f6ef7;   color: #fff;    border-color: #4f6ef7; font-weight: 700; }
.pip-node.t-nurture { background: #f59e0b1a; color: #fbbf24; border-color: #f59e0b44; }
.pip-node.t-escalated { background: #a855f71a; color: #c084fc; border-color: #a855f744; }
.pip-node.t-live    { background: #22c55e1a; color: #4ade80; border-color: #22c55e66; font-weight:700; }
.pip-node.t-blocked { background: #ef44441a; color: #f87171; border-color: #ef444444; }
.pip-arrow { color: #2d3148; font-size: 1rem; padding: 0 2px; flex-shrink: 0; }

/* ── Stage cards ── */
.stage-card {
    background: #13151f; border: 1px solid #1e2235;
    border-radius: 12px; padding: 1.1rem 1.3rem; margin-bottom: 0.85rem;
}
.stage-card.active   { border-color: #4f6ef7; box-shadow: 0 0 16px #4f6ef722; }
.stage-card.done     { border-color: #22c55e44; }
.stage-card.warn     { border-color: #f59e0b44; }
.stage-card.error    { border-color: #ef444466; }
.stage-card.escalated { border-color: #a855f766; }
.stage-label { font-size: 0.65rem; letter-spacing: 0.12em; text-transform: uppercase; color: #6b7280; margin-bottom: 0.25rem; }
.stage-title { font-size: 1rem; font-weight: 600; color: #e4e8f5; margin-bottom: 0.4rem; }
.stage-desc  { font-size: 0.8rem; color: #717891; line-height: 1.55; }

/* ── Metric tiles ── */
.metric-tile { background: #13151f; border: 1px solid #1e2235; border-radius: 10px; padding: 1rem; text-align: center; }
.metric-value { font-size: 1.6rem; font-weight: 700; color: #4f6ef7; line-height: 1; }
.metric-label { font-size: 0.68rem; color: #6b7280; margin-top: 4px; text-transform: uppercase; letter-spacing: 0.08em; }

/* ── Log panel ── */
.log-wrap { max-height: 360px; overflow-y: auto; background: #0b0d14; border: 1px solid #1e2235; border-radius: 8px; padding: 0.7rem; }
.log-entry { font-family: 'DM Mono', monospace; font-size: 0.72rem; color: #6b7a99; padding: 2px 0; border-bottom: 1px solid #13151f; }

/* ── General ── */
h1,h2,h3 { color: #e4e8f5 !important; }
p,li { color: #9aa3ba; }
hr { border-color: #1e2235 !important; }
.stButton > button {
    background: linear-gradient(135deg, #4f6ef7, #7c3aed) !important;
    color: white !important; border: none !important;
    border-radius: 8px !important; font-weight: 600 !important;
    padding: 0.5rem 1.5rem !important;
}
.stButton > button:hover { opacity: 0.9 !important; }
.stSelectbox label,.stTextInput label,.stCheckbox label { color: #9aa3ba !important; font-size: 0.82rem !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────────────────────────────────────

if "lead_state" not in st.session_state:
    st.session_state.lead_state = None

if "graph" not in st.session_state:
    st.session_state.graph = None
    st.session_state.graph_error = None

# Always attempt to build graph if not already built
if st.session_state.graph is None and st.session_state.graph_error is None:
    try:
        st.session_state.graph = build_aarna_graph()
    except Exception as e:
        st.session_state.graph_error = str(e)

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR — Lead Input Form
# ─────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🌍 Aarna GTM Pipeline")
    st.markdown("---")
    st.markdown("### Lead Details")

    company_name = st.text_input("Company Name",  value="Desert Adventure Co")
    contact_name = st.text_input("Contact Name",  value="Ahmed Al Mansouri")
    phone        = st.text_input("Phone",         value="+971501234567")
    email        = st.text_input("Email (leave blank to test enrichment)", value="")

    emirate = st.selectbox("Emirate", [
        "Dubai", "Abu Dhabi", "Sharjah", "RAK",
        "Ajman", "Umm Al Quwain", "Fujairah", "Outside UAE"
    ])
    supply_cat = st.selectbox("Supply Category", [
        "experience_provider", "service_provider"
    ])
    digitisation = st.selectbox("Digitisation Level", [
        "digitised", "semi_digitised", "undigitised"
    ])
    entry_source = st.selectbox("Entry Source", [
        "website_form", "social_inbound", "referral", "event_card", "bot_discovered"
    ])

    st.markdown("---")
    st.markdown("### Scenario Controls")

    partner_responds  = st.checkbox("Partner Responds & Is Interested", value=True)
    onboarding_ready  = st.checkbox("All Onboarding Data Provided",     value=True)
    agreement_signed  = st.checkbox("Agreement Signed",                  value=True)
    media_ok          = st.checkbox("Media Submitted",                   value=True)

    escalate_human    = st.checkbox("Trigger Human Escalation",          value=False)
    esc_reason = ""
    if escalate_human:
        esc_reason = st.text_input("Escalation Reason",
            value="Partner wants to negotiate commission rate")

    st.markdown("---")
    run_btn = st.button("▶  Run Pipeline", use_container_width=True)

def render_dashboard(s):
    import streamlit as st
    # ─────────────────────────────────────────────────────────────────────────────
    # HEADER
    # ─────────────────────────────────────────────────────────────────────────────

    st.markdown("""
    <div style="display:flex;align-items:center;gap:1rem;margin-bottom:1.5rem">
      <div style="width:48px;height:48px;background:linear-gradient(135deg,#4f6ef7,#7c3aed);
                  border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:1.4rem">🌍</div>
      <div>
        <div style="font-size:1.5rem;font-weight:700;color:#e4e8f5">Aarna GTM Pipeline</div>
        <div style="font-size:0.78rem;color:#6b7280">7-Stage Supply Partner Lifecycle · LangGraph · No-loop architecture</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ─────────────────────────────────────────────────────────────────────────────
    # PIPELINE DIAGRAM
    # ─────────────────────────────────────────────────────────────────────────────

    MAIN_STAGES = [
        ("discovery",     "1 Discovery"),
        ("enrichment",    "2 Enrichment"),
        ("qualification", "3 Qualify"),
        ("outreach",      "4 Outreach"),
        ("onboarding",    "5 Onboarding"),
        ("agreement",     "6 Agreement"),
        ("go_live",       "7 Go Live"),
    ]
    TERMINAL_MAP = {
        "nurture":          ("t-nurture",   "Nurture"),
        "escalated":        ("t-escalated", "Escalated"),
        "live":             ("t-live",      "✓ Live"),
        "go_live_blocked":  ("t-blocked",   "⚠ Blocked"),
    }

    s        = st.session_state.lead_state
    visited  = set(s["stage_history"]) if s else set()
    current  = s["current_stage"]      if s else ""

    nodes_html = ""
    for key, label in MAIN_STAGES:
        cls = "visited" if key in visited else ""
        if current == key:
            cls = "current"
        nodes_html += f'<div class="pip-node {cls}">{label}</div><span class="pip-arrow">→</span>'

    # Terminal node
    if current in TERMINAL_MAP:
        tcls, tlabel = TERMINAL_MAP[current]
        nodes_html += f'<div class="pip-node {tcls}">{tlabel}</div>'

    st.markdown(f'<div class="pip-row">{nodes_html}</div>', unsafe_allow_html=True)
    st.markdown("---")

    # ─────────────────────────────────────────────────────────────────────────────
    # EMPTY STATE
    # ─────────────────────────────────────────────────────────────────────────────

    if not s:
        st.markdown("""
    <div class="stage-card">
      <div class="stage-label">Getting started</div>
      <div class="stage-title">Configure a lead in the sidebar → click ▶ Run Pipeline</div>
      <div class="stage-desc">
        The workflow executes all 7 stages in a single pass with no recursion loops.<br><br>
        <strong>Paths to test:</strong><br>
        • Default settings → full happy path → listing goes live<br>
        • Uncheck "Partner Responds" → routes to Nurture after Outreach<br>
        • Set Supply Category to service_provider + low intent → routes to Nurture after Qualify<br>
        • Check "Trigger Human Escalation" → immediate handoff with summary<br>
        • Uncheck "Agreement Signed" → escalates after Agreement stage<br>
        • Uncheck "All Onboarding Data" → escalates after Onboarding stage
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ─────────────────────────────────────────────────────────────────────────────
    # RESULTS
    # ─────────────────────────────────────────────────────────────────────────────

    else:
        stage  = s.get("current_stage", "—")
        score  = s.get("lead_score", "—")
        n_ch   = len(s.get("outreach_channels_sent", []))
        status = (
            "✓ Live"    if s.get("listing_live")          else
            "⚠ Blocked" if stage == "go_live_blocked"      else
            "Escalated" if stage == "escalated"            else
            "Nurture"   if stage == "nurture"              else
            "—"
        )

        # ── Metrics ──────────────────────────────────────────────────────────────
        m1, m2, m3, m4 = st.columns(4)
        for col, val, label in [
            (m1, score,                              "Lead Score"),
            (m2, stage.replace("_"," ").title(),     "Final Stage"),
            (m3, str(n_ch),                          "Channels Sent"),
            (m4, status,                             "Listing Status"),
        ]:
            with col:
                st.markdown(
                    f'<div class="metric-tile">'
                    f'<div class="metric-value">{val}</div>'
                    f'<div class="metric-label">{label}</div>'
                    f'</div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        col_l, col_r = st.columns([3, 2])

        # ── Left: Stage cards ─────────────────────────────────────────────────────
        with col_l:
            st.markdown("### Stage Results")

            def card(key, title, desc, cls="done"):
                if key not in visited and current != key:
                    return
                effective = "active" if current == key else cls
                st.markdown(
                    f'<div class="stage-card {effective}">'
                    f'<div class="stage-label">Stage</div>'
                    f'<div class="stage-title">{title}</div>'
                    f'<div class="stage-desc">{desc}</div>'
                    f'</div>', unsafe_allow_html=True)

            card("discovery", "1 · Discovery & Entry",
                 f"Lead ID: <strong>{s.get('lead_id','—')}</strong> &nbsp;·&nbsp; "
                 f"Source: {s.get('entry_source','—')} &nbsp;·&nbsp; "
                 f"Intent: {s.get('intent_level','—')}")

            card("enrichment", "2 · Lead Enrichment",
                 f"Complete: {'✓' if s.get('enrichment_complete') else '✗'} &nbsp;·&nbsp; "
                 f"Email: {s.get('email','—')} &nbsp;·&nbsp; "
                 f"Still missing: {s.get('missing_fields') or 'none'}")

            if "qualification" in visited:
                score_badge_colour = {"HIGH":"#4ade80","MED":"#fb923c","LOW":"#f87171"}.get(score,"#fff")
                card("qualification", "3 · Qualification & Scoring",
                     f"Score: <strong style='color:{score_badge_colour}'>{score}</strong> &nbsp;·&nbsp; "
                     f"Category: {s.get('supply_category','—')} &nbsp;·&nbsp; "
                     f"Digitisation: {s.get('digitisation_level','—')}")

            if "outreach" in visited:
                channels  = s.get("outreach_channels_sent", [])
                responded = (
                    "✓ responded + interested"
                    if s.get("partner_responded") and s.get("partner_interested")
                    else "✗ no response / not interested"
                )

                reply_html = ""
                if s.get("partner_reply_text"):
                    reply_html = f"<br><br><span style='color:#a8b3cf'>✉️ <i>\"{s.get('partner_reply_text')}\"</i></span>"

                card("outreach", "4 · Multi-Channel Outreach",
                     f"Channels dispatched: {len(channels)} "
                     f"({', '.join(channels[:3])}{'…' if len(channels)>3 else ''}) &nbsp;·&nbsp; "
                     f"Partner: {responded}{reply_html}")

            if "onboarding" in visited:
                gaps = s.get("onboarding_gaps", [])
                card("onboarding", "5 · AI Onboarding Conversation",
                     f"Complete: {'✓' if s.get('onboarding_complete') else '✗'} &nbsp;·&nbsp; "
                     f"{'Gaps: ' + str(gaps) if gaps else 'All sections collected'} &nbsp;·&nbsp; "
                     f"Price: AED {s.get('pricing_per_person_aed',0):.0f}/person &nbsp;·&nbsp; "
                     f"Media: {'✓' if s.get('media_submitted') else '✗'}",
                     cls="warn" if gaps else "done")

            if "agreement" in visited:
                card("agreement", "6 · Agreement & Contract",
                     f"Platform: {s.get('agreement_platform','—')} &nbsp;·&nbsp; "
                     f"Signed: {'✓' if s.get('agreement_signed') else '✗ — pending, escalated to human'}",
                     cls="done" if s.get("agreement_signed") else "warn")

            if "go_live" in visited or stage in ("live", "go_live_blocked"):
                if s.get("listing_live"):
                    card("go_live", "7 · Go Live",
                         f"✓ Published at <strong>{s.get('live_timestamp','—')}</strong><br>"
                         "Connected: Aarna marketplace · Abhee (consumer) · MIRAEE (corporate) · Mondee 65k+ B2B agents",
                         cls="done")
                else:
                    failures = s.get("quality_failures", [])
                    card("go_live", "7 · Go Live — Blocked",
                         f"⚠ Quality checks failed: {failures}<br>Feedback sent to partner.",
                         cls="error")

            if stage == "nurture":
                st.markdown("""
    <div class="stage-card warn">
      <div class="stage-label">Terminal · Nurture</div>
      <div class="stage-title">Lead Parked in Nurture Sequence</div>
      <div class="stage-desc">Will re-qualify automatically when intent signal increases.</div>
    </div>""", unsafe_allow_html=True)

            if stage == "escalated":
                st.markdown(f"""
    <div class="stage-card escalated">
      <div class="stage-label">Terminal · Human Escalation</div>
      <div class="stage-title">Assigned to {s.get('assigned_team_member','—')}</div>
      <div class="stage-desc">Reason: {s.get('escalation_reason','—')}</div>
    </div>""", unsafe_allow_html=True)

        # ── Right: Meta + Logs ────────────────────────────────────────────────────
        with col_r:
            st.markdown("### Stage Path")
            path      = s.get("stage_history", [])
            path_html = " → ".join(
                f'<span style="color:#818cf8;font-size:0.78rem">{p}</span>'
                for p in path
            )
            st.markdown(f"<p>{path_html}</p>", unsafe_allow_html=True)

            if s.get("escalation_summary"):
                st.markdown("### Handoff Summary")
                st.code(s["escalation_summary"], language=None)

            if s.get("errors"):
                st.markdown("### ⚠ Errors")
                for err in s["errors"]:
                    st.error(err)

            st.markdown("### Execution Logs")
            log_html = "".join(
                f'<div class="log-entry">{line}</div>'
                for line in s.get("logs", [])
            )
            st.markdown(f'<div class="log-wrap">{log_html}</div>', unsafe_allow_html=True)

        # ── Go Live celebration ───────────────────────────────────────────────────
        if s.get("listing_live"):
            st.markdown("---")
            st.success(
                f"🎉 **{s.get('company_name')}** is live on Aarna! "
                f"Inventory now flowing to Abhee · MIRAEE · Mondee 65k+ agents. "
                f"Live since {s.get('live_timestamp','—')}."
            )

    # ─────────────────────────────────────────────────────────────────────────────
    # FOOTER
    # ─────────────────────────────────────────────────────────────────────────────

    st.markdown("---")
    st.markdown(
        '<p style="font-size:0.7rem;color:#3d4462;text-align:center">'
        "Aarna GTM Pipeline · LangGraph + Streamlit · 7 stages · No-loop architecture · "
        "Human escalation on request or commercial complexity"
        "</p>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# RUN PIPELINE
# ─────────────────────────────────────────────────────────────────────────────

if run_btn:
    # ── Reset previous result immediately so UI doesn't show stale data ──
    st.session_state.lead_state = None

    # ── Re-build graph if it's missing (e.g. after hot-reload) ──
    if st.session_state.graph is None:
        try:
            st.session_state.graph = build_aarna_graph()
            st.session_state.graph_error = None
        except Exception as e:
            st.session_state.graph_error = str(e)

    if st.session_state.graph is None:
        st.error(
            f"LangGraph unavailable: {st.session_state.graph_error}\n\n"
            "Run: `pip install langgraph langchain-core`"
        )
    else:
        initial: LeadState = {
            **DEMO_STATE,
            # ── Lead identity ──
            "company_name":           company_name,
            "contact_name":           contact_name,
            "phone":                  phone,
            "email":                  email,
            "emirate":                emirate,
            "supply_category":        supply_cat,
            "digitisation_level":     digitisation,
            "entry_source":           entry_source,
            # ── Scenario flags ──
            "partner_responded":      partner_responds,
            "partner_interested":     partner_responds,
            "partner_reply_text":     "",
            "media_submitted":        media_ok,
            "agreement_signed":       agreement_signed,
            "bank_details_collected": onboarding_ready,
            "trade_licence_number":   "DED-2024-98765" if onboarding_ready else "",
            "experience_description": (
                "4-hour desert safari: dune bashing, camel riding, BBQ dinner."
                if onboarding_ready else ""
            ),
            "pricing_per_person_aed": 350.0 if onboarding_ready else 0.0,
            "operating_days":         (
                ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"] if onboarding_ready else []
            ),
            # ── Escalation ──
            "escalate_to_human":  escalate_human,
            "escalation_reason":  esc_reason,
            # ── Explicitly reset all pipeline-accumulated state ──
            # (don't rely on DEMO_STATE for these — always start clean)
            "lead_id":                "",
            "stage_history":          [],
            "logs":                   [],
            "errors":                 [],
            "quality_failures":       [],
            "outreach_channels_sent": [],
            "onboarding_gaps":        [],
            "listing_live":           False,
            "live_timestamp":         "",
            "escalation_summary":     "",
            "assigned_team_member":   "",
            "onboarding_complete":    False,
            "enrichment_complete":    False,
            "missing_fields":         [],
            "current_stage":          "",
        }

        main_placeholder = st.empty()
        with st.spinner("Running pipeline…"):
            try:
                import time
                for output in st.session_state.graph.stream(initial):
                    for node_name, state in output.items():
                        st.session_state.lead_state = state
                        with main_placeholder.container():
                            render_dashboard(state)
                        time.sleep(1.5)
            except Exception as e:
                st.session_state.lead_state = None
                st.error(f"Pipeline error: {e}")
                with main_placeholder.container():
                    render_dashboard(None)

else:
    # If not running, just render the final dashboard normally
    render_dashboard(st.session_state.lead_state)
