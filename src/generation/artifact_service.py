from __future__ import annotations

from src.core.models import ArtifactType, GeneratedArtifact, JobPosting, UserProfile
from src.generation.openai_client import OpenAITextClient
from src.generation.prompts import SYSTEM_PROMPT, build_prompt


class ArtifactService:
    def __init__(self, client: OpenAITextClient) -> None:
        self.client = client

    def generate(self, profile: UserProfile, posting: JobPosting, artifact_type: ArtifactType) -> GeneratedArtifact:
        if not self.client.api_key:
            content = self._fallback(profile, posting, artifact_type)
        else:
            prompt = build_prompt(profile, posting, artifact_type)
            content = self.client.generate(SYSTEM_PROMPT, prompt)
            if not content:
                content = self._fallback(profile, posting, artifact_type)

        return GeneratedArtifact(job_url=posting.url, artifact_type=artifact_type, content=content)

    def _fallback(self, profile: UserProfile, posting: JobPosting, artifact_type: ArtifactType) -> str:
        common = (
            f"Role: {posting.title} at {posting.company}\n"
            f"Matched skills: {', '.join([s for s in profile.skills[:6]])}\n"
            f"Target focus: {', '.join(profile.target_roles)}\n"
        )
        if artifact_type == ArtifactType.RESUME_BULLETS:
            return common + "\n" + "\n".join(
                [
                    "- Built practical projects aligned with role requirements and documented measurable impact.",
                    "- Applied core technical skills in team settings to deliver features under deadlines.",
                    "- Used data-driven debugging and testing to improve reliability and user experience.",
                    "- Collaborated with peers through clear communication and iterative feedback cycles.",
                    "- Adapted quickly to new tools and learned domain context to ship quality outcomes.",
                ]
            )
        if artifact_type == ArtifactType.COVER_LETTER:
            return (
                f"Dear Hiring Team at {posting.company},\n\n"
                f"I am excited to apply for the {posting.title} internship. "
                f"My background in {', '.join(profile.skills[:4])} and interest in {', '.join(profile.target_roles)} "
                "has prepared me to contribute quickly. "
                "I enjoy solving practical problems, learning fast, and collaborating with cross-functional teams.\n\n"
                "I would value the opportunity to support your team while continuing to grow in a high-impact environment. "
                "Thank you for your consideration.\n\n"
                f"Sincerely,\n{profile.full_name}"
            )
        if artifact_type == ArtifactType.OUTREACH_EMAIL:
            return (
                f"Subject: Interest in {posting.title} Internship\n\n"
                f"Hi {posting.company} Recruiting Team,\n\n"
                f"I am interested in your {posting.title} internship and wanted to share my background in "
                f"{', '.join(profile.skills[:4])}. I would love to contribute and learn from your team. "
                f"If helpful, I can send targeted project examples for this role.\n\n"
                f"Best,\n{profile.full_name}"
            )
        return common + "\n- Prepare one project deep-dive story using STAR format.\n- Map each job requirement to one concrete example from your work.\n- Practice explaining trade-offs, testing strategy, and collaboration decisions.\n- Prepare questions about mentorship, team structure, and internship outcomes."
