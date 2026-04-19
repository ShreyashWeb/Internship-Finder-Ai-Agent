from __future__ import annotations

from datetime import UTC, datetime

import streamlit as st

from src.core.bootstrap import build_container
from src.core.models import ArtifactType, PlanStatus, UserProfile
from src.matching.insights import generate_insights
from src.matching.scorer import JobScorer
from src.pipeline.planner import ApplicationPlanner


st.set_page_config(page_title="Auto Internship Hunter", layout="wide")


def _inject_styles() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700;800&display=swap');

        :root {
            --ink: #0f172a;
            --ink-soft: #334155;
            --accent: #0b57d0;
            --accent-2: #ff7a18;
            --card: rgba(255, 255, 255, 0.92);
            --stroke: rgba(11, 87, 208, 0.2);
        }

        .stApp {
            font-family: 'Manrope', sans-serif;
            background:
                radial-gradient(circle at 8% 15%, rgba(11, 87, 208, 0.13), transparent 26%),
                radial-gradient(circle at 92% 20%, rgba(255, 122, 24, 0.12), transparent 28%),
                linear-gradient(135deg, #f8fbff 0%, #eff4fb 100%);
            color: var(--ink);
        }

        .block-container {
            padding-top: 1.2rem;
            padding-bottom: 2rem;
        }

        .hero {
            position: relative;
            overflow: hidden;
            border: 1px solid var(--stroke);
            background: linear-gradient(120deg, rgba(255,255,255,0.85), rgba(242, 247, 246, 0.75));
            border-radius: 20px;
            padding: 1.6rem 1.8rem;
            margin-bottom: 1rem;
            box-shadow: 0 20px 50px rgba(19, 38, 47, 0.08);
            animation: rise 600ms ease-out;
        }

        .hero-title {
            font-size: clamp(1.5rem, 2.4vw, 2.2rem);
            font-weight: 800;
            letter-spacing: 0.2px;
            margin: 0;
        }

        .hero-sub {
            margin-top: 0.55rem;
            color: var(--ink-soft);
            font-size: 0.98rem;
            max-width: 880px;
        }

        .tab-subtitle {
            color: var(--ink-soft);
            font-size: 0.95rem;
            margin: 0.2rem 0 0.8rem 0;
        }

        .pulse-orb {
            position: absolute;
            border-radius: 999px;
            filter: blur(0.2px);
            opacity: 0.45;
            animation: floatY 4.5s ease-in-out infinite;
        }

        .pulse-orb.one {
            width: 110px;
            height: 110px;
            right: 12px;
            top: 8px;
            background: radial-gradient(circle at 30% 30%, rgba(15,157,143,0.65), rgba(15,157,143,0.12));
        }

        .pulse-orb.two {
            width: 72px;
            height: 72px;
            right: 80px;
            bottom: 10px;
            background: radial-gradient(circle at 30% 30%, rgba(242,107,56,0.62), rgba(242,107,56,0.12));
            animation-delay: 1.2s;
        }

        .kicker {
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #1d4ed8;
            font-size: 0.72rem;
            margin-bottom: 0.2rem;
            font-weight: 700;
        }

        .metric-chip {
            display: inline-block;
            font-size: 0.78rem;
            color: #0b57d0;
            background: rgba(11, 87, 208, 0.11);
            border: 1px solid rgba(11, 87, 208, 0.24);
            padding: 0.2rem 0.55rem;
            border-radius: 999px;
            margin-right: 0.35rem;
            margin-bottom: 0.3rem;
        }

        .profile-card {
            border: 1px solid var(--stroke);
            background: rgba(255, 255, 255, 0.95);
            border-radius: 14px;
            padding: 0.8rem 0.95rem;
            margin-bottom: 0.9rem;
        }

        .profile-row {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.65rem;
        }

        .profile-item {
            border: 1px solid rgba(11, 87, 208, 0.18);
            border-radius: 10px;
            padding: 0.55rem 0.6rem;
            background: #ffffff;
        }

        .profile-label {
            font-size: 0.72rem;
            color: #475569;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.2rem;
            font-weight: 700;
        }

        .profile-value {
            font-size: 0.95rem;
            color: #0f172a;
            font-weight: 700;
            word-break: break-word;
        }

        .glass-panel {
            border: 1px solid var(--stroke);
            background: var(--card);
            border-radius: 16px;
            padding: 0.9rem 1rem;
            box-shadow: 0 10px 26px rgba(19, 38, 47, 0.08);
            animation: rise 450ms ease-out;
            margin-bottom: 0.85rem;
        }

        [data-testid="stTabs"] button {
            font-weight: 700;
        }

        [data-testid="stMetric"] {
            border: 1px solid var(--stroke);
            background: rgba(255, 255, 255, 0.7);
            border-radius: 14px;
            padding: 0.35rem 0.6rem;
        }

        .stButton > button {
            border-radius: 12px;
            border: 1px solid rgba(11, 87, 208, 0.35);
            color: #0f172a;
            background: #ffffff;
        }

        .stTextInput input,
        .stTextArea textarea,
        div[data-baseweb="select"] > div,
        .stNumberInput input {
            background: #ffffff !important;
            color: #0f172a !important;
            border: 1px solid rgba(11, 87, 208, 0.24) !important;
        }

        [data-testid="stWidgetLabel"] p,
        .stMarkdown,
        .stCaption,
        .stSubheader {
            color: #0f172a !important;
        }

        @keyframes rise {
            from { transform: translateY(10px); opacity: 0; }
            to { transform: translateY(0px); opacity: 1; }
        }

        @keyframes floatY {
            0% { transform: translateY(0); }
            50% { transform: translateY(-10px); }
            100% { transform: translateY(0); }
        }

        @media (max-width: 768px) {
            .hero { padding: 1.2rem 1rem; }
            .profile-row { grid-template-columns: 1fr; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_hero() -> None:
    st.markdown(
        """
        <div class="hero">
            <div class="pulse-orb one"></div>
            <div class="pulse-orb two"></div>
            <div class="kicker">AI Career Engine</div>
            <h1 class="hero-title">Auto Internship Hunter Agent</h1>
            <p class="hero-sub">
                Discover, filter, and execute with confidence. The agent now ranks opportunities, diagnoses skill gaps,
                generates tailored applications, and builds a daily action queue so you can move from searching to submitting.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _load_ranked(container: object) -> tuple[UserProfile | None, list]:
    profile = container.profile_repo.get()
    recent_jobs = container.job_repo.list_recent(limit=250)
    ranked = (
        JobScorer(threshold=container.settings.match_threshold).rank(profile, recent_jobs)
        if profile
        else []
    )
    return profile, ranked


_inject_styles()
_render_hero()

container = build_container()

profile, ranked = _load_ranked(container)

name_value = profile.full_name if profile and profile.full_name else "Not set"
email_value = profile.email if profile and profile.email else "Not set"
position_value = (
    ", ".join(profile.target_roles[:2])
    if profile and profile.target_roles
    else "Not set"
)

st.markdown(
    f"""
    <div class="profile-card">
        <div class="profile-row">
            <div class="profile-item">
                <div class="profile-label">Name</div>
                <div class="profile-value">{name_value}</div>
            </div>
            <div class="profile-item">
                <div class="profile-label">Email ID</div>
                <div class="profile-value">{email_value}</div>
            </div>
            <div class="profile-item">
                <div class="profile-label">Position</div>
                <div class="profile-value">{position_value}</div>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

tab_profile, tab_discover, tab_generate, tab_planner = st.tabs(
    ["Profile", "Discover", "Generate", "Planner"]
)

with tab_profile:
    st.markdown("<div class='glass-panel'>", unsafe_allow_html=True)
    st.subheader("Your Candidate Profile")
    st.markdown(
        "<p class='tab-subtitle'>Set your goals once, and the agent customizes every search, score, and artifact to this context.</p>",
        unsafe_allow_html=True,
    )

    existing = container.profile_repo.get()
    with st.form("profile_form"):
        full_name = st.text_input("Name", value=existing.full_name if existing else "")
        email = st.text_input("Email ID", value=existing.email if existing else "")
        target_roles = st.text_input(
            "Position(s) you are targeting (comma separated)",
            value=", ".join(existing.target_roles) if existing else "Software Engineer Intern",
        )
        skills = st.text_input(
            "Skills (comma separated)",
            value=", ".join(existing.skills) if existing else "Python, SQL, APIs",
        )
        experience = st.text_area(
            "Experience summary",
            value=existing.experience_summary if existing else "",
            height=120,
        )
        location = st.text_input(
            "Location preference",
            value=existing.location_preference if existing else "Remote",
        )
        submitted = st.form_submit_button("Save Profile", use_container_width=True)

    if submitted:
        updated_profile = UserProfile(
            full_name=full_name,
            email=email,
            target_roles=[item.strip() for item in target_roles.split(",") if item.strip()],
            skills=[item.strip() for item in skills.split(",") if item.strip()],
            experience_summary=experience,
            location_preference=location,
        )
        container.profile_repo.upsert(updated_profile)
        st.success("Profile saved. Switch to Discover to run a fresh search.")
    st.markdown("</div>", unsafe_allow_html=True)

with tab_discover:
    st.markdown("<div class='glass-panel'>", unsafe_allow_html=True)
    st.subheader("Opportunity Discovery")
    st.markdown(
        "<p class='tab-subtitle'>Run the fetch engine, rank opportunities by fit, and inspect why each role is recommended.</p>",
        unsafe_allow_html=True,
    )

    if st.button("Fetch + Rank Internships", use_container_width=True):
        try:
            result = container.pipeline.run()
            st.success(
                f"Run {result.run_id} completed. Fetched {result.fetched_count} jobs, ranked {result.ranked_count}."
            )
            profile, ranked = _load_ranked(container)
        except Exception as exc:
            st.error(str(exc))

    if ranked:
        insights_payload = generate_insights(profile, ranked[:20])
        c1, c2, c3 = st.columns(3)
        c1.metric("Average Fit", f"{insights_payload.average_score:.2f}")
        c2.metric("High Intent Roles", str(insights_payload.high_intent_count))
        c3.metric("Ranked Opportunities", str(len(ranked)))

        if insights_payload.top_missing_skills:
            st.warning("Top missing skills: " + ", ".join(insights_payload.top_missing_skills))
            chips = "".join(
                f'<span class="metric-chip">{skill}</span>'
                for skill in insights_payload.top_missing_skills
            )
            st.markdown(chips, unsafe_allow_html=True)

        with st.expander("7-day Strategy Blueprint", expanded=False):
            for idx, item in enumerate(insights_payload.weekly_action_plan, start=1):
                st.write(f"{idx}. {item}")
    else:
        st.info("No ranked jobs yet. Save profile, then run Fetch + Rank Internships.")
    st.markdown("</div>", unsafe_allow_html=True)

with tab_generate:
    st.markdown("<div class='glass-panel'>", unsafe_allow_html=True)
    st.subheader("Tailored Artifact Generator")
    st.markdown(
        "<p class='tab-subtitle'>Choose a ranked role and generate role-specific assets instantly.</p>",
        unsafe_allow_html=True,
    )

    if ranked:
        options = {
            f"{item.posting.title} | {item.posting.company} | {item.score:.2f}": item
            for item in ranked[:40]
        }
        selected_label = st.selectbox("Select a role", list(options.keys()), key="generate_role")
        selected = options[selected_label]

        left_meta, right_meta = st.columns([2, 1.2])
        with left_meta:
            st.markdown(f"**URL:** {selected.posting.url}")
            st.markdown(f"**Priority:** {selected.priority_label}")
            st.caption(selected.reasoning)
            st.markdown(f"**Matched skills:** {', '.join(selected.matched_skills) or 'None'}")
            st.markdown(f"**Missing skills:** {', '.join(selected.missing_skills) or 'None'}")
        with right_meta:
            if selected.score_breakdown:
                st.json(selected.score_breakdown, expanded=False)

        artifact_type = st.selectbox(
            "Artifact",
            [
                ArtifactType.RESUME_BULLETS,
                ArtifactType.COVER_LETTER,
                ArtifactType.OUTREACH_EMAIL,
                ArtifactType.INTERVIEW_PREP,
            ],
            format_func=lambda x: x.value,
            key="artifact_type",
        )

        if st.button("Generate Tailored Output", use_container_width=True):
            artifact = container.artifact_service.generate(profile, selected.posting, artifact_type)
            container.artifact_repo.save(artifact)
            st.text_area("Generated content", value=artifact.content, height=320)
    else:
        st.info("No ranked opportunities available. Use the Discover tab first.")
    st.markdown("</div>", unsafe_allow_html=True)

with tab_planner:
    st.markdown("<div class='glass-panel'>", unsafe_allow_html=True)
    st.subheader("Execution Planner")
    st.markdown(
        "<p class='tab-subtitle'>Convert recommendations into a daily execution queue and track completion status.</p>",
        unsafe_allow_html=True,
    )

    plan_days, plan_per_day = st.columns(2)
    days = plan_days.number_input("Plan horizon (days)", min_value=1, max_value=30, value=7)
    per_day = plan_per_day.number_input("Applications per day", min_value=1, max_value=10, value=3)

    if st.button("Build / Refresh Plan", use_container_width=True):
        if not profile:
            st.error("Please save profile first.")
        elif not ranked:
            st.error("No ranked jobs found. Use Discover tab first.")
        else:
            planner = ApplicationPlanner()
            items = planner.build_plan(ranked, days=int(days), per_day=int(per_day))
            container.plan_repo.replace_plan(items)
            st.success(f"Plan updated with {len(items)} tasks.")

    today = datetime.now(UTC).date().isoformat()
    today_items = container.plan_repo.list_by_date(today)
    st.markdown(f"**Today's queue ({today})**")

    if today_items:
        for item in today_items:
            with st.container(border=True):
                st.write(f"#{item.id} | {item.title} @ {item.company}")
                st.write(
                    f"Score: {item.score:.2f} | Priority: {item.priority_label} | Status: {item.status.value}"
                )
                if item.notes:
                    st.caption(item.notes)

                status_key = f"status_{item.id}"
                note_key = f"note_{item.id}"
                new_status = st.selectbox(
                    f"Update status for #{item.id}",
                    [
                        PlanStatus.PLANNED,
                        PlanStatus.IN_PROGRESS,
                        PlanStatus.APPLIED,
                        PlanStatus.SKIPPED,
                    ],
                    index=[
                        PlanStatus.PLANNED,
                        PlanStatus.IN_PROGRESS,
                        PlanStatus.APPLIED,
                        PlanStatus.SKIPPED,
                    ].index(item.status),
                    format_func=lambda x: x.value,
                    key=status_key,
                )
                note_text = st.text_input("Notes", value=item.notes, key=note_key)
                if st.button(f"Save #{item.id}", key=f"save_{item.id}"):
                    container.plan_repo.update_status(item.id, new_status, note_text)
                    st.success(f"Updated task #{item.id}")
    else:
        st.info("No tasks planned for today yet. Build a plan first.")
    st.markdown("</div>", unsafe_allow_html=True)
