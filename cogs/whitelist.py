import discord
from discord.ext import commands

from core.database import pool
from core.permissions import config_command_check, is_guild_admin


class Whitelist(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ---------- Whitelist ----------
    @commands.group(name="whitelist", invoke_without_command=True)
    @config_command_check()
    async def whitelist(self, ctx: commands.Context):
        await ctx.send("Uso: `.whitelist add @user`, `.whitelist remove @user`, `.whitelist list`")

    @whitelist.command(name="add")
    @config_command_check()
    async def whitelist_dda(self, ctx: commands.Context, member: discord.Member):
        await pool.execute(
            "INSERT INTO whitelist (guild_id, user_id) VALUES ($1, $2) ON CONFLICT DO NOTHING",
            ctx.guild.id,
            member.id,
        )
        await ctx.send(f"✅ {member.mention} añadido a la whitelist.")

    @whitelist.command(name="remove")
    @config_command_check()
    async def whitelist_remove(self, ctx: commands.Context, member: discord.Member):
        await pool.execute(
            "DELETE FROM whitelist WHERE guild_id = $1 AND user_id = $2", ctx.guild.id, member.id
        )
        await ctx.send(f"❌ {member.mention} eliminado de la whitelist.")

    @whitelist.command(name="list")
    @config_command_check()
    async def whitelist_list(self, ctx: commands.Context):
        rows = await pool.fetch("SELECT user_id FROM whitelist WHERE guild_id = $1", ctx.guild.id)
        if not rows:
            await ctx.send("La whitelist está vacía.")
            return
        mentions = "\n".join(f"<@{row['user_id']}>" for row in rows)
        embed = discord.Embed(title="Whitelist", description=mentions, color=discord.Color.blurple())
        await ctx.send(embed=embed)

    # ---------- Admin Whitelist ----------
    @commands.group(name="adminwhitelist", invoke_without_command=True)
    async def adminwhitelist(self, ctx: commands.Context):
        await ctx.send("Uso: `.adminwhitelist add @user`, `.adminwhitelist remove @user`, `.adminwhitelist list`")

    @adminwhitelist.command(name="add")
    async def adminwhitelist_add(self, ctx: commands.Context, member: discord.Member):
        if not is_guild_admin(ctx.author):
            await ctx.send("❌ Solo el dueño del servidor o un administrador puede usar esto.")
            return
        await pool.execute(
            "INSERT INTO admin_whitelist (guild_id, user_id) VALUES ($1, $2) ON CONFLICT DO NOTHING",
            ctx.guild.id,
            member.id,
        )
        await ctx.send(f"✅ {member.mention} añadido a la admin whitelist.")

    @adminwhitelist.command(name="remove")
    async def adminwhitelist_remove(self, ctx: commands.Context, member: discord.Member):
        if not is_guild_admin(ctx.author):
            await ctx.send("❌ Solo el dueño del servidor o un administrador puede usar esto.")
            return
        await pool.execute(
            "DELETE FROM admin_whitelist WHERE guild_id = $1 AND user_id = $2", ctx.guild.id, member.id
        )
        await ctx.send(f"❌ {member.mention} eliminado de la admin whitelist.")

    @adminwhitelist.command(name="list")
    async def adminwhitelist_list(self, ctx: commands.Context):
        rows = await pool.fetch("SELECT user_id FROM admin_whitelist WHERE guild_id = $1", ctx.guild.id)
        if not rows:
            await ctx.send("La admin whitelist está vacía.")
            return
        mentions = "\n".join(f"<@{row['user_id']}>" for row in rows)
        embed = discord.Embed(title="Admin Whitelist", description=mentions, color=discord.Color.blurple())
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Whitelist(bot))
