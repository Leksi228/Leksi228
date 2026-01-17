from __future__ import annotations

from typing import Dict, List, Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


# ----------------------------
# Helpers
# ----------------------------


def _label(settings: Dict, key: str, default: str) -> str:
    val = settings.get(key)
    return str(val) if val else default


def _sections(settings: Dict) -> List[str]:
    raw = settings.get("menu_sections", [])
    if isinstance(raw, list):
        return [str(x) for x in raw]
    if isinstance(raw, str):
        return [s.strip() for s in raw.split(",") if s.strip()]
    return []


# ----------------------------
# User keyboards
# ----------------------------


def main_menu_keyboard(settings: Dict) -> InlineKeyboardMarkup:
    """Main menu based on settings."""

    sections = set(_sections(settings))

    btn_models = _label(settings, "btn_models", "Модели")
    btn_profile = _label(settings, "btn_profile", "Профиль")
    btn_support = _label(settings, "btn_support", "Поддержка")
    btn_info = _label(settings, "btn_info", "Информация")
    btn_city = _label(settings, "btn_city", "Сменить город")
    btn_inline = _label(settings, "btn_inline_search", "Найти модель")

    keyboard: List[List[InlineKeyboardButton]] = []

    row1: List[InlineKeyboardButton] = []
    if "models" in sections:
        row1.append(InlineKeyboardButton(btn_models, callback_data="menu:models"))
    if "profile" in sections:
        row1.append(InlineKeyboardButton(btn_profile, callback_data="menu:profile"))
    if row1:
        keyboard.append(row1)

    row2: List[InlineKeyboardButton] = []
    if "inline_search" in sections:
        row2.append(InlineKeyboardButton(btn_inline, switch_inline_query_current_chat=""))
    if "support" in sections:
        row2.append(InlineKeyboardButton(btn_support, callback_data="menu:support"))
    if row2:
        keyboard.append(row2)

    row3: List[InlineKeyboardButton] = []
    if "info" in sections:
        row3.append(InlineKeyboardButton(btn_info, callback_data="menu:info"))
    if "city" in sections:
        row3.append(InlineKeyboardButton(btn_city, callback_data="menu:city"))
    if row3:
        keyboard.append(row3)

    if not keyboard:
        keyboard = [[InlineKeyboardButton("Меню", callback_data="menu:models")]]

    return InlineKeyboardMarkup(keyboard)


def profile_keyboard(settings: Dict) -> InlineKeyboardMarkup:
    back = _label(settings, "btn_back", "⬅️ Назад")
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Пополнить баланс", callback_data="profile:topup")],
            [InlineKeyboardButton("Избранное", callback_data="profile:favorites")],
            [InlineKeyboardButton(back, callback_data="profile:back")],
        ]
    )


def topup_keyboard(settings: Dict) -> InlineKeyboardMarkup:
    back = _label(settings, "btn_back", "⬅️ Назад")
    return InlineKeyboardMarkup([[InlineKeyboardButton(back, callback_data="topup:back")]])


def payment_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Банковская карта", callback_data="pay:card"),
                InlineKeyboardButton("Наличными", callback_data="pay:cash"),
            ],
            [InlineKeyboardButton("⬅️ Назад", callback_data="topup:back")],
        ]
    )


def models_list_keyboard(
    settings: Dict,
    models: List[tuple[int, Dict]],
    page: int = 0,
    per_page: int = 8,
) -> InlineKeyboardMarkup:
    back = _label(settings, "btn_back", "⬅️ Назад")

    start = page * per_page
    chunk = models[start : start + per_page]

    keyboard: List[List[InlineKeyboardButton]] = []
    for idx, model in chunk:
        name = str(model.get("name") or "Модель")
        keyboard.append([InlineKeyboardButton(name, callback_data=f"model:{idx}")])

    nav: List[InlineKeyboardButton] = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️", callback_data=f"models:page:{page-1}"))
    if start + per_page < len(models):
        nav.append(InlineKeyboardButton("➡️", callback_data=f"models:page:{page+1}"))
    if nav:
        keyboard.append(nav)

    keyboard.append([InlineKeyboardButton(back, callback_data="models:back")])
    return InlineKeyboardMarkup(keyboard)


def model_detail_keyboard(settings: Dict, link: Optional[str] = None) -> InlineKeyboardMarkup:
    back = _label(settings, "btn_back", "⬅️ Назад")
    keyboard: List[List[InlineKeyboardButton]] = []
    if link and (link.startswith("http://") or link.startswith("https://") or link.startswith("t.me/")):
        url = link
        if url.startswith("t.me/"):
            url = "https://" + url
        keyboard.append([InlineKeyboardButton("🔗 Перейти", url=url)])
    keyboard.append([InlineKeyboardButton(back, callback_data="model:back")])
    return InlineKeyboardMarkup(keyboard)


