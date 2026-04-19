from __future__ import annotations

import re
from typing import Dict, List, Set

from src.core.models import JobPosting, RankedJob, UserProfile


TOKEN_PATTERN = re.compile(r"[a-zA-Z][a-zA-Z0-9+#.\-]{1,}")

SKILL_ALIASES: Dict[str, str] = {
    "js": "javascript",
    "ts": "typescript",
    "nodejs": "node.js",
    "node": "node.js",
    "py": "python",
    "ml": "machine learning",
    "ai": "artificial intelligence",
    "nlp": "natural language processing",
    "db": "sql",
    "postgres": "postgresql",
    "mongo": "mongodb",
}

KNOWN_SKILLS: Set[str] = {
    "python",
    "sql",
    "javascript",
    "typescript",
    "react",
    "node.js",
    "java",
    "c++",
    "c#",
    "golang",
    "rust",
    "html",
    "css",
    "aws",
    "azure",
    "gcp",
    "docker",
    "kubernetes",
    "git",
    "rest",
    "graphql",
    "pandas",
    "numpy",
    "pytorch",
    "tensorflow",
    "machine learning",
    "artificial intelligence",
    "natural language processing",
    "data analysis",
    "data visualization",
    "power bi",
    "tableau",
    "postgresql",
    "mongodb",
    "redis",
    "linux",
    "bash",
    "testing",
    "pytest",
    "fastapi",
    "django",
    "flask",
}


class JobScorer:
    def __init__(self, threshold: float = 0.2) -> None:
        self.threshold = threshold

    def rank(self, profile: UserProfile, postings: List[JobPosting]) -> List[RankedJob]:
        ranked: List[RankedJob] = []
        skill_set = {self._normalize_skill(s) for s in profile.skills if s.strip()}

        for posting in postings:
            text = " ".join(
                [
                    posting.title,
                    posting.company,
                    posting.location,
                    posting.description,
                    " ".join(posting.tags),
                ]
            ).lower()
            text_tokens = set(TOKEN_PATTERN.findall(text))
            required_skills = self._extract_required_skills(text, text_tokens)

            matched_skills = [skill for skill in skill_set if self._skill_in_text(skill, text, text_tokens)]
            matched_set = set(matched_skills)
            missing_skills = sorted(required_skills - matched_set)

            profile_match = len(matched_set) / max(len(skill_set), 1)
            required_coverage = len(matched_set & required_skills) / max(len(required_skills), 1)

            role_bonus = self._role_bonus(profile, posting)
            internship_bonus = 0.08 if "intern" in posting.title.lower() else 0.0
            location_bonus = self._location_bonus(profile, posting)

            score_breakdown = {
                "profile_match": round(profile_match * 0.45, 3),
                "required_coverage": round(required_coverage * 0.25, 3),
                "role_alignment": round(role_bonus, 3),
                "internship_bonus": round(internship_bonus, 3),
                "location_bonus": round(location_bonus, 3),
            }
            score = min(1.0, sum(score_breakdown.values()))
            if score >= self.threshold:
                priority_label = self._priority_label(score)
                ranked.append(
                    RankedJob(
                        posting=posting,
                        score=score,
                        matched_skills=sorted(matched_set),
                        missing_skills=missing_skills,
                        score_breakdown=score_breakdown,
                        priority_label=priority_label,
                        reasoning=self._build_reasoning(priority_label, matched_set, missing_skills),
                    )
                )

        ranked.sort(key=lambda item: item.score, reverse=True)
        return ranked

    def _role_bonus(self, profile: UserProfile, posting: JobPosting) -> float:
        text = f"{posting.title} {posting.description}".lower()
        bonus = 0.0
        for role in profile.target_roles:
            normalized_role = role.lower().strip()
            if normalized_role and normalized_role in text:
                bonus += 0.1
        return min(0.15, bonus)

    def _location_bonus(self, profile: UserProfile, posting: JobPosting) -> float:
        preference = profile.location_preference.lower().strip()
        if not preference:
            return 0.03
        location_text = posting.location.lower().strip()
        if preference in location_text:
            return 0.07
        if "remote" in preference and "remote" in location_text:
            return 0.07
        return 0.0

    def _normalize_skill(self, skill: str) -> str:
        normalized = skill.lower().strip()
        return SKILL_ALIASES.get(normalized, normalized)

    def _skill_in_text(self, skill: str, text: str, text_tokens: Set[str]) -> bool:
        if " " in skill or "." in skill:
            return skill in text
        return skill in text_tokens or skill in text

    def _extract_required_skills(self, text: str, text_tokens: Set[str]) -> Set[str]:
        required: Set[str] = set()
        for skill in KNOWN_SKILLS:
            if self._skill_in_text(skill, text, text_tokens):
                required.add(skill)
        return required

    def _priority_label(self, score: float) -> str:
        if score >= 0.75:
            return "High Intent Apply"
        if score >= 0.5:
            return "Strong Match"
        if score >= 0.3:
            return "Stretch With Upskilling"
        return "Low Priority"

    def _build_reasoning(self, label: str, matched: Set[str], missing: List[str]) -> str:
        matched_preview = ", ".join(sorted(list(matched))[:5]) or "none"
        missing_preview = ", ".join(missing[:5]) or "none"
        return f"{label}. Matched: {matched_preview}. Missing: {missing_preview}."
