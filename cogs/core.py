 import discord
from discord import app_commands
from discord.ext import commands

from core.database import pool


class Core(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="ping", description="Verifica que el bot y la base de datos responden")
    async def ping(self, interaction: discord.Interaction):
        db_status = "conectada" if pool is not None else "no conectada"
        await interaction.response.send_message(
            f"🏓 Pong! Latencia: {round(self.bot.latency * 1000)}ms | Base de datos: {db_status}"
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Core(bot))
