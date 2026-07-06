from discord.ext import commands

from core.database import pool


class Core(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="ping")
    async def ping(self, ctx: commands.Context):
        db_status = "conectada" if pool is not None else "no conectada"
        await ctx.send(f"🏓 Pong! Latencia: {round(self.bot.latency * 1000)}ms | Base de datos: {db_status}")


async def setup(bot: commands.Bot):
    await bot.add_cog(Core(bot))
