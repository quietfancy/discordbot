from .database import (
    setup_database,
    add_admin_user,
    remove_admin_user,
    get_admin_users,
    is_db_admin,
    upsert_channel_config,
    delete_channel_config,
    get_channel_config,
    list_channel_configs
)

from config import SUPER_ADMIN, ADMIN_ROLES, ALLOWED_CHANNELS

async def is_admin(ctx) -> bool:
    # Super Admins by user ID (string match)
    if str(ctx.author.id) in SUPER_ADMIN:
        return True

    # Role-based check
    if hasattr(ctx.author, "roles"):
        user_roles = {role.name for role in ctx.author.roles}
        return any(role in ADMIN_ROLES for role in user_roles)

    return False

def is_allowed_channel_name(channel_name: str) -> bool:
    return not ALLOWED_CHANNELS or channel_name.lower() in ALLOWED_CHANNELS

__all__ = [
    "setup_database",
    "add_admin_user",
    "remove_admin_user",
    "get_admin_users",
    "is_db_admin",
    "upsert_channel_config",
    "delete_channel_config",
    "get_channel_config",
    "list_channel_configs",
    "is_admin"
]
