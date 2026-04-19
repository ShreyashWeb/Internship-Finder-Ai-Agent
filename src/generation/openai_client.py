from __future__ import annotations

from openai import OpenAI


class OpenAITextClient:
    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model
        self.client = OpenAI(api_key=api_key) if api_key else None

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        if not self.client:
            return "[OPENAI_API_KEY missing] Add your key in .env to enable AI-generated artifacts."

        response = self.client.responses.create(
            model=self.model,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.5,
        )
        return response.output_text.strip()
