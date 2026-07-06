import time

import discord
from discord.ext import commands

from core.database import pool
from core.permissions import config_command_check, is_whitelisted

THRESHOLD = 3          # acciones permitidas
WINDOW_SECONDS = 10     # ventana de tiempo para contar las acciones


class AntiNuke(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # tracker en memoria: {guild_id: {user_id: {action: [timestamps]}}}
        self.tracker: dict[int, dict[int, dict[str, list[float]]]] = {}

    # ---------- Config ----------
    @commands.group(name="antinuke", invoke_without_command=True)
    @config_command_check()
    async def antinuke(self, ctx: commands.Context):
        row = await pool.fetchrow("SELECT enabled FROM antinuke_config WHERE guild_id = $1", ctx.guild.id)
        enabled = row["enabled"] if row else False
        estado = "✅ activado" if enabled else "❌ desactivado"
        embed = discord.Embed(title="Anti-Nuke Config", color=discord.Color.blurple())
        embed.add_field(name="Estado", value=estado)
        await ctx.send(embed=embed)

    @antinuke.command(name="enable")
    @config_command_check()
    async def antinuke_enable(self, ctx: commands.Context):
        await pool.execute(
            """INSERT INTO antinuke_config (guild_id, enabled) VALUES ($1, TRUE)
               ON CONFLICT (guild_id) DO UPDATE SET enabled = TRUE""",
            ctx.guild.id,
        )
        await ctx.send("✅ Anti-nuke activado.")

    @antinuke.command(name="disable")
    @config_command_check()
    async def antinuke_disable(self, ctx: commands.Context):
        await pool.execute(
            """INSERT INTO antinuke_config (guild_id, enabled) VALUES ($1, FALSE)
               ON CONFLICT (guild_id) DO UPDATE SET enabled = FALSE""",
            ctx.guild.id,
        )
        await ctx.send("❌ Anti-nuke desactivado.")

    # ---------- Helpers ----------
    async def _is_enabled(self, guild_id: int) -> bool:
        row = await pool.fetchrow("SELECT enabled FROM antinuke_config WHERE guild_id = $1", guild_id)
        return bool(row and row["enabled"])

    async def _get_executor(self, guild: discord.Guild, action: discord.AuditLogAction):
        async for entry in guild.audit_logs(action=action, limit=1):
            if (discord.utils.utcnow() - entry.created_at).total_seconds() < 5:
                return entry.user
        return None

    def _register(self, guild_id: int, user_id: int, action: str) -> bool:
        now = time.monotonic()
        guild_data = self.tracker.setdefault(guild_id, {})
        user_data = guild_data.setdefault(user_id, {})
        timestamps = [t for t in user_data.get(action, []) if now - t < WINDOW_SECONDS]
        timestamps.append(now)
        user_data[action] = timestamps
        return len(timestamps) >= THRESHOLD

    async def _punish(self, guild: discord.Guild, user: discord.abc.User, reason: str):
        member = guild.get_member(user.id)
        if member is None:
            return
        dangerous_perms = ["administrator", "manage_guild", "manage_roles", "manage_channels", "ban_members", "kick_members"]
        roles_to_remove = [
            role for role in member.roles
            if role != guild.default_role and any(getattr(role.permissions, p) for p in dangerous_perms)
        ]
        try:
            if roles_to_remove:
                await member.remove_roles(*roles_to_remove, reason="Anti-nuke: acción sospechosa detectada")
        except discord.Forbidden:
            pass
        try:
            await guild.owner.send(f"🚨 Anti-nuke en **{guild.name}**: se le quitaron roles peligrosos a {member} por {reason}.")
        except (discord.Forbidden, AttributeError):
            pass

    async def _handle_action(self, guild: discord.Guild, action_name: str, audit_action: discord.AuditLogAction):
        if not await self._is_enabled(guild.id):
            return
        executor = await self._get_executor(guild, audit_action)
        if executor is None or executor.bot:
            return
        if await is_whitelisted(guild.id, executor.id):
            return
        if self._register(guild.id, executor.id, action_name):
            await self._punish(guild, executor, action_name)

    # ---------- Listeners ----------
    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        await self._handle_action(channel.guild, "channel_delete", discord.AuditLogAction.channel_delete)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        await self._handle_action(role.guild, "role_delete", discord.AuditLogAction.role_delete)

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        await self._handle_action(guild, "member_ban", discord.AuditLogAction.ban)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        # Detectar si fue un kick (no un ban ni salida voluntaria) via audit log
        await self._handle_action(member.guild, "member_kick", discord.AuditLogAction.kick)


async def setup(bot: commands.Bot):
    await bot.add_cog(AntiNuke(bot))
