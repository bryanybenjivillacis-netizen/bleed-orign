import asyncio
import logging
import os

import discord
from discord.ext import commands

from core.config import DISCORD_TOKEN
from core.database import close_pool, init_db

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("bot")

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix=",", intents=intents, help_command=None)


@bot.event
async def on_ready():
    log.info(f"Conectado como {bot.user} ({bot.user.id})")
    synced = await bot.tree.sync()
    log.info(f"{len(synced)} comandos slash sincronizados")


async def load_cogs():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py") and not filename.startswith("_"):
            await bot.load_extension(f"cogs.{filename[:-3]}")
            log.info(f"Cog cargado: {filename}")


async def main():
    await init_db()
    try:
        async with bot:
            await load_cogs()
            await bot.start(DISCORD_TOKEN)
    finally:
        await close_pool()


if __name__ == "__main__":
    asyncio.run(main())
