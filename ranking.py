import discord
import asyncio
import json
from discord.ext import commands
from discord.ui import View, Button
from discord import Interaction
from datetime import datetime

# Role IDs
ROLE_ID_RECRUIT = 1303660480480673812     # Recruit role
ROLE_ID_OFFICIAL_MEMBER = 1346557689303662633  # Official Member role
ROLE_ID_AWAITING_TRYOUT = 1303662669626081300  # Awaiting Tryout role
ROLE_ID_UNOFFICIAL_PERSONNEL = 1303661603006447736  # Unofficial Personnel role
ROLE_ID_SENIOR_PERSONNEL = 1303657384216100914  # Senior Personnel role

# Persistent storage for points
POINTS_FILE = "points.json"

# Load points from file
def load_points():
    try:
        with open(POINTS_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Save points to file
def save_points(points):
    with open(POINTS_FILE, "w") as f:
        json.dump(points, f)

class ShiftView(View):
    def __init__(self, bot, user_id, start_time):
        super().__init__(timeout=None)
        self.bot = bot
        self.user_id = user_id
        self.start_time = start_time
        self.paused = False

    async def update_embed(self, interaction):
        elapsed_time = datetime.now() - self.start_time
        minutes = elapsed_time.total_seconds() // 60
        embed = discord.Embed(
            title="Shift Logging",
            description=f"**Elapsed Time:** {int(minutes)} minutes\n"
                        f"**Status:** {'Paused' if self.paused else 'Active'}",
            color=discord.Color.blue()
        )
        await interaction.message.edit(embed=embed, view=self)

    @discord.ui.button(label="Pause", style=discord.ButtonStyle.red)
    async def pause(self, interaction: Interaction, button: Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("You cannot control this shift.", ephemeral=True)
            return
        self.paused = True
        await self.update_embed(interaction)

    @discord.ui.button(label="Resume", style=discord.ButtonStyle.green)
    async def resume(self, interaction: Interaction, button: Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("You cannot control this shift.", ephemeral=True)
            return
        self.paused = False
        await self.update_embed(interaction)

    @discord.ui.button(label="Stop", style=discord.ButtonStyle.gray)
    async def stop(self, interaction: Interaction, button: Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("You cannot control this shift.", ephemeral=True)
            return
        for child in self.children:
            child.disabled = True  # Disable all buttons
        await interaction.message.edit(view=self)
        await interaction.response.send_message(
            "✅ Shift stopped. Remember to store all recordings of your shifts, as you may be asked for them at any time.",
            ephemeral=True
        )
        self.stop()

class Ranking(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_shifts = {}

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def rank(self, ctx, action: str = None, member: discord.Member = None):
        """Ranks a member using: !rank entree @user"""
        if action != "entree" or member is None:
            await ctx.send("Usage: `!rank entree @user`")
            return

        # Prompt for Roblox username
        await ctx.send("Please provide the Roblox username of the person being ranked:")
        try:
            roblox_message = await self.bot.wait_for(
                "message",
                timeout=30.0,
                check=lambda m: m.author == ctx.author and m.channel == ctx.channel,
            )
            roblox_username = roblox_message.content
        except asyncio.TimeoutError:
            await ctx.send("❌ You took too long to respond. Command canceled.")
            return

        # Grab the roles from the guild
        role_recruit = ctx.guild.get_role(ROLE_ID_RECRUIT)
        role_official = ctx.guild.get_role(ROLE_ID_OFFICIAL_MEMBER)
        role_senior_personnel = ctx.guild.get_role(ROLE_ID_SENIOR_PERSONNEL)
        role_awaiting = ctx.guild.get_role(ROLE_ID_AWAITING_TRYOUT)
        role_unofficial = ctx.guild.get_role(ROLE_ID_UNOFFICIAL_PERSONNEL)

        # Apply the roles
        await member.add_roles(role_recruit, role_official, role_senior_personnel)
        await member.remove_roles(role_awaiting, role_unofficial)

        # Send confirmation message
        await ctx.send(f"✅ {member.mention} has been ranked successfully.")

        # Log the ranking in a specific channel
        log_channel_id = 1317200253170090014  # Replace with your logging channel ID
        log_channel = ctx.guild.get_channel(log_channel_id)
        if log_channel:
            embed = discord.Embed(
                title="Ranking Log",
                color=discord.Color.green(),
                description=(
                    f"**Discord Username:** {member.mention}\n"
                    f"**Roblox Username:** {roblox_username}\n"
                    f"**Old Rank:** Awaiting Tryout / Unofficial Personnel\n"
                    f"**New Rank:** Recruit / Official Member / Senior Personnel\n"
                    f"**Ranked By:** {ctx.author.mention}\n"
                    f"**Proof:** [Jump to Command](https://discord.com/channels/{ctx.guild.id}/{ctx.channel.id}/{ctx.message.id})"
                ),
            )
            await log_channel.send(embed=embed)

    @commands.command()
    async def startshift(self, ctx):
        """Start a shift."""
        points = load_points()
        user_points = points.get(str(ctx.author.id), {"points": 0, "time": 0})
        total_points = user_points["points"]
        total_time = user_points["time"]

        embed = discord.Embed(
            title="Start Shift",
            description=(
                f"**Current Points:** {total_points}\n"
                f"**Total Time on Shifts:** {total_time} minutes\n\n"
                "Are you sure you want to start a shift?\n"
                "You must store all recordings of your shifts, as you may be asked for them at any time."
            ),
            color=discord.Color.orange()
        )
        view = View()
        confirm_button = Button(label="Yes", style=discord.ButtonStyle.green)
        cancel_button = Button(label="No", style=discord.ButtonStyle.red)

        async def confirm_callback(interaction: Interaction):
            if interaction.user != ctx.author:
                await interaction.response.send_message("This is not your confirmation.", ephemeral=True)
                return
            await interaction.response.defer()
            start_time = datetime.now()
            self.active_shifts[ctx.author.id] = start_time
            dm_channel = await ctx.author.create_dm()
            shift_view = ShiftView(self.bot, ctx.author.id, start_time)
            await dm_channel.send(
                embed=discord.Embed(
                    title="Shift Started",
                    description="Your shift has started. Use the buttons below to manage your shift.",
                    color=discord.Color.green()
                ),
                view=shift_view
            )
            await ctx.send("✅ Shift started. Check your DMs for details.")
            view.stop()

        async def cancel_callback(interaction: Interaction):
            if interaction.user != ctx.author:
                await interaction.response.send_message("This is not your confirmation.", ephemeral=True)
                return
            await interaction.response.defer()
            await ctx.send("❌ Shift start canceled.")
            view.stop()

        confirm_button.callback = confirm_callback
        cancel_button.callback = cancel_callback
        view.add_item(confirm_button)
        view.add_item(cancel_button)

        await ctx.send(embed=embed, view=view)

    @commands.command()
    async def stopshift(self, ctx):
        """Stop a shift."""
        if ctx.author.id not in self.active_shifts:
            await ctx.send("❌ You don't have an active shift.")
            return

        start_time = self.active_shifts.pop(ctx.author.id)
        elapsed_time = datetime.now() - start_time
        minutes = int(elapsed_time.total_seconds() // 60)

        points = load_points()
        user_points = points.get(str(ctx.author.id), {"points": 0, "time": 0})
        user_points["points"] += minutes
        user_points["time"] += minutes
        points[str(ctx.author.id)] = user_points
        save_points(points)

        await ctx.send(
            f"✅ Shift stopped. You earned {minutes} points.\n"
            "⚠️ **Important:** You must store all recordings of your shifts, as you may be asked for them at any time."
        )

    @commands.command()
    async def points(self, ctx, member: discord.Member = None):
        """Shows how many points a user has (leave blank for self)."""
        member = member or ctx.author  # Default to the command author if no member is mentioned
        points = load_points()
        user_points = points.get(str(member.id), {"points": 0, "time": 0})
        total_points = user_points["points"]
        total_time = user_points["time"]

        embed = discord.Embed(
            title="Points Summary",
            description=(
                f"**User:** {member.mention}\n"
                f"**Points:** {total_points}\n"
                f"**Total Time on Shifts:** {total_time} minutes"
            ),
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def addpoints(self, ctx, member: discord.Member, points_to_add: int):
        """Adds points to a user (Administrator only)."""
        if points_to_add < 1:
            await ctx.send("❌ You must add at least 1 point.")
            return

        points = load_points()
        user_points = points.get(str(member.id), {"points": 0, "time": 0})
        user_points["points"] += points_to_add
        points[str(member.id)] = user_points
        save_points(points)

        await ctx.send(f"✅ Added {points_to_add} points to {member.mention}.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def removepoints(self, ctx, member: discord.Member, points_to_remove: int):
        """Removes points from a user (Administrator only)."""
        if points_to_remove < 1:
            await ctx.send("❌ You must remove at least 1 point.")
            return

        points = load_points()
        user_points = points.get(str(member.id), {"points": 0, "time": 0})

        if user_points["points"] < points_to_remove:
            await ctx.send(f"❌ {member.mention} does not have enough points to remove.")
            return

        # Ask for confirmation
        embed = discord.Embed(
            title="Confirmation Required",
            description=(
                f"Are you sure you want to remove {points_to_remove} points from {member.mention}?\n"
                f"**Current Points:** {user_points['points']}"
            ),
            color=discord.Color.orange()
        )
        view = View()
        confirm_button = Button(label="Yes", style=discord.ButtonStyle.green)
        cancel_button = Button(label="No", style=discord.ButtonStyle.red)

        async def confirm_callback(interaction: Interaction):
            if interaction.user != ctx.author:
                await interaction.response.send_message("This is not your confirmation.", ephemeral=True)
                return
            user_points["points"] -= points_to_remove
            points[str(member.id)] = user_points
            save_points(points)
            await ctx.send(f"✅ Removed {points_to_remove} points from {member.mention}.")
            view.stop()

        async def cancel_callback(interaction: Interaction):
            if interaction.user != ctx.author:
                await interaction.response.send_message("This is not your confirmation.", ephemeral=True)
                return
            await ctx.send("❌ Point removal canceled.")
            view.stop()

        confirm_button.callback = confirm_callback
        cancel_button.callback = cancel_callback
        view.add_item(confirm_button)
        view.add_item(cancel_button)

        await ctx.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(Ranking(bot))