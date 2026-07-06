import discord
from discord.ext import commands

from core.database import pool
from core.permissions import config_command_check, is_guild_admin


class CommandPermissions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ---------- Permisos por comando ----------
    @commands.group(name="cmdperms", invoke_without_command=True)
    @config_command_check()
    async def cmdperms(self, ctx: commands.Context):
        await ctx.send("Uso: `.cmdperms add <comando> @role`, `.cmdperms remove <comando> @role`, `.cmdperms list <comando>`")

    @cmdperms.command(name="add")
    @config_command_check()
    async def cmdperms_add(self, ctx: commands.Context, command: str, role: discord.Role):
        if self.bot.get_command(command) is None:
            await ctx.send(f"❌ El comando `{command}` no existe.")
            return
        await pool.execute(
            "INSERT INTO command_permissions (guild_id, command, role_id) VALUES ($1, $2, $3) ON CONFLICT DO NOTHING",
            ctx.guild.id,
            command,
            role.id,
        )
        await ctx.send(f"✅ {role.mention} ahora puede usar `.{command}`.")

    @cmdperms.command(name="remove")
    @config_command_check()
    async def cmdperms_remove(self, ctx: commands.Context, command: str, role: discord.Role):
        await pool.execute(
            "DELETE FROM command_permissions WHERE guild_id = $1 AND command = $2 AND role_id = $3",
            ctx.guild.id,
            command,
            role.id,
        )
        await ctx.send(f"❌ {role.mention} ya no puede usar `.{command}` (por este permiso).")

    @cmdperms.command(name="list")
    @config_command_check()
    async def cmdperms_list(self, ctx: commands.Context, command: str):
        rows = await pool.fetch(
            "SELECT role_id FROM command_permissions WHERE guild_id = $1 AND command = $2", ctx.guild.id, command
        )
        if not rows:
            await ctx.send(f"`.{command}` no tiene roles con permiso asignado (solo administradores).")
            return
        roles = "\n".join(f"<@&{row['role_id']}>" for row in rows)
        embed = discord.Embed(title=f"Permisos — .{command}", description=roles, color=discord.Color.orange())
        await ctx.send(embed=embed)

    # ---------- Dar roles por comando ----------
    @commands.group(name="rolecommand", invoke_without_command=True)
    @config_command_check()
    async def rolecommand(self, ctx: commands.Context):
        await ctx.send("Uso: `.rolecommand setup <nombre> @role`, `.rolecommand <nombre> @miembro`, `.rolecommand list`")

    @rolecommand.command(name="setup")
    @config_command_check()
    async def rolecommand_setup(self, ctx: commands.Context, name: str, role: discord.Role):
        await pool.execute(
            "INSERT INTO command_roles (guild_id, command, role_id) VALUES ($1, $2, $3) ON CONFLICT DO NOTHING",
            ctx.guild.id,
            name.lower(),
            role.id,
        )
        await ctx.send(f"✅ Comando `.rolecommand {name}` creado — le dará el rol {role.mention} a quien lo reciba.")

    @rolecommand.command(name="list")
    @config_command_check()
    async def rolecommand_list(self, ctx: commands.Context):
        rows = await pool.fetch("SELECT command, role_id FROM command_roles WHERE guild_id = $1", ctx.guild.id)
        if not rows:
            await ctx.send("No hay comandos de rol configurados.")
            return
        lines = "\n".join(f"`.rolecommand {row['command']}` → <@&{row['role_id']}>" for row in rows)
        embed = discord.Embed(title="Comandos de rol", description=lines, color=discord.Color.teal())
        await ctx.send(embed=embed)

    @rolecommand.command(name="give")
    async def rolecommand_give(self, ctx: commands.Context, name: str, member: discord.Member):
        row = await pool.fetchrow(
            "SELECT role_id FROM command_roles WHERE guild_id = $1 AND command = $2", ctx.guild.id, name.lower()
        )
        if not row:
            await ctx.send(f"❌ No existe el comando de rol `{name}`.")
            return
        allowed = is_guild_admin(ctx.author)
        if not allowed:
            perm_row = await pool.fetchrow(
                "SELECT 1 FROM command_permissions WHERE guild_id = $1 AND command = $2 AND role_id = ANY($3::bigint[])",
                ctx.guild.id,
                f"rolecommand_{name.lower()}",
                [r.id for r in ctx.author.roles],
            )
            allowed = perm_row is not None
        if not allowed:
            await ctx.send("❌ No tienes permiso para usar este comando de rol.")
            return
        role = ctx.guild.get_role(row["role_id"])
        if role is None:
            await ctx.send("❌ El rol configurado ya no existe.")
            return
        await member.add_roles(role, reason=f"rolecommand {name} usado por {ctx.author}")
        await ctx.send(f"✅ {member.mention} ahora tiene el rol {role.mention}.")


async def setup(bot: commands.Bot):
    await bot.add_cog(CommandPermissions(bot))
