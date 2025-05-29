import os
from dotenv import load_dotenv

load_dotenv()  # reads .env in project root

BOT_PREFIX  = os.getenv("BOT_PREFIX", "!")
TOKEN       = os.getenv("DISCORD_TOKEN")
SUPER_ADMIN = os.getenv("SUPER_ADMIN", "").split(",") if os.getenv("SUPER_ADMIN") else []
ADMIN_ROLES = os.getenv("ADMIN_ROLES", "").split(",") if os.getenv("ADMIN_ROLES") else []

ALLOWED_CHANNELS = [
    name.strip().lower()
    for name in os.getenv("ALLOWED_CHANNELS", "").split(",")
    if name.strip()
]