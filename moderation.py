import discord
from discord.ext import commands
import random
import asyncio
from discord.ui import View, Button
from discord import Interaction

ROLE_ID_RECRUIT = 1303660480480673812     # Recruit role
ROLE_ID_OFFICIAL_MEMBER = 1346557689303662633  # Official Member role
ROLE_ID_AWAITING_TRYOUT = 1303662669626081300  # Awaiting Tryout role
ROLE_ID_UNOFFICIAL_PERSONNEL = 1303661603006447736
ROLE_ID_LOA = 1313895372828967054  # LOA role
ROLE_ID_LOA_CHECKER = 1359948180745093161  # LOA Checker role

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def test(self, ctx):
        """A simple test command that replies with 'Test Ran'"""
        await ctx.send("Test Ran")

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def lock(self, ctx):
        """Locks the current channel."""
        overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = False
        await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        await ctx.send("🔒 This channel has been locked.")

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def unlock(self, ctx):
        """Unlocks the current channel."""
        overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = None  # Resets to default permissions
        await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        await ctx.send("🔓 This channel has been unlocked.")

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def slowmode(self, ctx, seconds: int):
        """Sets slowmode for the current channel."""
        await ctx.channel.edit(slowmode_delay=seconds)
        await ctx.send(f"🐢 Slowmode set to {seconds} seconds.")

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        """Kicks a member from the server."""
        await member.kick(reason=reason)
        await ctx.send(f"👢 {member.mention} has been kicked. Reason: {reason}")

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        """Bans a member from the server."""
        await member.ban(reason=reason)
        await ctx.send(f"🔨 {member.mention} has been banned. Reason: {reason}")

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, *, member_name: str):
        """Unbans a member from the server."""
        banned_users = await ctx.guild.bans()
        for ban_entry in banned_users:
            user = ban_entry.user
            if user.name == member_name:
                await ctx.guild.unban(user)
                await ctx.send(f"✅ {user.mention} has been unbanned.")
                return
        await ctx.send(f"❌ No banned user found with the name `{member_name}`.")

    @commands.command()
    @commands.has_permissions(moderate_members=True)
    async def timeout(self, ctx, member: discord.Member, minutes: int, *, reason: str = "No reason provided"):
        """Times out a member for a specified number of minutes."""
        duration = discord.utils.utcnow() + discord.timedelta(minutes=minutes)
        await member.timeout(duration, reason=reason)
        await ctx.send(f"⏳ {member.mention} has been timed out for {minutes} minutes. Reason: {reason}")

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def mute(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        """Mutes a member by adding a Muted role."""
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if not muted_role:
            muted_role = await ctx.guild.create_role(name="Muted")
            for channel in ctx.guild.channels:
                await channel.set_permissions(muted_role, send_messages=False, speak=False)
        await member.add_roles(muted_role, reason=reason)
        await ctx.send(f"🔇 {member.mention} has been muted. Reason: {reason}")

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def unmute(self, ctx, member: discord.Member):
        """Unmutes a member by removing the Muted role."""
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if muted_role in member.roles:
            await member.remove_roles(muted_role)
            await ctx.send(f"🔊 {member.mention} has been unmuted.")
        else:
            await ctx.send(f"❌ {member.mention} is not muted.")

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, number: int):
        """Clears a specified number of messages."""
        if number < 1 or number > 100:
            await ctx.send("❌ Please specify a number between 1 and 100.")
            return

        if number <= 10:
            # Clear messages directly if the number is 10 or less
            await ctx.channel.purge(limit=number + 1)  # +1 to include the command message
            await ctx.send(f"✅ Cleared {number} messages.", delete_after=5)
        else:
            # Ask for confirmation if the number is greater than 10
            embed = discord.Embed(
                title="Confirmation Required",
                description=f"Are you sure you want to clear {number} messages?",
                color=discord.Color.orange()
            )

            # Create buttons for confirmation
            class ConfirmView(View):
                def __init__(self):
                    super().__init__()
                    self.value = None

                @discord.ui.button(label="YES", style=discord.ButtonStyle.green)
                async def confirm(self, interaction: Interaction, button: Button):
                    if interaction.user == ctx.author:
                        self.value = True
                        self.stop()
                        await interaction.response.defer()
                    else:
                        await interaction.response.send_message("You cannot confirm this action.", ephemeral=True)

                @discord.ui.button(label="NO", style=discord.ButtonStyle.red)
                async def cancel(self, interaction: Interaction, button: Button):
                    if interaction.user == ctx.author:
                        self.value = False
                        self.stop()
                        await interaction.response.defer()
                    else:
                        await interaction.response.send_message("You cannot cancel this action.", ephemeral=True)

            view = ConfirmView()
            confirmation_message = await ctx.send(embed=embed, view=view)

            # Wait for the user's response
            await view.wait()

            if view.value is None:
                await confirmation_message.edit(content="❌ Confirmation timed out.", embed=None, view=None)
            elif view.value:
                await ctx.channel.purge(limit=number + 1)  # +1 to include the command message
                await ctx.send(f"✅ Cleared {number} messages.", delete_after=5)
            else:
                await confirmation_message.edit(content="❌ Clear command canceled.", embed=None, view=None)

    @commands.command()
    async def loa(self, ctx, reason: str, time_in_days: int):
        """Request a Leave of Absence (LOA)."""
        # Check if the user has the Official Member role
        official_member_role = ctx.guild.get_role(ROLE_ID_OFFICIAL_MEMBER)
        if official_member_role not in ctx.author.roles:
            await ctx.send("❌ You must have the Official Member role to request an LOA.")
            return

        # Get the specific user by ID
        admin_id = 920314437179674694  # Replace with the specific user ID
        try:
            admin = await self.bot.fetch_user(admin_id)  # Fetch the user directly
        except discord.NotFound:
            await ctx.send("❌ The designated administrator could not be found.")
            return

        # Send a DM to the designated administrator
        embed = discord.Embed(
            title="LOA Request",
            description=f"**Requester:** {ctx.author.mention}\n"
                        f"**Reason:** {reason}\n"
                        f"**Time (days):** {time_in_days}",
            color=discord.Color.blue()
        )
        embed.set_footer(text="React with ✅ to approve or ❌ to decline.")

        try:
            message = await admin.send(embed=embed)
        except discord.Forbidden:
            await ctx.send(f"❌ Could not DM the designated administrator ({admin.mention}).")
            return

        # Add reactions to the message
        await message.add_reaction("✅")
        await message.add_reaction("❌")

        # Wait for the administrator's reaction
        def check(reaction, user):
            return (
                user == admin
                and str(reaction.emoji) in ["✅", "❌"]
                and reaction.message.id == message.id
            )

        try:
            reaction, user = await self.bot.wait_for("reaction_add", timeout=86400.0, check=check)
        except asyncio.TimeoutError:
            await admin.send("❌ You did not respond to the LOA request in time.")
            return

        if str(reaction.emoji) == "✅":
            # Approve the LOA
            loa_role = ctx.guild.get_role(ROLE_ID_LOA)
            await ctx.author.add_roles(loa_role)
            await ctx.author.send(f"✅ Your LOA request has been approved for {time_in_days} days.")
            await admin.send("✅ You have approved the LOA request.")
        elif str(reaction.emoji) == "❌":
            # Decline the LOA
            await admin.send("❌ Please reply with the reason for declining the LOA request.")

            def message_check(m):
                return m.author == admin and m.channel == message.channel

            try:
                decline_reason = await self.bot.wait_for("message", timeout=86400.0, check=message_check)
            except asyncio.TimeoutError:
                await admin.send("❌ You did not provide a reason for declining the LOA request in time.")
                return

            await ctx.author.send(f"❌ Your LOA request has been declined.\n**Reason:** {decline_reason.content}")
            await admin.send("❌ You have declined the LOA request.")

async def setup(bot):
    await bot.add_cog(Moderation(bot))