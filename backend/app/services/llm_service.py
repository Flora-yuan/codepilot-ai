import os

from openai import OpenAI


DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-chat"


class LLMService:
    """Call DeepSeek through the OpenAI-compatible SDK."""

    def __init__(self) -> None:
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY environment variable is not set")

        self.client = OpenAI(
            api_key=api_key,
            base_url=DEEPSEEK_BASE_URL,
        )

    def ask(self, prompt: str) -> str:
        """
        Send one prompt to DeepSeek and return the answer text.

        The project uses DeepSeek to read retrieved code snippets and explain
        them in natural language.
        """
        response = self.client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a code assistant. Answer only from the code "
                        "context provided by the user."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )

        message = response.choices[0].message.content
        return message or ""
