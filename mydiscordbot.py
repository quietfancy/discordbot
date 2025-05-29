import asyncio
import logging
import os
import discord

import db

from discord.ext import commands
from config import BOT_PREFIX, TOKEN, ALLOWED_CHANNELS

# set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# initialize bot
intents = discord.Intents.default()
intents.message_content = True  # if you need message content
bot = commands.Bot(command_prefix=BOT_PREFIX, intents=intents)

# dynamically load all cogs in ./cogs/
@bot.event
async def on_ready():
    logger.info(f"Logged in as {bot.user} (ID: {bot.user.id})")
    logger.info("------")

async def load_cogs():
    for filename in os.listdir("./cogs"):
        if not filename.endswith(".py") or filename == "__init__.py":
            continue
        cog = f"cogs.{filename[:-3]}"
        try:
            await bot.load_extension(cog)
            logger.info(f"Loaded cog: {cog}")
        except Exception as e:
            logger.exception(f"Failed to load cog {cog}: {e}")

@bot.check
async def globally_block_channels(ctx):
    if not ALLOWED_CHANNELS:
        return True  # allow all if not restricted

    if isinstance(ctx.channel, discord.TextChannel):
        return ctx.channel.name.lower() in ALLOWED_CHANNELS

    return False  # block if not in guild text channel

# graceful startup
async def main():
    db.setup_database()

    async with bot:
        await load_cogs()
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
