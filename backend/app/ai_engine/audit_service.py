import json
import os
from datetime import datetime
from typing import Any


class AuditService:
    def __init__(self, storage_path: str | None = None):
        self.storage_path = storage_path or os.path.join(os.getcwd(), "ai_audit_log.json")
        self._ensure_storage()

    def _ensure_storage(self) -> None:
        if not os.path.exists(self.storage_path):
            with open(self.storage_path, "w", encoding="utf-8") as file:
                json.dump([], file)

    def record_event(self, event_type: str, user_id: str | None, details: dict[str, Any]) -> None:
        entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'event_type': event_type,
            'user_id': user_id,
            'details': details
        }
        with open(self.storage_path, "r+", encoding="utf-8") as file:
            data = json.load(file)
            data.append(entry)
            file.seek(0)
            json.dump(data, file, indent=2, ensure_ascii=False)
            file.truncate()

    def get_audit_log(self, limit: int = 100) -> list[dict[str, Any]]:
        with open(self.storage_path, "r", encoding="utf-8") as file:
            data = json.load(file)
        return data[-limit:]
