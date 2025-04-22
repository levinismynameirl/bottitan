import discord
import asyncio
import asyncpg
from discord.ext import commands
from discord.ui import View, Button
from discord import Interaction
from datetime import datetime
import random
import string
from captcha.image import ImageCaptcha

# Role IDs
ROLE_ID_RECRUIT = 1303660480480673812     # Recruit role
ROLE_ID_OFFICIAL_MEMBER = 1346557689303662633  # Official Member role
ROLE_ID_AWAITING_TRYOUT = 1303662669626081300  # Awaiting Tryout role
ROLE_ID_UNOFFICIAL_PERSONNEL = 1303661603006447736  # Unofficial Personnel role
ROLE_ID_JUNIOR_PERSONNEL = 1303659781013241889  # Junior Personnel role

# PostgreSQL connection string
DATABASE_URL = "postgresql://postgres:jAHFxyiZVaVQAujHMPOLBtlMHZTbllTa@postgres.railway.internal:5432/railway"

async def initialize_database():
    """Initialize the database and create the points table if it doesn't exist."""
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS points (
            user_id TEXT PRIMARY KEY,
            points INTEGER DEFAULT 0,
            time INTEGER DEFAULT 0
        )
    """)
    await conn.close()

async def get_user_points(user_id):
    """Get a user's points and time from the database."""
    conn = await asyncpg.connect(DATABASE_URL)
    row = await conn.fetchrow("SELECT points, time FROM points WHERE user_id = $1", str(user_id))
    await conn.close()
    return {"points": row["points"], "time": row["time"]} if row else {"points": 0, "time": 0}

async def update_user_points(user_id, points, time):
    """Update a user's points and time in the database."""
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute("""
        INSERT INTO points (user_id, points, time)
        VALUES ($1, $2, $3)
        ON CONFLICT (user_id) DO UPDATE SET
            points = points + $2,
            time = time + $3
    """, str(user_id), points, time)
    await conn.close()

