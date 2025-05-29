from discord.ext import commands
from discord import ui, ButtonStyle, Interaction
import discord
import db

class PurgeConfirmView(ui.View):
    def __init__(self, ctx, target_user, target_channel):
        super().__init__(timeout=5)
        self.ctx = ctx
        self.target_user = target_user
        self.target_channel = target_channel

        self.message = None
        self.confirmed = False

    @ui.button(label="✅ Confirm", style=ButtonStyle.danger)
    async def confirm(self, interaction: Interaction, button: ui.Button):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message("❌ You cannot confirm this action.", ephemeral=True)

        self.confirmed = True

        await interaction.response.defer()
        
        await self.clear_view(interaction)
        await self.ctx.send(f"🧹 Starting purge of messages from {self.target_user.mention}...", delete_after=5)

        deleted_total = 0
        user_id = self.target_user.id

        channels = [self.target_channel] if self.target_channel else [
            c for c in self.ctx.guild.text_channels
            if c.permissions_for(self.ctx.guild.me).read_message_history and c.permissions_for(self.ctx.guild.me).manage_messages
        ]

        for channel in channels:
            try:
                purged = await channel.purge(check=lambda m: m.author.id == user_id, limit=None)
                deleted_total += len(purged)
            except discord.Forbidden:
                await self.ctx.send(f"⚠️ Missing permissions in {channel.mention}", delete_after=8)
            except Exception as e:
                await self.ctx.send(f"⚠️ Error purging {channel.mention}: {e}", delete_after=8)

        await self.ctx.send(f"✅ Finished purging {deleted_total} messages from {self.target_user.mention}.")
        self.stop()

    @ui.button(label="❌ Cancel", style=ButtonStyle.secondary)
    async def cancel(self, interaction: Interaction, button: ui.Button):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message("❌ You cannot cancel this action.", ephemeral=True)

        await self.clear_view(interaction)

        await interaction.response.send_message("❌ Purge canceled.", ephemeral=True)
        self.stop()

    async def on_timeout(self):
        if self.confirmed:
            return

        try:
            await self.message.edit(content="⏱️ Timed out — no action taken.", view=None)
        except Exception:
            pass

        self.stop()

    async def clear_view(self, interaction: Interaction):
        await interaction.message.edit(view=None)


class PurgeUserCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="purgeuser")
    async def purge_user(self, ctx, user: discord.User, channel: discord.TextChannel = None):
        """Confirm and purge all messages from a user in the specified or all channels."""
        if not await db.is_admin(ctx):
            return await ctx.send("❌ You are not authorized to use this command.")

        if not ctx.guild:
            return await ctx.send("❌ This command must be used in a server.")

        label = f"{channel.mention}" if channel else "*all channels*"
        view = PurgeConfirmView(ctx, user, channel)
        view.message = await ctx.send(
            f"⚠️ Are you sure you want to purge **all messages** from {user.mention} in {label}?",
            view=view
        )

async def setup(bot):
    await bot.add_cog(PurgeUserCog(bot))
