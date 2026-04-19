from __future__ import annotations

from src.core.models import ArtifactType, JobPosting, UserProfile


SYSTEM_PROMPT = (
    "You are an expert internship application coach. "
    "Write tailored, factual, concise output based only on the provided profile and job details."
)



def build_prompt(profile: UserProfile, posting: JobPosting, artifact_type: ArtifactType) -> str:
    shared = f"""
Candidate profile:
- Name: {profile.full_name}
- Email: {profile.email}
- Target roles: {", ".join(profile.target_roles)}
- Skills: {", ".join(profile.skills)}
- Experience summary: {profile.experience_summary}
- Location preference: {profile.location_preference}

Job posting:
- Title: {posting.title}
- Company: {posting.company}
- Location: {posting.location}
- URL: {posting.url}
- Tags: {", ".join(posting.tags)}
- Description: {posting.description[:2500]}
""".strip()

    if artifact_type == ArtifactType.RESUME_BULLETS:
        instruction = "Write 5 concise resume bullet points tailored to this role. Use action verbs and measurable outcomes when possible."
    elif artifact_type == ArtifactType.COVER_LETTER:
        instruction = "Write a 250-350 word internship cover letter tailored to this role and company."
    elif artifact_type == ArtifactType.OUTREACH_EMAIL:
        instruction = "Write a short outreach email to a recruiter/hiring manager showing fit and interest."
    else:
        instruction = "Write 8 interview prep bullet points: likely questions + concise talking points for this role."

    return f"{shared}\n\nTask: {instruction}"
