import discord
from discord.ext import commands

from core.database import pool


async def is_admin_whitelisted(guild_id: int, user_id: int) -> bool:
    row = await pool.fetchrow(
        "SELECT 1 FROM admin_whitelist WHERE guild_id = $1 AND user_id = $2", guild_id, user_id
    )
    return row is not None


async def is_whitelisted(guild_id: int, user_id: int) -> bool:
    if await is_admin_whitelisted(guild_id, user_id):
        return True
    row = await pool.fetchrow(
        "SELECT 1 FROM whitelist WHERE guild_id = $1 AND user_id = $2", guild_id, user_id
    )
    return row is not None


def is_guild_admin(member: discord.Member) -> bool:
    return member.guild.owner_id == member.id or member.guild_permissions.administrator


async def has_role_permission(guild_id: int, table: str, command: str, member: discord.Member) -> bool:
    """Revisa si alguno de los roles del miembro tiene permiso asignado para ese comando."""
    role_ids = [role.id for role in member.roles]
    if not role_ids:
        return False
    row = await pool.fetchrow(
        f"SELECT 1 FROM {table} WHERE guild_id = $1 AND command = $2 AND role_id = ANY($3::bigint[])",
        guild_id,
        command,
        role_ids,
    )
    return row is not None


def config_command_check():
    """Solo el dueño del servidor, administradores, o admin-whitelist pueden usar comandos de configuración."""

    async def predicate(ctx: commands.Context) -> bool:
        if is_guild_admin(ctx.author):
            return True
        return await is_admin_whitelisted(ctx.guild.id, ctx.author.id)

    return commands.check(predicate)
