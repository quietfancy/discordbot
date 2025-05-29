from croniter import croniter
from discord.ext import commands
import discord
import db
from datetime import datetime

# Helper to get next runs from a CRON expression
def get_next_runs(cron_expr: str, count: int = 5):
    now = datetime.now()
    try:
        itr = croniter(cron_expr, now)
        return [itr.get_next(datetime).strftime('%Y-%m-%d %H:%M:%S') for _ in range(count)]
    except Exception:
        return ["⚠️ Unable to parse CRON expression"]

class ChannelConfigCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="channelconfig", invoke_without_command=True)
    async def channelconfig(self, ctx):
        """Manage channel purge schedules."""
        if not await db.is_admin(ctx):
            return await ctx.send("You are not authorized to use this command.")
        await ctx.send("Available subcommands: set, unset, enable, disable, get, list")

    @channelconfig.command(name="set")
    async def set_config(self, ctx, channel: discord.TextChannel, *, cron_expr: str):
        """Create or update a purge schedule for a channel."""
        if not await db.is_admin(ctx):
            return await ctx.send("You are not authorized to use this command.")
        clean_cron = cron_expr.replace('`', '').strip()
        if not croniter.is_valid(clean_cron):
            return await ctx.send("❌ Invalid CRON expression.")
        await db.upsert_channel_config(str(channel.id), channel.name, clean_cron, True)
        await ctx.send(f"✅ Config for channel `{channel.name}` set and enabled.")

    @channelconfig.command(name="unset")
    async def unset_config(self, ctx, channel: discord.TextChannel):
        """Remove purge schedule for a channel."""
        if not await db.is_admin(ctx):
            return await ctx.send("You are not authorized to use this command.")
        await db.delete_channel_config(str(channel.id))
        await ctx.send(f"🗑️ Config for channel `{channel.name}` removed.")

    @channelconfig.command(name="enable")
    async def enable_config(self, ctx, channel: discord.TextChannel):
        """Enable an existing channel purge config."""
        if not await db.is_admin(ctx):
            return await ctx.send("You are not authorized to use this command.")
        existing = await db.get_channel_config(str(channel.id))
        if not existing:
            return await ctx.send("❌ No config exists to enable.")
        await db.upsert_channel_config(str(channel.id), channel.name, existing["cron_expr"], True)
        await ctx.send(f"✅ Config for `{channel.name}` is now enabled.")

    @channelconfig.command(name="disable")
    async def disable_config(self, ctx, channel: discord.TextChannel):
        """Disable an existing channel purge config."""
        if not await db.is_admin(ctx):
            return await ctx.send("You are not authorized to use this command.")
        existing = await db.get_channel_config(str(channel.id))
        if not existing:
            return await ctx.send("❌ No config exists to disable.")
        await db.upsert_channel_config(str(channel.id), channel.name, existing["cron_expr"], False)
        await ctx.send(f"⛔ Config for `{channel.name}` is now disabled.")

    @channelconfig.command(name="get")
    async def get_config(self, ctx, channel: discord.TextChannel):
        """View config for a specific channel."""
        if not await db.is_admin(ctx):
            return await ctx.send("You are not authorized to use this command.")

        config = await db.get_channel_config(str(channel.id))
        if not config:
            return await ctx.send("ℹ️ No config found for this channel.")

        next_runs = get_next_runs(config["cron_expr"])
        run_lines = "\n".join(f"• {dt}" for dt in next_runs)

        await ctx.send(
            f"**Channel:** {config['channel_name']}\n"
            f"**CRON:** `{config['cron_expr']}`\n"
            f"**Enabled:** {'✅' if config['enabled'] else '⛔'}\n"
            f"**Next Runs:**\n{run_lines}"
        )

    @channelconfig.command(name="list")
    async def list_configs(self, ctx):
        """List all configured channels with purge schedules."""
        if not await db.is_admin(ctx):
            return await ctx.send("You are not authorized to use this command.")
        configs = await db.list_channel_configs()
        if not configs:
            return await ctx.send("ℹ️ No channel configurations found.")
        msg = "\n".join(
            f"- **{row['channel_name']}** → CRON: `{row['cron_expr']}`, Enabled: {'✅' if row['enabled'] else '⛔'}"
            for row in configs
        )
        await ctx.send(f"**Configured Channels:**\n{msg}")

async def setup(bot):
    await bot.add_cog(ChannelConfigCog(bot))
