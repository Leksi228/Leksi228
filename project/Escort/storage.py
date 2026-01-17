import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional

from .config import ESCORT_DATA_FILE


@dataclass
class EscortProfile:
    user_id: int
    username: str = ""
    balance_rub: int = 0
    orders_count: int = 0
    worker_id: Optional[int] = None
    city: str = ""


@dataclass
class EscortData:
    profiles: Dict[str, Dict]
    models: List[Dict]
    settings: Dict[str, str]


DEFAULT_SETTINGS = {
    # тексты
    "title": "Emerans Club",
    "welcome_text": "Привет! Для подбора моделей напишите ваш город.",
    "menu_text": "Главное меню:",
    "support_username": "@EmeransClubSupport_bot",
    "channel_link": "",

    # реквизиты
    "card_number": "",

    # подписи кнопок
    "btn_models": "Модели",
    "btn_profile": "Профиль",
    "btn_support": "Поддержка",
    "btn_info": "Информация",
    "btn_city": "Сменить город",
    "btn_admin": "⚙️ Админка",
    "btn_back": "⬅️ Назад",

    # секции главного меню (что показывать)
    "menu_sections": ["models", "profile", "support", "info", "city"],
}



def ensure_settings(data: "EscortData") -> None:
    """Make sure all required settings exist (migration-safe)."""
    for k, v in DEFAULT_SETTINGS.items():
        if k not in data.settings:
            data.settings[k] = v  # type: ignore[assignment]


def load_data() -> EscortData:
    path = Path(ESCORT_DATA_FILE)
    if path.exists():
        with path.open("r", encoding="utf-8") as handle:
            raw = json.load(handle)
    else:
        raw = {"profiles": {}, "models": [], "settings": {}}
    data = EscortData(
        profiles=raw.get("profiles", {}),
        models=raw.get("models", []),
        settings=raw.get("settings", {}),
    )
    ensure_settings(data)
    # normalize menu_sections if someone stored it as a string
    if isinstance(data.settings.get("menu_sections"), str):
        data.settings["menu_sections"] = [
            s.strip() for s in str(data.settings.get("menu_sections")).split(",") if s.strip()
        ]
    return data


def save_data(data: EscortData) -> None:
    path = Path(ESCORT_DATA_FILE)
    ensure_settings(data)
    payload = {"profiles": data.profiles, "models": data.models, "settings": data.settings}
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


def ensure_profile(data: EscortData, user_id: int, username: str) -> EscortProfile:
    existing = data.profiles.get(str(user_id))
    if existing:
        profile = EscortProfile(**existing)
        if username:
            profile.username = username
        data.profiles[str(user_id)] = asdict(profile)
        return profile
    profile = EscortProfile(user_id=user_id, username=username)
    data.profiles[str(user_id)] = asdict(profile)
    return profile


def update_profile(data: EscortData, profile: EscortProfile) -> None:
    data.profiles[str(profile.user_id)] = asdict(profile)
