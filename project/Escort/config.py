import os
from dotenv import load_dotenv

load_dotenv()

ESCORT_BOT_TOKEN = os.getenv("ESCORT_BOT_TOKEN", "").strip()
ESCORT_DATA_FILE = os.getenv("ESCORT_DATA_FILE", "escort_data.json").strip()
ESCORT_LOG_CHAT_ID = os.getenv("ESCORT_LOG_CHAT_ID", "").strip()
ESCORT_ADMIN_IDS = [
    int(item)
    for item in os.getenv("ESCORT_ADMIN_IDS", "").split(",")
    if item.strip().isdigit()
]
SUPPORT_BOT_TOKEN = os.getenv("SUPPORT_BOT_TOKEN", "").strip()
SUPPORT_LOG_CHAT_ID = os.getenv("SUPPORT_LOG_CHAT_ID", "").strip()
SUPPORT_DATA_FILE = os.getenv("SUPPORT_DATA_FILE", "support_data.json").strip()
