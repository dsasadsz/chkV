import json
import tempfile
from pathlib import Path
from unittest.mock import Mock

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from chatbot.memory import JSONChatMemory
from chatbot.openrouter import OPENROUTER_SYSTEM_PROMPT, OpenRouterClient


class JSONChatMemoryTests(TestCase):
    def test_records_each_question_and_returns_history_as_messages(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            memory = JSONChatMemory(Path(tmp_dir))
            user = User.objects.create_user(
                username="traveler",
                email="traveler@example.com",
                password="OrbitPass123!",
            )

            turn_id = memory.record_user_question(
                user=user,
                question="Question about Saturn",
                metadata={"source": "text"},
            )
            memory.record_assistant_answer(user=user, turn_id=turn_id, answer="Saturn answer.")

            journal_path = Path(tmp_dir) / f"user_{user.id}.json"
            payload = json.loads(journal_path.read_text(encoding="utf-8"))

            self.assertEqual(payload["user"]["id"], user.id)
            self.assertEqual(payload["history"][0]["user_question"], "Question about Saturn")
            self.assertEqual(payload["history"][0]["assistant_answer"], "Saturn answer.")
            self.assertEqual(payload["history"][0]["metadata"]["source"], "text")
            self.assertEqual(
                memory.history_as_messages(user=user, limit=4),
                [
                    {"role": "user", "content": "Question about Saturn"},
                    {"role": "assistant", "content": "Saturn answer."},
                ],
            )

    def test_clear_history_keeps_user_payload_and_resets_dialog_turns(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            memory = JSONChatMemory(Path(tmp_dir))
            user = User.objects.create_user(username="orbiter", password="OrbitPass123!")
            turn_id = memory.record_user_question(user=user, question="Old question")
            memory.record_assistant_answer(user=user, turn_id=turn_id, answer="Old answer")

            memory.clear_history(user)
            payload = memory.load(user)

            self.assertEqual(payload["user"]["id"], user.id)
            self.assertEqual(payload["history"], [])
            self.assertEqual(payload["metadata"]["total_questions"], 0)


@override_settings(OPENROUTER_API_KEY="test-key")
class OpenRouterClientTests(TestCase):
    def test_chat_posts_openrouter_payload_and_returns_message_text(self):
        session = Mock()
        response = Mock()
        response.json.return_value = {
            "id": "gen-1",
            "model": "openai/gpt-4o-mini",
            "choices": [{"message": {"content": "Hello, commander."}}],
            "usage": {"total_tokens": 42},
        }
        response.raise_for_status.return_value = None
        session.post.return_value = response
        client = OpenRouterClient(session=session, api_key="test-key")

        result = client.chat(
            messages=[{"role": "user", "content": "Hello"}],
            user_id="user-1",
        )

        self.assertEqual(result.content, "Hello, commander.")
        self.assertEqual(result.model, "openai/gpt-4o-mini")
        session.post.assert_called_once()
        _, kwargs = session.post.call_args
        self.assertEqual(kwargs["json"]["model"], "openai/gpt-4o-mini")
        self.assertEqual(kwargs["json"]["messages"][0], {"role": "system", "content": OPENROUTER_SYSTEM_PROMPT})
        self.assertEqual(kwargs["json"]["messages"][1]["content"], "Hello")
        self.assertEqual(kwargs["json"]["user"], "user-1")
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer test-key")


class ChatPageTests(TestCase):
    def test_opening_chat_page_starts_new_empty_dialog(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            with override_settings(BOT_MEMORY_ROOT=Path(tmp_dir)):
                user = User.objects.create_user(username="pilot", password="OrbitPass123!")
                self.client.login(username="pilot", password="OrbitPass123!")
                memory = JSONChatMemory.from_settings()
                turn_id = memory.record_user_question(user=user, question="Old question")
                memory.record_assistant_answer(user=user, turn_id=turn_id, answer="Old answer")

                response = self.client.get(reverse("chatbot:chat_page"))

                self.assertEqual(response.status_code, 200)
                self.assertEqual(memory.load(user)["history"], [])
                self.assertContains(response, "data-quick-replies")
