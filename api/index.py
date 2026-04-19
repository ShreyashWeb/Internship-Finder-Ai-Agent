from __future__ import annotations

from datetime import UTC, datetime
import os

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from src.core.bootstrap import build_container
from src.core.models import ArtifactType, PlanStatus, UserProfile
from src.matching.insights import generate_insights
from src.matching.scorer import JobScorer
from src.pipeline.planner import ApplicationPlanner

app = FastAPI(title="Internship Finder AI Agent API", version="1.0.0")
BUILD_SHA = os.getenv("VERCEL_GIT_COMMIT_SHA", "local")
BUILD_ID = BUILD_SHA[:7]


def _load_ranked(container: object) -> tuple[UserProfile | None, list]:
        profile = container.profile_repo.get()
        recent_jobs = container.job_repo.list_recent(limit=250)
        ranked = (
                JobScorer(threshold=container.settings.match_threshold).rank(profile, recent_jobs)
                if profile
                else []
        )
        return profile, ranked


@app.get("/", response_class=HTMLResponse)
def root() -> str:
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Internship Finder AI Agent</title>
    <style>
        body {
            margin: 0;
            font-family: Manrope, Segoe UI, sans-serif;
            color: #0f172a;
            background:
                radial-gradient(circle at 10% 10%, rgba(11, 87, 208, 0.16), transparent 25%),
                radial-gradient(circle at 90% 15%, rgba(255, 122, 24, 0.14), transparent 28%),
                linear-gradient(135deg, #f8fbff, #eef5ff);
        }
        .wrap { max-width: 980px; margin: 24px auto; padding: 0 14px; }
        .hero {
            border: 1px solid rgba(11, 87, 208, 0.22);
            border-radius: 18px;
            background: rgba(255, 255, 255, 0.9);
            padding: 18px;
            box-shadow: 0 12px 30px rgba(15, 23, 42, 0.08);
            margin-bottom: 14px;
        }
        .card {
            border: 1px solid rgba(11, 87, 208, 0.2);
            border-radius: 14px;
            background: rgba(255, 255, 255, 0.92);
            padding: 14px;
            margin-bottom: 12px;
        }
        h1 { margin: 0 0 6px 0; }
        h3 { margin: 2px 0 10px 0; }
        .grid { display: grid; gap: 10px; grid-template-columns: repeat(2, minmax(0,1fr)); }
        .grid3 { display: grid; gap: 10px; grid-template-columns: repeat(3, minmax(0,1fr)); }
        label { font-size: 12px; color: #334155; font-weight: 700; }
        input, textarea, select {
            width: 100%; box-sizing: border-box;
            border: 1px solid rgba(11, 87, 208, 0.28);
            border-radius: 10px; padding: 9px;
            font-size: 14px; color: #0f172a; background: #fff;
        }
        textarea { min-height: 92px; }
        button {
            border: 1px solid rgba(11, 87, 208, 0.35);
            border-radius: 10px; padding: 9px 12px;
            background: #fff; color: #0f172a; cursor: pointer;
            font-weight: 700;
        }
        .row { display: flex; gap: 8px; flex-wrap: wrap; }
        .pill {
            display: inline-block; padding: 3px 8px; border-radius: 999px;
            border: 1px solid rgba(11, 87, 208, 0.24); background: rgba(11, 87, 208, 0.1);
            color: #0b57d0; font-size: 12px; margin-right: 6px; margin-bottom: 6px;
        }
        .muted { color: #475569; font-size: 13px; }
        pre {
            background: #f8fafc; border: 1px solid #dbeafe;
            border-radius: 10px; padding: 10px; overflow-x: auto;
            white-space: pre-wrap;
        }
        @media (max-width: 760px) {
            .grid, .grid3 { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="wrap">
        <div class="hero">
            <h1>Internship Finder AI Agent</h1>
            <div class="muted">Vercel UI: save profile, run discovery, rank matches, generate artifacts, and build a daily plan.</div>
            <div class="muted" style="margin-top:6px; font-weight:700; color:#0b57d0;">UI Build: {BUILD_ID}</div>
        </div>

        <div class="card">
            <h3>Profile</h3>
            <div class="grid3">
                <div><label>Name</label><input id="name" /></div>
                <div><label>Email ID</label><input id="email" /></div>
                <div><label>Position</label><input id="roles" placeholder="Software Engineer Intern, Data Analyst Intern" /></div>
            </div>
            <div class="grid">
                <div><label>Skills</label><input id="skills" placeholder="Python, SQL, APIs" /></div>
                <div><label>Location Preference</label><input id="location" placeholder="Remote" /></div>
            </div>
            <div><label>Experience Summary</label><textarea id="experience"></textarea></div>
            <div class="row" style="margin-top:8px;">
                <button onclick="saveProfile()">Save Profile</button>
                <button onclick="runDiscovery()">Fetch + Rank</button>
            </div>
            <div id="status" class="muted" style="margin-top:8px;"></div>
        </div>

        <div class="card">
            <h3>Top Matches</h3>
            <div id="metrics" class="muted"></div>
            <div id="missing"></div>
            <pre id="matches">Run discovery to load opportunities.</pre>
        </div>

        <div class="card">
            <h3>Generate Artifact</h3>
            <div class="grid">
                <div><label>Job URL</label><input id="jobUrl" placeholder="Paste a URL from top matches" /></div>
                <div>
                    <label>Artifact Type</label>
                    <select id="artifactType">
                        <option value="resume_bullets">resume_bullets</option>
                        <option value="cover_letter">cover_letter</option>
                        <option value="outreach_email">outreach_email</option>
                        <option value="interview_prep">interview_prep</option>
                    </select>
                </div>
            </div>
            <div class="row" style="margin-top:8px;"><button onclick="generateArtifact()">Generate</button></div>
            <pre id="artifactOutput">Generated artifact will appear here.</pre>
        </div>

        <div class="card">
            <h3>Planner</h3>
            <div class="grid">
                <div><label>Days</label><input id="days" type="number" min="1" max="30" value="7" /></div>
                <div><label>Per Day</label><input id="perDay" type="number" min="1" max="10" value="3" /></div>
            </div>
            <div class="row" style="margin-top:8px;">
                <button onclick="buildPlan()">Build / Refresh Plan</button>
                <button onclick="loadTodayPlan()">Load Today Queue</button>
            </div>
            <pre id="planOutput">Today's queue will appear here.</pre>
        </div>
    </div>

    <script>
        async function api(path, method='GET', body=null) {
            const res = await fetch(path, {
                method,
                headers: {'Content-Type': 'application/json'},
                body: body ? JSON.stringify(body) : null
            });
            if (!res.ok) {
                let text = await res.text();
                throw new Error(text || 'Request failed');
            }
            return await res.json();
        }

        function setStatus(msg) {
            document.getElementById('status').textContent = msg;
        }

        async function saveProfile() {
            try {
                const payload = {
                    full_name: document.getElementById('name').value,
                    email: document.getElementById('email').value,
                    target_roles: document.getElementById('roles').value,
                    skills: document.getElementById('skills').value,
                    experience_summary: document.getElementById('experience').value,
                    location_preference: document.getElementById('location').value
                };
                await api('/profile', 'POST', payload);
                setStatus('Profile saved.');
            } catch (e) {
                setStatus('Profile save failed: ' + e.message);
            }
        }

        async function runDiscovery() {
            try {
                const out = await api('/run', 'POST');
                setStatus(`Run ${out.run_id} completed. Fetched ${out.fetched_count}, ranked ${out.ranked_count}.`);
                await loadMatches();
            } catch (e) {
                setStatus('Discovery failed: ' + e.message);
            }
        }

        async function loadMatches() {
            try {
                const out = await api('/matches?limit=15');
                document.getElementById('metrics').textContent = `Average fit: ${out.insights.average_score} | High intent: ${out.insights.high_intent_count}`;
                const missing = out.insights.top_missing_skills || [];
                document.getElementById('missing').innerHTML = missing.map(s => `<span class='pill'>${s}</span>`).join('');
                document.getElementById('matches').textContent = (out.matches || []).map((m, i) => `${i+1}. ${m.title} | ${m.company} | ${m.score} | ${m.url}`).join('\n') || 'No matches';
            } catch (e) {
                document.getElementById('matches').textContent = 'Load matches failed: ' + e.message;
            }
        }

        async function generateArtifact() {
            try {
                const out = await api('/generate', 'POST', {
                    job_url: document.getElementById('jobUrl').value,
                    artifact_type: document.getElementById('artifactType').value
                });
                document.getElementById('artifactOutput').textContent = out.content;
            } catch (e) {
                document.getElementById('artifactOutput').textContent = 'Generate failed: ' + e.message;
            }
        }

        async function buildPlan() {
            try {
                const out = await api('/plan/build', 'POST', {
                    days: Number(document.getElementById('days').value),
                    per_day: Number(document.getElementById('perDay').value)
                });
                document.getElementById('planOutput').textContent = `Plan built with ${out.count} tasks.`;
            } catch (e) {
                document.getElementById('planOutput').textContent = 'Plan build failed: ' + e.message;
            }
        }

        async function loadTodayPlan() {
            try {
                const out = await api('/plan/today');
                document.getElementById('planOutput').textContent = (out.items || []).map(
                    x => `#${x.id} ${x.title} @ ${x.company} | score=${x.score} | ${x.status}`
                ).join('\n') || 'No tasks planned for today.';
            } catch (e) {
                document.getElementById('planOutput').textContent = 'Load plan failed: ' + e.message;
            }
        }

        api('/profile').then(p => {
            if (!p) return;
            document.getElementById('name').value = p.full_name || '';
            document.getElementById('email').value = p.email || '';
            document.getElementById('roles').value = (p.target_roles || []).join(', ');
            document.getElementById('skills').value = (p.skills || []).join(', ');
            document.getElementById('experience').value = p.experience_summary || '';
            document.getElementById('location').value = p.location_preference || '';
            loadMatches();
        }).catch(() => {});
    </script>
</body>
</html>
"""


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy"}


@app.get("/version")
def version() -> dict[str, str]:
    return {
        "build_id": BUILD_ID,
        "build_sha": BUILD_SHA,
    }


@app.get("/profile")
def get_profile() -> dict | None:
        container = build_container()
        profile = container.profile_repo.get()
        if not profile:
                return None
        return {
                "full_name": profile.full_name,
                "email": profile.email,
                "target_roles": profile.target_roles,
                "skills": profile.skills,
                "experience_summary": profile.experience_summary,
                "location_preference": profile.location_preference,
        }


@app.post("/profile")
def save_profile(payload: dict) -> dict[str, str]:
        container = build_container()
        profile = UserProfile(
                full_name=str(payload.get("full_name", "")).strip(),
                email=str(payload.get("email", "")).strip(),
                target_roles=[x.strip() for x in str(payload.get("target_roles", "")).split(",") if x.strip()],
                skills=[x.strip() for x in str(payload.get("skills", "")).split(",") if x.strip()],
                experience_summary=str(payload.get("experience_summary", "")).strip(),
                location_preference=str(payload.get("location_preference", "")).strip(),
        )
        if not profile.full_name or not profile.email:
                raise HTTPException(status_code=400, detail="full_name and email are required")
        container.profile_repo.upsert(profile)
        return {"status": "saved"}


@app.post("/run")
def run_pipeline() -> dict:
        container = build_container()
        result = container.pipeline.run()
        return {
                "run_id": result.run_id,
                "fetched_count": result.fetched_count,
                "ranked_count": result.ranked_count,
        }


@app.get("/matches")
def get_matches(limit: int = 20) -> dict:
        container = build_container()
        profile, ranked = _load_ranked(container)
        if not profile:
                raise HTTPException(status_code=400, detail="Profile not found")
        ranked_slice = ranked[: max(1, min(limit, 50))]
        insights = generate_insights(profile, ranked_slice)
        return {
                "matches": [
                        {
                                "title": item.posting.title,
                                "company": item.posting.company,
                                "score": round(item.score, 3),
                                "url": item.posting.url,
                                "priority": item.priority_label,
                        }
                        for item in ranked_slice
                ],
                "insights": {
                        "average_score": insights.average_score,
                        "high_intent_count": insights.high_intent_count,
                        "top_missing_skills": insights.top_missing_skills,
                },
        }


@app.post("/generate")
def generate_artifact(payload: dict) -> dict:
        container = build_container()
        profile = container.profile_repo.get()
        if not profile:
                raise HTTPException(status_code=400, detail="Profile not found")

        job_url = str(payload.get("job_url", "")).strip()
        artifact_type_raw = str(payload.get("artifact_type", "resume_bullets"))
        if not job_url:
                raise HTTPException(status_code=400, detail="job_url is required")

        postings = container.job_repo.list_recent(limit=500)
        posting = next((job for job in postings if job.url == job_url), None)
        if posting is None:
                raise HTTPException(status_code=404, detail="Job URL not found in local database")

        try:
                artifact_type = ArtifactType(artifact_type_raw)
        except ValueError as exc:
                raise HTTPException(status_code=400, detail="Invalid artifact_type") from exc

        artifact = container.artifact_service.generate(profile, posting, artifact_type)
        container.artifact_repo.save(artifact)
        return {"content": artifact.content}


@app.post("/plan/build")
def build_plan(payload: dict) -> dict:
        container = build_container()
        profile, ranked = _load_ranked(container)
        if not profile:
                raise HTTPException(status_code=400, detail="Profile not found")
        if not ranked:
                raise HTTPException(status_code=400, detail="No ranked jobs found. Run discovery first")

        days = int(payload.get("days", 7))
        per_day = int(payload.get("per_day", 3))
        planner = ApplicationPlanner()
        items = planner.build_plan(ranked, days=days, per_day=per_day)
        container.plan_repo.replace_plan(items)
        return {"status": "ok", "count": len(items)}


@app.get("/plan/today")
def get_today_plan() -> dict:
        container = build_container()
        today = datetime.now(UTC).date().isoformat()
        items = container.plan_repo.list_by_date(today)
        return {
                "date": today,
                "items": [
                        {
                                "id": item.id,
                                "title": item.title,
                                "company": item.company,
                                "score": round(item.score, 3),
                                "status": item.status.value,
                        }
                        for item in items
                ],
        }


@app.post("/plan/update")
def update_plan(payload: dict) -> dict[str, str]:
        container = build_container()
        item_id = int(payload.get("item_id", 0))
        status_raw = str(payload.get("status", PlanStatus.PLANNED.value))
        notes = str(payload.get("notes", ""))
        if item_id <= 0:
                raise HTTPException(status_code=400, detail="item_id must be positive")

        try:
                status = PlanStatus(status_raw)
        except ValueError as exc:
                raise HTTPException(status_code=400, detail="Invalid status") from exc

        container.plan_repo.update_status(item_id=item_id, status=status, notes=notes)
        return {"status": "updated"}