# ----------------------------
# Admin keyboards
# ----------------------------


def admin_main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("📦 Модели", callback_data="admin:models"),
                InlineKeyboardButton("🎨 Дизайн", callback_data="admin:design"),
            ],
            [InlineKeyboardButton("❌ Закрыть", callback_data="admin:close")],
        ]
    )


def admin_models_keyboard(models: List[Dict], page: int = 0, per_page: int = 8) -> InlineKeyboardMarkup:
    start = page * per_page
    items = list(enumerate(models))[start : start + per_page]

    keyboard: List[List[InlineKeyboardButton]] = []
    for idx, model in items:
        name = str(model.get("name") or f"Модель #{idx}")
        keyboard.append([InlineKeyboardButton(f"✏️ {name}", callback_data=f"admin:model:{idx}")])

    nav: List[InlineKeyboardButton] = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️", callback_data=f"admin:models_page:{page-1}"))
    if start + per_page < len(models):
        nav.append(InlineKeyboardButton("➡️", callback_data=f"admin:models_page:{page+1}"))
    if nav:
        keyboard.append(nav)

    keyboard.append([InlineKeyboardButton("➕ Добавить модель", callback_data="admin:model_add")])
    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="admin:back")])
    return InlineKeyboardMarkup(keyboard)


def admin_model_actions_keyboard(model_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Имя", callback_data=f"admin:edit:{model_id}:name"),
                InlineKeyboardButton("Цена", callback_data=f"admin:edit:{model_id}:price"),
            ],
            [
                InlineKeyboardButton("Ссылка", callback_data=f"admin:edit:{model_id}:link"),
                InlineKeyboardButton("Города", callback_data=f"admin:edit:{model_id}:cities"),
            ],
            [InlineKeyboardButton("Описание", callback_data=f"admin:edit:{model_id}:desc")],
            [InlineKeyboardButton("🗑 Удалить", callback_data=f"admin:delete:{model_id}")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="admin:models")],
        ]
    )


def admin_design_keyboard(settings: Dict) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Название проекта", callback_data="admin:design_set:title")],
            [InlineKeyboardButton("Ссылка на канал", callback_data="admin:design_set:channel_link")],
            [InlineKeyboardButton("Текст приветствия", callback_data="admin:design_set:welcome_text")],
            [InlineKeyboardButton("Текст меню", callback_data="admin:design_set:menu_text")],
            [InlineKeyboardButton("Юзернейм поддержки", callback_data="admin:design_set:support_username")],
            [InlineKeyboardButton("Подписи кнопок", callback_data="admin:design_buttons")],
            [InlineKeyboardButton("Секция главного меню", callback_data="admin:design_sections")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="admin:back")],
        ]
    )


def admin_buttons_keyboard(settings: Dict) -> InlineKeyboardMarkup:
    items = [
        ("btn_models", "Кнопка: Модели"),
        ("btn_profile", "Кнопка: Профиль"),
        ("btn_support", "Кнопка: Поддержка"),
        ("btn_info", "Кнопка: Информация"),
        ("btn_city", "Кнопка: Сменить город"),
        ("btn_back", "Кнопка: Назад"),
        ("btn_inline_search", "Кнопка: Инлайн поиск"),
    ]

    keyboard: List[List[InlineKeyboardButton]] = []
    for key, title in items:
        current = str(settings.get(key) or "")
        suffix = f" — <{current}>" if current else ""
        keyboard.append([InlineKeyboardButton(f"{title}{suffix}", callback_data=f"admin:btn_set:{key}")])

    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="admin:design")])
    return InlineKeyboardMarkup(keyboard)


def admin_sections_keyboard(settings: Dict) -> InlineKeyboardMarkup:
    current = set(_sections(settings))

    def mark(enabled: bool) -> str:
        return "✅" if enabled else "❌"

    items = [
        ("models", "Модели"),
        ("profile", "Профиль"),
        ("support", "Поддержка"),
        ("info", "Информация"),
        ("city", "Сменить город"),
        ("inline_search", "Инлайн поиск"),
    ]

    keyboard: List[List[InlineKeyboardButton]] = []
    for key, title in items:
        enabled = key in current
        keyboard.append(
            [InlineKeyboardButton(f"{mark(enabled)} {title}", callback_data=f"admin:toggle_section:{key}")]
        )

    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="admin:design")])
    return InlineKeyboardMarkup(keyboard)
