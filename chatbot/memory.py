import json
import tempfile
import threading
from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.utils import timezone


class JSONChatMemory:
    """Per-user JSON journal for bot memory."""

    _lock = threading.Lock()

    def __init__(self, root_dir):
        self.root_dir = Path(root_dir)

    @classmethod
    def from_settings(cls):
        return cls(getattr(settings, "BOT_MEMORY_ROOT", settings.BASE_DIR / "bot_memory"))

    def record_user_question(self, user, question, metadata=None):
        journal = self.load(user)
        turn = {
            "id": uuid4().hex,
            "created_at": timezone.now().isoformat(),
            "user_question": question,
            "assistant_answer": "",
            "metadata": metadata or {},
        }
        journal["history"].append(turn)
        journal["metadata"]["last_question_at"] = turn["created_at"]
        journal["metadata"]["total_questions"] = journal["metadata"].get("total_questions", 0) + 1
        self.save(user, journal)
        return turn["id"]

    def record_assistant_answer(self, user, turn_id, answer, metadata=None):
        journal = self.load(user)
        for turn in reversed(journal["history"]):
            if turn["id"] == turn_id:
                turn["assistant_answer"] = answer
                turn["answered_at"] = timezone.now().isoformat()
                if metadata:
                    turn["metadata"].update(metadata)
                break
        else:
            raise ValueError(f"Unknown chat turn: {turn_id}")

        journal["metadata"]["last_answer_at"] = timezone.now().isoformat()
        self.save(user, journal)

    def history_as_messages(self, user, limit=12):
        journal = self.load(user)
        messages = []
        for turn in journal["history"][-limit:]:
            question = turn.get("user_question", "").strip()
            answer = turn.get("assistant_answer", "").strip()
            if question:
                messages.append({"role": "user", "content": question})
            if answer:
                messages.append({"role": "assistant", "content": answer})
        return messages

    def clear_history(self, user):
        journal = self.load(user)
        created_at = journal.get("metadata", {}).get("created_at", timezone.now().isoformat())
        journal["history"] = []
        journal["metadata"] = {
            "created_at": created_at,
            "schema_version": 1,
            "total_questions": 0,
            "cleared_at": timezone.now().isoformat(),
        }
        self.save(user, journal)
        return journal

    def load(self, user):
        path = self.path_for_user(user)
        if not path.exists():
            return self._empty_journal(user)

        with path.open("r", encoding="utf-8") as file:
            payload = json.load(file)

        payload.setdefault("user", self._user_payload(user))
        payload.setdefault("history", [])
        payload.setdefault("metadata", {})
        return payload

    def save(self, user, payload):
        path = self.path_for_user(user)
        self.root_dir.mkdir(parents=True, exist_ok=True)
        payload["user"] = self._user_payload(user)
        payload.setdefault("history", [])
        payload.setdefault("metadata", {})
        payload["metadata"]["updated_at"] = timezone.now().isoformat()

        with self._lock:
            with tempfile.NamedTemporaryFile(
                "w",
                encoding="utf-8",
                dir=self.root_dir,
                delete=False,
                suffix=".tmp",
            ) as tmp_file:
                json.dump(payload, tmp_file, ensure_ascii=False, indent=2)
                tmp_file.write("\n")
                tmp_path = Path(tmp_file.name)
            tmp_path.replace(path)

    def path_for_user(self, user):
        return self.root_dir / f"user_{user.id}.json"

    def _empty_journal(self, user):
        return {
            "user": self._user_payload(user),
            "history": [],
            "metadata": {
                "created_at": timezone.now().isoformat(),
                "schema_version": 1,
                "total_questions": 0,
            },
        }

    def _user_payload(self, user):
        profile = getattr(user, "profile", None)
        return {
            "id": user.id,
            "username": user.get_username(),
            "email": user.email,
            "profile": {
                "age": getattr(profile, "age", None),
                "profile_image": getattr(getattr(profile, "profile_image", None), "name", ""),
            },
        }
