import datetime

import discord
from discord.ext import commands

from core.database import pool
from cogs.fakeperms import has_fake_permission


async def can_moderate(ctx: commands.Context, permission: str) -> bool:
    if getattr(ctx.author.guild_permissions, permission, False):
        return True
    return await has_fake_permission(ctx.guild.id, ctx.author, permission)


async def log_case(guild_id: int, user_id: int, moderator_id: int, action: str, reason: str | None):
    await pool.execute(
        "INSERT INTO moderation_cases (guild_id, user_id, moderator_id, action, reason) VALUES ($1, $2, $3, $4, $5)",
        guild_id,
        user_id,
        moderator_id,
        action,
        reason,
    )


class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="ban")
    async def ban(self, ctx: commands.Context, member: discord.Member, *, reason: str = "Sin razón"):
        if not await can_moderate(ctx, "ban_members"):
            await ctx.send("❌ No tienes permiso para banear.")
            return
        await member.ban(reason=reason)
        await log_case(ctx.guild.id, member.id, ctx.author.id, "ban", reason)
        await ctx.send(f"🔨 {member} baneado. Razón: {reason}")

    @commands.command(name="unban")
    async def unban(self, ctx: commands.Context, user_id: int, *, reason: str = "Sin razón"):
        if not await can_moderate(ctx, "ban_members"):
            await ctx.send("❌ No tienes permiso para desbanear.")
            return
        user = await self.bot.fetch_user(user_id)
        await ctx.guild.unban(user, reason=reason)
        await log_case(ctx.guild.id, user_id, ctx.author.id, "unban", reason)
        await ctx.send(f"✅ {user} desbaneado.")

    @commands.command(name="kick")
    async def kick(self, ctx: commands.Context, member: discord.Member, *, reason: str = "Sin razón"):
        if not await can_moderate(ctx, "kick_members"):
            await ctx.send("❌ No tienes permiso para expulsar.")
            return
        await member.kick(reason=reason)
        await log_case(ctx.guild.id, member.id, ctx.author.id, "kick", reason)
        await ctx.send(f"👢 {member} expulsado. Razón: {reason}")

    @commands.command(name="mute")
    async def mute(self, ctx: commands.Context, member: discord.Member, minutes: int, *, reason: str = "Sin razón"):
        if not await can_moderate(ctx, "moderate_members"):
            await ctx.send("❌ No tienes permiso para mutear.")
            return
        until = discord.utils.utcnow() + datetime.timedelta(minutes=minutes)
        await member.timeout(until, reason=reason)
        await log_case(ctx.guild.id, member.id, ctx.author.id, "mute", reason)
        await ctx.send(f"🔇 {member} muteado por {minutes} minutos. Razón: {reason}")

    @commands.command(name="unmute")
    async def unmute(self, ctx: commands.Context, member: discord.Member):
        if not await can_moderate(ctx, "moderate_members"):
            await ctx.send("❌ No tienes permiso para desmutear.")
            return
        await member.timeout(None)
        await log_case(ctx.guild.id, member.id, ctx.author.id, "unmute", None)
        await ctx.send(f"🔊 {member} desmuteado.")

    @commands.command(name="warn")
    async def warn(self, ctx: commands.Context, member: discord.Member, *, reason: str = "Sin razón"):
        if not await can_moderate(ctx, "moderate_members"):
            await ctx.send("❌ No tienes permiso para advertir.")
            return
        await log_case(ctx.guild.id, member.id, ctx.author.id, "warn", reason)
        await ctx.send(f"⚠️ {member} advertido. Razón: {reason}")

    @commands.command(name="warnings")
    async def warnings(self, ctx: commands.Context, member: discord.Member):
        rows = await pool.fetch(
            "SELECT id, reason, created_at FROM moderation_cases WHERE guild_id = $1 AND user_id = $2 AND action = 'warn' ORDER BY id",
            ctx.guild.id,
            member.id,
        )
        if not rows:
            await ctx.send(f"{member} no tiene advertencias.")
            return
        lines = "\n".join(f"`#{r['id']}` — {r['reason']} ({r['created_at'].strftime('%Y-%m-%d')})" for r in rows)
        embed = discord.Embed(title=f"Advertencias — {member}", description=lines, color=discord.Color.red())
        await ctx.send(embed=embed)

    @commands.command(name="purge")
    async def purge(self, ctx: commands.Context, amount: int):
        if not await can_moderate(ctx, "manage_messages"):
            await ctx.send("❌ No tienes permiso para borrar mensajes.")
            return
        deleted = await ctx.channel.purge(limit=amount + 1)
        msg = await ctx.send(f"🧹 {len(deleted) - 1} mensajes borrados.")
        await msg.delete(delay=3)


async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))
