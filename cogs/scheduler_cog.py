import asyncio
import discord
from discord.ext import commands, tasks
from croniter import croniter
from datetime import datetime, timezone

from db import list_channel_configs, upsert_channel_config

class SchedulerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.running = set()  # cache to avoid double-purging
        self.check_crons.start()

    def cog_unload(self):
        self.check_crons.cancel()

    @tasks.loop(seconds=60)
    async def check_crons(self):
        now = datetime.now(timezone.utc)
        configs = await list_channel_configs()

        for config in configs:
            if not config["enabled"]:
                continue

            channel_id = int(config["channel_id"])
            cron_expr = config["cron_expr"]

            try:
                itr = croniter(cron_expr, now)
                prev = itr.get_prev(datetime)
                # if the prev fire time is within last 60s, trigger
                if (now - prev).total_seconds() < 60:
                    if channel_id in self.running:
                        continue  # avoid duplicate purge

                    self.running.add(channel_id)
                    asyncio.create_task(self.purge_channel(channel_id))
            except Exception as e:
                print(f"[CRON ERROR] Invalid CRON for channel {channel_id}: {cron_expr} – {e}")

    async def purge_channel(self, channel_id: int):
        try:
            channel = self.bot.get_channel(channel_id)
            if not channel:
                print(f"Channel {channel_id} not found.")
                return

            if isinstance(channel, discord.TextChannel):
                await channel.purge(limit=None)
                print(f"Purged all messages in #{channel.name}")
        except Exception as e:
            print(f"Error purging {channel_id}: {e}")
        finally:
            await asyncio.sleep(2)  # optional delay to prevent flapping
            self.running.discard(channel_id)

async def setup(bot):
    await bot.add_cog(SchedulerCog(bot))
