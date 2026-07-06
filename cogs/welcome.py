import discord
from discord.ext import commands

from core.database import pool
from core.permissions import config_command_check

PLACEHOLDERS_HELP = "Puedes usar `{user}` (menciona al miembro), `{server}` (nombre del servidor) y `{count}` (total de miembros)."


class Welcome(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.group(name="welcome", invoke_without_command=True)
    @config_command_check()
    async def welcome(self, ctx: commands.Context):
        row = await pool.fetchrow("SELECT channel_id, message FROM welcome_config WHERE guild_id = $1", ctx.guild.id)
        if not row or not row["channel_id"]:
            await ctx.send("El welcome no está configurado. Usa `.welcome channel #canal` y `.welcome message <texto>`.")
            return
        embed = discord.Embed(title="Welcome Config", color=discord.Color.green())
        embed.add_field(name="Canal", value=f"<#{row['channel_id']}>", inline=False)
        embed.add_field(name="Mensaje", value=row["message"] or "(sin mensaje)", inline=False)
        await ctx.send(embed=embed)

    @welcome.command(name="channel")
    @config_command_check()
    async def welcome_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        await pool.execute(
            """INSERT INTO welcome_config (guild_id, channel_id) VALUES ($1, $2)
               ON CONFLICT (guild_id) DO UPDATE SET channel_id = $2""",
            ctx.guild.id,
            channel.id,
        )
        await ctx.send(f"✅ Canal de bienvenida configurado en {channel.mention}.")

    @welcome.command(name="message")
    @config_command_check()
    async def welcome_message(self, ctx: commands.Context, *, text: str):
        await pool.execute(
            """INSERT INTO welcome_config (guild_id, message) VALUES ($1, $2)
               ON CONFLICT (guild_id) DO UPDATE SET message = $2""",
            ctx.guild.id,
            text,
        )
        await ctx.send(f"✅ Mensaje de bienvenida actualizado. {PLACEHOLDERS_HELP}")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        row = await pool.fetchrow(
            "SELECT channel_id, message FROM welcome_config WHERE guild_id = $1", member.guild.id
        )
        if not row or not row["channel_id"]:
            return
        channel = member.guild.get_channel(row["channel_id"])
        if channel is None:
            return
        text = row["message"] or "Bienvenido {user} a {server}!"
        text = text.replace("{user}", member.mention).replace("{server}", member.guild.name).replace(
            "{count}", str(member.guild.member_count)
        )
        await channel.send(text)


async def setup(bot: commands.Bot):
    await bot.add_cog(Welcome(bot))
