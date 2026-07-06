import discord
from discord.ext import commands

from core.database import pool
from core.permissions import config_command_check


class TicketPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎫 Abrir Ticket", style=discord.ButtonStyle.blurple, custom_id="ticket_open_button")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        row = await pool.fetchrow("SELECT category_id, support_role_id FROM ticket_config WHERE guild_id = $1", guild.id)
        if not row:
            await interaction.response.send_message("❌ El sistema de tickets no está configurado.", ephemeral=True)
            return

        existing = await pool.fetchrow(
            "SELECT channel_id FROM tickets WHERE guild_id = $1 AND user_id = $2 AND open = TRUE",
            guild.id,
            interaction.user.id,
        )
        if existing:
            await interaction.response.send_message(f"❌ Ya tienes un ticket abierto: <#{existing['channel_id']}>", ephemeral=True)
            return

        category = guild.get_channel(row["category_id"]) if row["category_id"] else None
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        }
        support_role = guild.get_role(row["support_role_id"]) if row["support_role_id"] else None
        if support_role:
            overwrites[support_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        channel = await guild.create_text_channel(
            name=f"ticket-{interaction.user.name}", category=category, overwrites=overwrites
        )
        await pool.execute(
            "INSERT INTO tickets (channel_id, guild_id, user_id) VALUES ($1, $2, $3)",
            channel.id,
            guild.id,
            interaction.user.id,
        )
        await channel.send(
            f"🎫 Ticket de {interaction.user.mention}. Usa `.close` para cerrarlo.",
            allowed_mentions=discord.AllowedMentions(users=True),
        )
        await interaction.response.send_message(f"✅ Ticket creado: {channel.mention}", ephemeral=True)


class Tickets(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        bot.add_view(TicketPanelView())

    @commands.group(name="ticket", invoke_without_command=True)
    @config_command_check()
    async def ticket(self, ctx: commands.Context):
        await ctx.send("Uso: `.ticket setup #categoria @rol_soporte #canal_panel`")

    @ticket.command(name="setup")
    @config_command_check()
    async def ticket_setup(
        self,
        ctx: commands.Context,
        category: discord.CategoryChannel,
        support_role: discord.Role,
        panel_channel: discord.TextChannel,
    ):
        await pool.execute(
            """INSERT INTO ticket_config (guild_id, category_id, support_role_id, panel_channel_id)
               VALUES ($1, $2, $3, $4)
               ON CONFLICT (guild_id) DO UPDATE SET category_id = $2, support_role_id = $3, panel_channel_id = $4""",
            ctx.guild.id,
            category.id,
            support_role.id,
            panel_channel.id,
        )
        embed = discord.Embed(
            title="Soporte",
            description="Haz clic en el botón para abrir un ticket.",
            color=discord.Color.blurple(),
        )
        await panel_channel.send(embed=embed, view=TicketPanelView())
        await ctx.send(f"✅ Panel de tickets enviado en {panel_channel.mention}.")

    @commands.command(name="close")
    async def close(self, ctx: commands.Context):
        row = await pool.fetchrow(
            "SELECT user_id FROM tickets WHERE channel_id = $1 AND open = TRUE", ctx.channel.id
        )
        if not row:
            await ctx.send("❌ Este canal no es un ticket abierto.")
            return
        await pool.execute("UPDATE tickets SET open = FALSE WHERE channel_id = $1", ctx.channel.id)
        await ctx.send("🔒 Cerrando ticket en 5 segundos...")
        await ctx.channel.delete(delay=5, reason=f"Ticket cerrado por {ctx.author}")


async def setup(bot: commands.Bot):
    await bot.add_cog(Tickets(bot))
