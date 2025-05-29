import os
import sqlite3
import asyncio

DB_PATH = os.path.join('data', "bot.db")
db_lock = asyncio.Lock()

def setup_database():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("""
    CREATE TABLE IF NOT EXISTS channel_configs (
        channel_id TEXT PRIMARY KEY,
        channel_name TEXT NOT NULL,
        cron_expr TEXT NOT NULL,
        last_run TEXT NOT NULL,
        enabled INTEGER NOT NULL CHECK (enabled IN (0,1))
    );
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS admin_users (
            user_id TEXT PRIMARY KEY
        );
        """)
    conn.commit()
    conn.close()

async def run_db_query(fn):
    async with db_lock:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        try:
            result = fn(conn)
            conn.commit()
            return result
        finally:
            conn.close()

# ADMIN USERS
async def add_admin_user(user_id: str):
    await run_db_query(lambda conn: conn.execute(
        "INSERT INTO admin_users (user_id) VALUES (?) ON CONFLICT(user_id) DO NOTHING",
        (user_id,)
    ))

async def remove_admin_user(user_id: str):
    await run_db_query(lambda conn: conn.execute(
        "DELETE FROM admin_users WHERE user_id = ?",
        (user_id,)
    ))

async def get_admin_users():
    return await run_db_query(lambda conn: conn.execute(
        "SELECT user_id FROM admin_users"
    ).fetchall())

async def is_db_admin(user_id: str) -> bool:
    result = await run_db_query(lambda conn: conn.execute(
        "SELECT 1 FROM admin_users WHERE user_id = ?", (user_id,)
    ).fetchone())
    return result is not None


# CHANNEL CONFIGS
async def upsert_channel_config(channel_id: str, channel_name: str, cron_expr: str, enabled: bool):
    def q(conn):
        conn.execute("""
            INSERT INTO channel_configs (channel_id, channel_name, cron_expr, enabled)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(channel_id) DO UPDATE SET
                channel_name = excluded.channel_name,
                cron_expr = excluded.cron_expr,
                enabled = excluded.enabled;
        """, (channel_id, channel_name, cron_expr, int(enabled)))
    await run_db_query(q)

async def delete_channel_config(channel_id: str):
    await run_db_query(lambda conn: conn.execute("DELETE FROM channel_configs WHERE channel_id = ?", (channel_id,)))

async def get_channel_config(channel_id: str):
    return await run_db_query(lambda conn: conn.execute("SELECT * FROM channel_configs WHERE channel_id = ?", (channel_id,)).fetchone())

async def list_channel_configs():
    return await run_db_query(lambda conn: conn.execute("SELECT * FROM channel_configs").fetchall())
