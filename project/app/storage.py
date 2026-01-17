import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.config import DATA_FILE


@dataclass
class UserProfile:
    user_id: int
    nickname: Optional[str] = None
    description: Optional[str] = None
    status: str = "обычный"
    show_nickname_in_profits: bool = True
    first_seen: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    balance_rub: int = 0
    profit_count: int = 0
    profit_total_rub: int = 0
    profit_history: List[Dict[str, Any]] = field(default_factory=list)
    payout_rate: int = 0


@dataclass
class BotData:
    approved_users: List[int]
    applications: Dict[str, Dict[str, Any]]
    profiles: Dict[str, Dict[str, Any]]
    mentors: List[int]
    banners: Dict[str, str]
    profit_channel_id: Optional[int]
    links: Dict[str, str]
    profit_count: int
    profit_total_rub: int


def load_data() -> BotData:
    path = Path(DATA_FILE)
    if path.exists():
        with path.open("r", encoding="utf-8") as handle:
            raw = json.load(handle)
    else:
        raw = {
            "approved_users": [],
            "applications": {},
            "profiles": {},
            "mentors": [],
            "banners": {},
            "profit_channel_id": None,
            "links": {},
            "profit_count": 0,
            "profit_total_rub": 0,
        }
    return BotData(
        approved_users=raw.get("approved_users", []),
        applications=raw.get("applications", {}),
        profiles=raw.get("profiles", {}),
        mentors=raw.get("mentors", []),
        banners=raw.get("banners", {}),
        profit_channel_id=raw.get("profit_channel_id"),
        links=raw.get("links", {}),
        profit_count=raw.get("profit_count", 0),
        profit_total_rub=raw.get("profit_total_rub", 0),
    )


def save_data(data: BotData) -> None:
    payload = {
        "approved_users": data.approved_users,
        "applications": data.applications,
        "profiles": data.profiles,
        "mentors": data.mentors,
        "banners": data.banners,
        "profit_channel_id": data.profit_channel_id,
        "links": data.links,
        "profit_count": data.profit_count,
        "profit_total_rub": data.profit_total_rub,
    }
    path = Path(DATA_FILE)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


def ensure_profile(data: BotData, user_id: int) -> UserProfile:
    profile = data.profiles.get(str(user_id))
    if profile:
        default_profile = asdict(UserProfile(user_id=user_id))
        default_profile.update(profile)
        return UserProfile(**default_profile)
    new_profile = UserProfile(user_id=user_id)
    data.profiles[str(user_id)] = asdict(new_profile)
    return new_profile


def update_profile(data: BotData, profile: UserProfile) -> None:
    data.profiles[str(profile.user_id)] = asdict(profile)
