from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def _format_amount(amount: float | int) -> str:
    if isinstance(amount, float) and amount.is_integer():
        return str(int(amount))
    return str(amount)


def main_menu_keyboard(is_admin: bool) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton("Мой профиль", callback_data="menu:profile"),
            InlineKeyboardButton("Направления", callback_data="menu:tracks"),
        ],
        [
            InlineKeyboardButton("Кураторы", callback_data="menu:mentors"),
            InlineKeyboardButton("О проекте", callback_data="menu:about"),
        ],
    ]
    if is_admin:
        rows.append([InlineKeyboardButton("⚙️ Админка", callback_data="menu:admin")])
    return InlineKeyboardMarkup(rows)


def apply_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("Подать заявку", callback_data="apply:start")]]
    )


def origin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Реклама", callback_data="origin:ad"),
                InlineKeyboardButton("Тикток", callback_data="origin:tiktok"),
            ]
        ]
    )


def time_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("4ч", callback_data="time:4h"),
                InlineKeyboardButton("8ч и более", callback_data="time:8h+"),
            ]
        ]
    )


def admin_decision_keyboard(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "Принять", callback_data=f"admin:accept:{user_id}"
                ),
                InlineKeyboardButton(
                    "Отклонить", callback_data=f"admin:reject:{user_id}"
                ),
            ]
        ]
    )


def directions_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("💃 Escort", callback_data="direction:escort"),
                InlineKeyboardButton("📈 Trade", callback_data="direction:trade"),
            ],
            [
                InlineKeyboardButton("🖼️ NFT", callback_data="direction:nft"),
                InlineKeyboardButton("⬅️ Назад", callback_data="direction:back"),
            ],
        ]
    )


def admin_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🎨 Дизайн", callback_data="admin:design"),
                InlineKeyboardButton("🧑‍🏫 Добавить наставника", callback_data="admin:mentor_add"),
            ],
            [
                InlineKeyboardButton("📊 Профиты", callback_data="admin:profits"),
                InlineKeyboardButton("💳 Выдать баланс", callback_data="admin:balance_grant"),
            ],
            [
                InlineKeyboardButton("📣 Канал профитов", callback_data="admin:profit_channel"),
                InlineKeyboardButton("🔗 Ссылки", callback_data="admin:links"),
            ],
            [
                InlineKeyboardButton("⬅️ Назад", callback_data="admin:back"),
            ],
        ]
    )


def design_sections_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Главное меню", callback_data="design:main"),
                InlineKeyboardButton("Направления", callback_data="design:directions"),
            ],
            [
                InlineKeyboardButton("Кураторы", callback_data="design:mentors"),
                InlineKeyboardButton("О проекте", callback_data="design:about"),
            ],
            [
                InlineKeyboardButton("Мой профиль", callback_data="design:profile"),
            ],
            [InlineKeyboardButton("⬅️ Назад", callback_data="design:back")],
        ]
    )


def links_sections_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("ℹ️ INFO", callback_data="links:info"),
                InlineKeyboardButton("📘 Мануалы", callback_data="links:manuals"),
            ],
            [
                InlineKeyboardButton("💎 Профиты", callback_data="links:profits"),
                InlineKeyboardButton("💬 Чат", callback_data="links:chat"),
            ],
            [InlineKeyboardButton("⬅️ Назад", callback_data="links:back")],
        ]
    )


def about_links_keyboard(links: dict[str, str]) -> InlineKeyboardMarkup:
    rows = []
    if links.get("info"):
        rows.append([InlineKeyboardButton("ℹ️ INFO", url=links["info"])])
    if links.get("manuals"):
        rows.append([InlineKeyboardButton("📘 Мануалы", url=links["manuals"])])
    if links.get("profits"):
        rows.append([InlineKeyboardButton("💎 Профиты", url=links["profits"])])
    if links.get("chat"):
        rows.append([InlineKeyboardButton("💬 Чат", url=links["chat"])])
    rows.append([InlineKeyboardButton("⬅️ Назад", callback_data="about:back")])
    return InlineKeyboardMarkup(rows) if rows else InlineKeyboardMarkup([])


def profits_service_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("💃 Escort", callback_data="profit:service:escort"),
                InlineKeyboardButton("📈 Trade", callback_data="profit:service:trade"),
            ],
            [
                InlineKeyboardButton("🖼️ NFT", callback_data="profit:service:nft"),
                InlineKeyboardButton("🎯 Прямик", callback_data="profit:service:direct"),
            ],
        ]
    )


def profits_curator_keyboard(mentors: list[int]) -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(
            f"🧑‍🏫 {mentor_id}", callback_data=f"profit:mentor:{mentor_id}"
        )
        for mentor_id in mentors
    ]
    rows = [buttons[i : i + 2] for i in range(0, len(buttons), 2)]
    rows.append(
        [InlineKeyboardButton("🙅 Без куратора", callback_data="profit:mentor:none")]
    )
    return InlineKeyboardMarkup(rows)


def profits_multiplier_keyboard() -> InlineKeyboardMarkup:
    rows = []
    for idx in range(1, 11, 2):
        row = [
            InlineKeyboardButton(f"х{idx}", callback_data=f"profit:multiplier:{idx}"),
            InlineKeyboardButton(
                f"х{idx + 1}", callback_data=f"profit:multiplier:{idx + 1}"
            ),
        ]
        rows.append(row)
    return InlineKeyboardMarkup(rows)


def profits_rate_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("80%", callback_data="profit:rate:80"),
                InlineKeyboardButton("70%", callback_data="profit:rate:70"),
            ],
            [
                InlineKeyboardButton("65%", callback_data="profit:rate:65"),
                InlineKeyboardButton("100%", callback_data="profit:rate:100"),
            ],
        ]
    )


def profile_keyboard(show_nickname_in_profits: bool) -> InlineKeyboardMarkup:
    profits_label = "Вкл" if show_nickname_in_profits else "Выкл"
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("✏️ Никнейм", callback_data="profile:nickname"),
                InlineKeyboardButton("📝 Описание", callback_data="profile:description"),
            ],
            [
                InlineKeyboardButton("👛 Мой кошелек", callback_data="profile:wallet"),
                InlineKeyboardButton(
                    f"📈 Профиты: {profits_label}",
                    callback_data="profile:profits_toggle",
                ),
            ],
            [InlineKeyboardButton("⬅️ Назад", callback_data="profile:back")],
        ]
    )


def wallet_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("💸 Вывод", callback_data="wallet:withdraw"),
                InlineKeyboardButton(
                    "📜 История транзакций", callback_data="wallet:history"
                ),
            ],
            [InlineKeyboardButton("⬅️ Назад", callback_data="wallet:back")],
        ]
    )


def withdraw_request_keyboard(user_id: int, amount: float) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ Взять в обработку",
                    callback_data=f"withdraw:take:{user_id}:{_format_amount(amount)}",
                )
            ]
        ]
    )
