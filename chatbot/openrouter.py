from dataclasses import dataclass, field

import requests
from django.conf import settings


DEFAULT_OPENROUTER_MODEL = "openai/gpt-4o-mini"
OPENROUTER_CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_SYSTEM_PROMPT = (
    "Ты — официальный ИИ-консультант компании Travel X. Мы занимаемся космическим туризмом. "
    "Наш опыт: более 10 лет на рынке, проведено 50+ успешных суборбитальных полетов. "
    "Страховка: каждый пассажир застрахован на $10 млн, страховка покрывает все риски от старта до посадки. "
    "Отвечай вежливо, кратко и только по теме космического туризма. "
    "Если не знаешь ответ — предлагай связаться с менеджером."
)


class OpenRouterConfigurationError(RuntimeError):
    pass


class OpenRouterAPIError(RuntimeError):
    pass


@dataclass(frozen=True)
class OpenRouterChatResult:
    content: str
    model: str
    response_id: str = ""
    usage: dict = field(default_factory=dict)
    raw: dict = field(default_factory=dict)


class OpenRouterClient:
    def __init__(
        self,
        api_key=None,
        model=None,
        session=None,
        timeout=None,
        site_url=None,
        app_title=None,
    ):
        self.api_key = api_key or getattr(settings, "OPENROUTER_API_KEY", "")
        self.model = model or getattr(settings, "OPENROUTER_MODEL", DEFAULT_OPENROUTER_MODEL)
        self.session = session or requests.Session()
        self.timeout = timeout or getattr(settings, "OPENROUTER_TIMEOUT", 45)
        self.site_url = site_url or getattr(settings, "OPENROUTER_SITE_URL", "")
        self.app_title = app_title or getattr(settings, "OPENROUTER_APP_TITLE", "Travel X")

        if not self.api_key:
            raise OpenRouterConfigurationError("OPENROUTER_API_KEY is not configured.")

    def chat(self, messages, user_id=None, temperature=0.7, max_tokens=900):
        payload = {
            "model": self.model,
            "messages": self._with_system_prompt(messages),
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if user_id is not None:
            payload["user"] = str(user_id)

        response = self.session.post(
            OPENROUTER_CHAT_URL,
            headers=self._headers(),
            json=payload,
            timeout=self.timeout,
        )

        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            raise OpenRouterAPIError(str(exc)) from exc

        data = response.json()
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise OpenRouterAPIError("OpenRouter returned an unexpected response shape.") from exc

        return OpenRouterChatResult(
            content=content,
            model=data.get("model", self.model),
            response_id=data.get("id", ""),
            usage=data.get("usage", {}),
            raw=data,
        )

    def _headers(self):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if self.site_url:
            headers["HTTP-Referer"] = self.site_url
        if self.app_title:
            headers["X-Title"] = self.app_title
        return headers

    def _with_system_prompt(self, messages):
        conversation = [message for message in messages if message.get("role") != "system"]
        return [{"role": "system", "content": OPENROUTER_SYSTEM_PROMPT}, *conversation]
