import discord
from discord.ext import commands

from core.database import pool
from core.permissions import config_command_check


class VoiceMaster(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ---------- Config ----------
    @commands.group(name="voicemaster", invoke_without_command=True)
    @config_command_check()
    async def voicemaster(self, ctx: commands.Context):
        await ctx.send("Uso: `.voicemaster setup #canal-de-voz`")

    @voicemaster.command(name="setup")
    @config_command_check()
    async def voicemaster_setup(self, ctx: commands.Context, channel: discord.VoiceChannel):
        await pool.execute(
            """INSERT INTO voicemaster_config (guild_id, join_channel_id, category_id) VALUES ($1, $2, $3)
               ON CONFLICT (guild_id) DO UPDATE SET join_channel_id = $2, category_id = $3""",
            ctx.guild.id,
            channel.id,
            channel.category_id,
        )
        await ctx.send(f"✅ {channel.mention} configurado como canal 'Join to Create'.")

    # ---------- Crear / borrar canales temporales ----------
    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        row = await pool.fetchrow(
            "SELECT join_channel_id, category_id FROM voicemaster_config WHERE guild_id = $1", member.guild.id
        )
        if row and after.channel and after.channel.id == row["join_channel_id"]:
            category = member.guild.get_channel(row["category_id"]) if row["category_id"] else after.channel.category
            new_channel = await member.guild.create_voice_channel(
                name=f"Canal de {member.display_name}", category=category
            )
            await pool.execute(
                "INSERT INTO voicemaster_channels (channel_id, guild_id, owner_id) VALUES ($1, $2, $3)",
                new_channel.id,
                member.guild.id,
                member.id,
            )
            await member.move_to(new_channel)

        if before.channel:
            owned = await pool.fetchrow(
                "SELECT owner_id FROM voicemaster_channels WHERE channel_id = $1", before.channel.id
            )
            if owned and len(before.channel.members) == 0:
                await pool.execute("DELETE FROM voicemaster_channels WHERE channel_id = $1", before.channel.id)
                await before.channel.delete(reason="Canal de voicemaster vacío")

    # ---------- Comandos de gestión (solo el dueño del canal) ----------
    async def _get_owned_channel(self, ctx: commands.Context) -> discord.VoiceChannel | None:
        if ctx.author.voice is None or ctx.author.voice.channel is None:
            await ctx.send("❌ No estás en un canal de voz.")
            return None
        row = await pool.fetchrow(
            "SELECT owner_id FROM voicemaster_channels WHERE channel_id = $1", ctx.author.voice.channel.id
        )
        if not row or row["owner_id"] != ctx.author.id:
            await ctx.send("❌ No eres el dueño de este canal.")
            return None
        return ctx.author.voice.channel

    @commands.command(name="lock")
    async def lock(self, ctx: commands.Context):
        channel = await self._get_owned_channel(ctx)
        if channel is None:
            return
        await channel.set_permissions(ctx.guild.default_role, connect=False)
        await ctx.send("🔒 Canal bloqueado.")

    @commands.command(name="unlock")
    async def unlock(self, ctx: commands.Context):
        channel = await self._get_owned_channel(ctx)
        if channel is None:
            return
        await channel.set_permissions(ctx.guild.default_role, connect=True)
        await ctx.send("🔓 Canal desbloqueado.")

    @commands.command(name="rename")
    async def rename(self, ctx: commands.Context, *, name: str):
        channel = await self._get_owned_channel(ctx)
        if channel is None:
            return
        await channel.edit(name=name)
        await ctx.send(f"✅ Canal renombrado a **{name}**.")

    @commands.command(name="limit")
    async def limit(self, ctx: commands.Context, amount: int):
        channel = await self._get_owned_channel(ctx)
        if channel is None:
            return
        await channel.edit(user_limit=amount)
        await ctx.send(f"✅ Límite de usuarios establecido en {amount}.")

    @commands.command(name="permit")
    async def permit(self, ctx: commands.Context, member: discord.Member):
        channel = await self._get_owned_channel(ctx)
        if channel is None:
            return
        await channel.set_permissions(member, connect=True)
        await ctx.send(f"✅ {member.mention} tiene permiso para entrar.")

    @commands.command(name="vckick")
    async def vckick(self, ctx: commands.Context, member: discord.Member):
        channel = await self._get_owned_channel(ctx)
        if channel is None:
            return
        if member.voice and member.voice.channel and member.voice.channel.id == channel.id:
            await member.move_to(None)
        await ctx.send(f"✅ {member.mention} fue expulsado del canal.")


async def setup(bot: commands.Bot):
    await bot.add_cog(VoiceMaster(bot))