class ShiftView(View):
    def __init__(self, bot, user_id, start_time):
        super().__init__(timeout=None)
        self.bot = bot
        self.user_id = user_id
        self.start_time = start_time
        self.paused = False

    async def update_embed(self, interaction):
        """Update the embed with the current elapsed time."""
        elapsed_time = datetime.now() - self.start_time
        minutes = int(elapsed_time.total_seconds() // 60)

        embed = discord.Embed(
            title="Shift Logging",
            description=f"**Elapsed Time:** {minutes} minutes\n"
                        f"**Status:** {'Paused' if self.paused else 'Active'}",
            color=discord.Color.blue()
        )
        await interaction.response.edit_message(embed=embed, view=self)

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

        # Calculate the total elapsed time
        elapsed_time = datetime.now() - self.start_time
        minutes = int(elapsed_time.total_seconds() // 60)

        # Update the user's points in the database
        await update_user_points(self.user_id, minutes, minutes)

        # Disable all buttons
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)

        await interaction.followup.send(
            f"✅ Shift stopped. You earned {minutes} points.\n"
            "⚠️ **Important:** You must store all recordings of your shifts, as you may be asked for them at any time.",
            ephemeral=True
        )
        self.stop()

class Ranking(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_shifts = {}

    @commands.command()
    async def startshift(self, ctx):
        """Start a shift using reactions in a DM."""
        user_points = await get_user_points(ctx.author.id)
        total_points = user_points["points"]
        total_time = user_points["time"]

        # Send an embed in the server channel
        embed = discord.Embed(
            title="Start Shift",
            description=(
                f"**Current Points:** {total_points}\n"
                f"**Total Time on Shifts:** {total_time} minutes\n\n"
                "React with ✅ to start your shift or ❌ to cancel.\n"
                "⚠️ **Important:** You must store all recordings of your shifts, as you may be asked for them at any time."
            ),
            color=discord.Color.orange()
        )
        message = await ctx.send(embed=embed)

        # Add reactions
        await message.add_reaction("✅")
        await message.add_reaction("❌")

        def check_reaction(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == message.id

        try:
            reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check_reaction)
            if str(reaction.emoji) == "✅":
                start_time = datetime.now()
                self.active_shifts[ctx.author.id] = start_time

                # Send a DM to the user
                try:
                    dm_channel = await ctx.author.create_dm()
                    dm_embed = discord.Embed(
                        title="Shift Started",
                        description=(
                            "Your shift has started. Use the reactions below to control your shift:\n"
                            "⏸️ **Pause**\n"
                            "▶️ **Resume**\n"
                            "⏹️ **Stop**"
                        ),
                        color=discord.Color.green()
                    )
                    dm_message = await dm_channel.send(embed=dm_embed)

                    # Add reactions for pause, resume, and stop
                    await dm_message.add_reaction("⏸️")
                    await dm_message.add_reaction("▶️")
                    await dm_message.add_reaction("⏹️")

                    paused = False

                    def dm_check(reaction, user):
                        return user == ctx.author and str(reaction.emoji) in ["⏸️", "▶️", "⏹️"] and reaction.message.id == dm_message.id

                    while True:
                        reaction, user = await self.bot.wait_for("reaction_add", timeout=None, check=dm_check)

                        if str(reaction.emoji) == "⏸️":
                            if paused:
                                await dm_channel.send("❌ Your shift is already paused.", delete_after=5)
                            else:
                                paused = True
                                await dm_channel.send("⏸️ Your shift has been paused.", delete_after=5)

                        elif str(reaction.emoji) == "▶️":
                            if not paused:
                                await dm_channel.send("❌ Your shift is already active.", delete_after=5)
                            else:
                                paused = False
                                await dm_channel.send("▶️ Your shift has been resumed.", delete_after=5)

                        elif str(reaction.emoji) == "⏹️":
                            elapsed_time = datetime.now() - start_time
                            minutes = int(elapsed_time.total_seconds() // 60)

                            # Update the user's points in the database
                            await update_user_points(ctx.author.id, minutes, minutes)

                            await dm_channel.send(
                                f"⏹️ Your shift has been stopped. You earned {minutes} points.\n"
                                "⚠️ **Important:** You must store all recordings of your shifts, as you may be asked for them at any time."
                            )
                            break  # Exit the loop when the shift is stopped

                except discord.Forbidden:
                    await ctx.send("❌ I could not send you a DM. Please enable DMs and try again.")
            elif str(reaction.emoji) == "❌":
                await ctx.send("❌ Shift start canceled.")
        except asyncio.TimeoutError:
            await ctx.send("❌ You took too long to respond. Shift start canceled.")

    @commands.command()
    async def stopshift(self, ctx):
        """Stop a shift."""
        if ctx.author.id not in self.active_shifts:
            await ctx.send("❌ You don't have an active shift.")
            return

        start_time = self.active_shifts.pop(ctx.author.id)
        elapsed_time = datetime.now() - start_time
        minutes = int(elapsed_time.total_seconds() // 60)

        await update_user_points(ctx.author.id, minutes, minutes)

        await ctx.send(
            f"✅ Shift stopped. You earned {minutes} points.\n"
            "⚠️ **Important:** You must store all recordings of your shifts, as you may be asked for them at any time."
        )

    @commands.command()
    async def points(self, ctx, member: discord.Member = None):
        """Shows how many points a user has (leave blank for self)."""
        member = member or ctx.author  # Default to the command author if no member is mentioned
        user_points = await get_user_points(member.id)
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

        # Debugging message
        print(f"Adding {points_to_add} points to user {member.id}")

        # Update the user's points in the database
        await update_user_points(member.id, points_to_add, 0)

        # Fetch the updated points to confirm the change
        user_points = await get_user_points(member.id)
        total_points = user_points["points"]

        await ctx.send(f"✅ Added {points_to_add} points to {member.mention}. Total points: {total_points}.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def removepoints(self, ctx, member: discord.Member, points_to_remove: int):
        """Removes points from a user (Administrator only)."""
        if points_to_remove < 1:
            await ctx.send("❌ You must remove at least 1 point.")
            return

        user_points = await get_user_points(member.id)
        if user_points["points"] < points_to_remove:
            await ctx.send(f"❌ {member.mention} does not have enough points to remove.")
            return

        await update_user_points(member.id, -points_to_remove, 0)
        await ctx.send(f"✅ Removed {points_to_remove} points from {member.mention}.")

    @commands.command()
    async def leaderboard(self, ctx):
        """Display the top 10 users with the most points."""
        conn = await asyncpg.connect(DATABASE_URL)
        rows = await conn.fetch("SELECT user_id, points FROM points ORDER BY points DESC LIMIT 10")
        await conn.close()

        if not rows:
            await ctx.send("❌ No points have been recorded yet.")
            return

        embed = discord.Embed(
            title="🏆 Leaderboard",
            description="Top 10 users with the most points:",
            color=discord.Color.gold()
        )

        for rank, row in enumerate(rows, start=1):
            user = self.bot.get_user(int(row["user_id"]))
            user_name = user.name if user else f"Unknown User ({row['user_id']})"
            embed.add_field(name=f"#{rank}: {user_name}", value=f"{row['points']} points", inline=False)

        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def rankentree(self, ctx, member: discord.Member):
        """Assign roles and set nickname for a new recruit."""
        # Role IDs
        recruit_role = ctx.guild.get_role(ROLE_ID_RECRUIT)
        official_member_role = ctx.guild.get_role(ROLE_ID_OFFICIAL_MEMBER)
        junior_personnel_role = ctx.guild.get_role(ROLE_ID_JUNIOR_PERSONNEL)
        visitor_role = ctx.guild.get_role(ROLE_ID_AWAITING_TRYOUT)
        unofficial_personnel_role = ctx.guild.get_role(ROLE_ID_UNOFFICIAL_PERSONNEL)

        # Add roles
        if recruit_role:
            await member.add_roles(recruit_role)
        if official_member_role:
            await member.add_roles(official_member_role)
        if junior_personnel_role:
            await member.add_roles(junior_personnel_role)

        # Remove roles
        if visitor_role:
            await member.remove_roles(visitor_role)
        if unofficial_personnel_role:
            await member.remove_roles(unofficial_personnel_role)

        await ctx.send(f"✅ Roles updated for {member.mention}.")

        # Send a DM to the member being ranked
        try:
            dm_channel = await member.create_dm()

            # Ask for codename
            await dm_channel.send("Please enter user's **codename**:")
            try:
                codename_msg = await self.bot.wait_for(
                    "message", timeout=60.0, check=lambda m: m.author == member and m.channel == dm_channel
                )
                codename = codename_msg.content
            except asyncio.TimeoutError:
                await dm_channel.send("❌ You took too long to respond. Command canceled.")
                await ctx.send(f"❌ {member.mention} did not respond in time. Command canceled.")
                return

            # Ask for Roblox username
            await dm_channel.send("Please enter user's **Roblox username**:")
            try:
                roblox_msg = await self.bot.wait_for(
                    "message", timeout=60.0, check=lambda m: m.author == member and m.channel == dm_channel
                )
                roblox_username = roblox_msg.content
            except asyncio.TimeoutError:
                await dm_channel.send("❌ You took too long to respond. Command canceled.")
                await ctx.send(f"❌ {member.mention} did not respond in time. Command canceled.")
                return

            # Update nickname
            new_nickname = f"{codename} | {roblox_username}"
            try:
                await member.edit(nick=new_nickname)
                await dm_channel.send(f"✅ Your nickname has been updated to: `{new_nickname}`")
                await ctx.send(f"✅ Nickname updated for {member.mention} to: `{new_nickname}`")
            except discord.Forbidden:
                await dm_channel.send("❌ I do not have permission to change your nickname.")
                await ctx.send(f"❌ I do not have permission to change {member.mention}'s nickname.")
        except discord.Forbidden:
            await ctx.send(f"❌ Could not send a DM to {member.mention}. Ensure they have DMs enabled.")
        
async def setup(bot):
    await bot.add_cog(Ranking(bot))
