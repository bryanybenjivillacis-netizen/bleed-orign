import discord
from discord.ext import commands

from core.database import pool
from core.permissions import config_command_check

VALID_PERMISSIONS = [
    "administrator", "manage_guild", "manage_roles", "manage_channels",
    "manage_messages", "kick_members", "ban_members", "manage_nicknames",
    "mute_members", "moderate_members",
]


async def has_fake_permission(guild_id: int, member: discord.Member, permission: str) -> bool:
    role_ids = [role.id for role in member.roles]
    if not role_ids:
        return False
    row = await pool.fetchrow(
        "SELECT 1 FROM fake_permissions WHERE guild_id = $1 AND role_id = ANY($2::bigint[]) AND permission = $3",
        guild_id,
        role_ids,
        permission,
    )
    return row is not None


class FakePermissions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.group(name="fakeperms", invoke_without_command=True)
    @config_command_check()
    async def fakeperms(self, ctx: commands.Context):
        await ctx.send(
            "Uso: `.fakeperms add @role <permiso>`, `.fakeperms remove @role <permiso>`, `.fakeperms list @role`\n"
            f"Permisos válidos: {', '.join(VALID_PERMISSIONS)}"
        )

    @fakeperms.command(name="add")
    @config_command_check()
    async def fakeperms_add(self, ctx: commands.Context, role: discord.Role, permission: str):
        permission = permission.lower()
        if permission not in VALID_PERMISSIONS:
            await ctx.send(f"❌ Permiso inválido. Usa uno de: {', '.join(VALID_PERMISSIONS)}")
            return
        await pool.execute(
            "INSERT INTO fake_permissions (guild_id, role_id, permission) VALUES ($1, $2, $3) ON CONFLICT DO NOTHING",
            ctx.guild.id,
            role.id,
            permission,
        )
        await ctx.send(f"✅ {role.mention} ahora tiene el fake permission `{permission}`.")

    @fakeperms.command(name="remove")
    @config_command_check()
    async def fakeperms_remove(self, ctx: commands.Context, role: discord.Role, permission: str):
        await pool.execute(
            "DELETE FROM fake_permissions WHERE guild_id = $1 AND role_id = $2 AND permission = $3",
            ctx.guild.id,
            role.id,
            permission.lower(),
        )
        await ctx.send(f"❌ Fake permission `{permission}` eliminado de {role.mention}.")

    @fakeperms.command(name="list")
    @config_command_check()
    async def fakeperms_list(self, ctx: commands.Context, role: discord.Role):
        rows = await pool.fetch(
            "SELECT permission FROM fake_permissions WHERE guild_id = $1 AND role_id = $2", ctx.guild.id, role.id
        )
        if not rows:
            await ctx.send(f"{role.mention} no tiene fake permissions.")
            return
        perms = "\n".join(row["permission"] for row in rows)
        embed = discord.Embed(title=f"Fake Permissions — {role.name}", description=perms, color=discord.Color.gold())
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(FakePermissions(bot))
