import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict

from .config import SUPPORT_DATA_FILE


@dataclass
class SupportData:
    user_to_topic: Dict[str, int]
    topic_to_user: Dict[str, int]


def load_data() -> SupportData:
    path = Path(SUPPORT_DATA_FILE)
    if path.exists():
        with path.open("r", encoding="utf-8") as handle:
            raw = json.load(handle)
    else:
        raw = {"user_to_topic": {}, "topic_to_user": {}}
    return SupportData(
        user_to_topic=raw.get("user_to_topic", {}),
        topic_to_user=raw.get("topic_to_user", {}),
    )


def save_data(data: SupportData) -> None:
    path = Path(SUPPORT_DATA_FILE)
    payload = {
        "user_to_topic": data.user_to_topic,
        "topic_to_user": data.topic_to_user,
    }
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


def ensure_topic(data: SupportData, user_id: int, topic_id: int) -> None:
    data.user_to_topic[str(user_id)] = topic_id
    data.topic_to_user[str(topic_id)] = user_id
