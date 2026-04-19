from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from src.core.bootstrap import build_container
from src.core.models import ArtifactType, PlanStatus, UserProfile
from src.matching.insights import generate_insights
from src.matching.scorer import JobScorer
from src.pipeline.planner import ApplicationPlanner
from src.pipeline.run_pipeline import format_ranked_jobs
from src.pipeline.scheduler import DailyScheduler


app = typer.Typer(help="Auto Internship Hunter Agent")
console = Console()


@app.command()
def profile(
    full_name: str = typer.Option(..., prompt=True),
    email: str = typer.Option(..., prompt=True),
    target_roles: str = typer.Option(..., prompt="Target roles (comma separated)"),
    skills: str = typer.Option(..., prompt="Skills (comma separated)"),
    experience_summary: str = typer.Option("", prompt="Experience summary"),
    location_preference: str = typer.Option("", prompt="Location preference"),
) -> None:
    container = build_container()
    user_profile = UserProfile(
        full_name=full_name,
        email=email,
        target_roles=[item.strip() for item in target_roles.split(",") if item.strip()],
        skills=[item.strip() for item in skills.split(",") if item.strip()],
        experience_summary=experience_summary,
        location_preference=location_preference,
    )
    container.profile_repo.upsert(user_profile)
    console.print("Profile saved.")


@app.command()
def run() -> None:
    container = build_container()
    result = container.pipeline.run()
    console.print(
        f"Run {result.run_id} complete. Fetched={result.fetched_count}, Ranked={result.ranked_count}"
    )
    console.print(format_ranked_jobs(result.top_jobs[:10]))


@app.command()
def list_jobs(limit: int = 10) -> None:
    container = build_container()
    profile = container.profile_repo.get()
    if not profile:
        raise typer.BadParameter("No profile found. Run profile command first.")

    recent_jobs = container.job_repo.list_recent(limit=200)
    ranked = JobScorer(threshold=container.settings.match_threshold).rank(profile, recent_jobs)

    table = Table(title="Top Internship Matches")
    table.add_column("#")
    table.add_column("Title")
    table.add_column("Company")
    table.add_column("Score")
    table.add_column("Priority")
    table.add_column("Top Gap")
    table.add_column("URL")

    for index, item in enumerate(ranked[:limit], start=1):
        table.add_row(
            str(index),
            item.posting.title,
            item.posting.company,
            f"{item.score:.2f}",
            item.priority_label,
            item.missing_skills[0] if item.missing_skills else "-",
            item.posting.url,
        )

    console.print(table)


@app.command()
def insights(limit: int = 20) -> None:
    container = build_container()
    profile = container.profile_repo.get()
    if not profile:
        raise typer.BadParameter("No profile found. Run profile command first.")

    recent_jobs = container.job_repo.list_recent(limit=max(50, limit))
    ranked = JobScorer(threshold=container.settings.match_threshold).rank(profile, recent_jobs)
    insights_payload = generate_insights(profile, ranked[:limit])

    console.print(f"Average fit score: {insights_payload.average_score:.2f}")
    console.print(f"High intent opportunities: {insights_payload.high_intent_count}")
    console.print(
        "Top missing skills: " + (", ".join(insights_payload.top_missing_skills) if insights_payload.top_missing_skills else "None")
    )

    console.print("\n7-day action plan:")
    for idx, item in enumerate(insights_payload.weekly_action_plan, start=1):
        console.print(f"{idx}. {item}")


@app.command()
def generate(
    job_url: str = typer.Option(..., prompt=True),
    artifact_type: ArtifactType = typer.Option(ArtifactType.RESUME_BULLETS),
    export: bool = typer.Option(True, help="Export generated content to text file"),
) -> None:
    container = build_container()
    profile = container.profile_repo.get()
    if not profile:
        raise typer.BadParameter("No profile found. Run profile command first.")

    postings = container.job_repo.list_recent(limit=500)
    posting = next((job for job in postings if job.url == job_url), None)
    if posting is None:
        raise typer.BadParameter("Job URL not found in local database. Run pipeline first.")

    artifact = container.artifact_service.generate(profile, posting, artifact_type)
    container.artifact_repo.save(artifact)

    console.print(artifact.content)

    if export:
        filename = _safe_filename(f"{artifact_type.value}_{posting.company}_{posting.title}.txt")
        output_path = container.settings.export_dir / filename
        output_path.write_text(artifact.content, encoding="utf-8")
        console.print(f"Saved to {output_path}")


@app.command()
def schedule() -> None:
    container = build_container()
    scheduler = DailyScheduler(container.pipeline, container.settings.schedule_time)
    console.print(f"Starting daily scheduler at {container.settings.schedule_time}...")
    scheduler.start()


@app.command()
def plan_build(days: int = 7, per_day: int = 3) -> None:
    container = build_container()
    profile = container.profile_repo.get()
    if not profile:
        raise typer.BadParameter("No profile found. Run profile command first.")

    recent_jobs = container.job_repo.list_recent(limit=300)
    ranked = JobScorer(threshold=container.settings.match_threshold).rank(profile, recent_jobs)
    planner = ApplicationPlanner()
    items = planner.build_plan(ranked, days=days, per_day=per_day)
    container.plan_repo.replace_plan(items)
    console.print(f"Application plan built: {len(items)} tasks across {days} days.")


@app.command()
def plan_today() -> None:
    container = build_container()
    today = datetime.now(UTC).date().isoformat()
    items = container.plan_repo.list_by_date(today)
    if not items:
        console.print("No tasks scheduled for today. Run plan-build first.")
        return

    table = Table(title=f"Application Queue for {today}")
    table.add_column("ID")
    table.add_column("Title")
    table.add_column("Company")
    table.add_column("Score")
    table.add_column("Priority")
    table.add_column("Status")

    for item in items:
        table.add_row(
            str(item.id),
            item.title,
            item.company,
            f"{item.score:.2f}",
            item.priority_label,
            item.status.value,
        )
    console.print(table)


@app.command()
def plan_update(
    item_id: int = typer.Option(..., prompt=True),
    status: PlanStatus = typer.Option(..., prompt=True),
    notes: str = typer.Option(""),
) -> None:
    container = build_container()
    container.plan_repo.update_status(item_id=item_id, status=status, notes=notes)
    console.print(f"Updated item {item_id} to {status.value}.")



def _safe_filename(value: str) -> str:
    return "".join(ch for ch in value if ch.isalnum() or ch in "._-").strip("._")


if __name__ == "__main__":
    app()
