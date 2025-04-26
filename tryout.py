import discord
from discord.ext import commands
from discord.ui import Button, View
from datetime import datetime, timedelta
import asyncio
import time

class Tryout(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tryouts = {}  # Store tryout data by tryout ID
        self.codename_approvers = [1133038563047514192, 920314437179674694]  # Replace with approver IDs

    async def update_management_message(self, tryout_id):
        """Update the tryout management channel message."""
        tryout = self.tryouts[tryout_id]
        channel = tryout["channel"]
        elapsed_time = int(time.time() - tryout["start_time"].timestamp())
        elapsed_minutes = elapsed_time // 60

        participants = "\n".join(
            [f"<@{member_id}>: {points} points" for member_id, points in tryout["participants"].items()]
        )
        participants = participants if participants else "No participants yet."

        embed = discord.Embed(
            title=f"Tryout Management - ID `{tryout_id}`",
            description=f"**Host:** {tryout['host'].mention}\n"
                        f"**Co-Host:** {tryout['co_host'].mention if tryout['co_host'] else 'None'}\n"
                        f"**Elapsed Time:** {elapsed_minutes} minutes\n\n"
                        f"**Participants:**\n{participants}",
            color=discord.Color.green()
        )
        if "management_message" in tryout:
            await tryout["management_message"].edit(embed=embed)
        else:
            tryout["management_message"] = await channel.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def tryoutstart(self, ctx):
        """Start a tryout."""
        await ctx.send("How many minutes until the tryout starts?")
        
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.isdigit()

        try:
            msg = await self.bot.wait_for("message", timeout=60, check=check)
            minutes_until_start = int(msg.content)
        except asyncio.TimeoutError:
            await ctx.send("❌ You took too long to respond. Tryout setup canceled.")
            return

        start_time = datetime.utcnow() + timedelta(minutes=minutes_until_start)
        tryout_id = len(self.tryouts) + 1
        self.tryouts[tryout_id] = {
            "host": ctx.author,
            "co_host": None,
            "participants": {},
            "start_time": start_time,
        }

        embed = discord.Embed(
            title="Tryout Announcement",
            description=f"A tryout is starting at **{start_time.strftime('%H:%M')} UTC**.\n"
                        f"There are **12 spaces** available.\n"
                        f"Tryout ID: `{tryout_id}`\n\n"
                        f"Click the buttons below to join or leave the tryout.",
            color=discord.Color.blue()
        )
        embed.set_footer(text="You must have the 'Visitor' role to join.")

        join_button = Button(label="Join Tryout", style=discord.ButtonStyle.green)
        leave_button = Button(label="Leave Tryout", style=discord.ButtonStyle.red)

        async def join_callback(interaction):
            visitor_role = discord.utils.get(ctx.guild.roles, name="Visitor")
            if visitor_role not in interaction.user.roles:
                await interaction.response.send_message("❌ You must have the 'Visitor' role to join the tryout.", ephemeral=True)
                return

            if len(self.tryouts[tryout_id]["participants"]) >= 12:
                await interaction.response.send_message("❌ The tryout is full.", ephemeral=True)
                return

            if interaction.user.id in self.tryouts[tryout_id]["participants"]:
                await interaction.response.send_message("❌ You are already in the tryout.", ephemeral=True)
                return

            self.tryouts[tryout_id]["participants"][interaction.user.id] = 10  # Start with 10 points
            await interaction.response.send_message("✅ You have joined the tryout.", ephemeral=True)

        async def leave_callback(interaction):
            if interaction.user.id not in self.tryouts[tryout_id]["participants"]:
                await interaction.response.send_message("❌ You are not in the tryout.", ephemeral=True)
                return

            del self.tryouts[tryout_id]["participants"][interaction.user.id]
            await interaction.response.send_message("✅ You have left the tryout.", ephemeral=True)

        join_button.callback = join_callback
        leave_button.callback = leave_callback

        view = View()
        view.add_item(join_button)
        view.add_item(leave_button)

        # Fetch the specific channel by ID
        tryout_channel = self.bot.get_channel(1355956599260188795)
        if tryout_channel is None:
            await ctx.send("❌ Could not find the tryout channel. Please check the channel ID.")
            return

        await tryout_channel.send(embed=embed, view=view)

        # Wait until the tryout starts
        await asyncio.sleep(minutes_until_start * 60)

        # Create tryout management channel
        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            ctx.author: discord.PermissionOverwrite(read_messages=True, manage_channels=True),
        }
        channel = await ctx.guild.create_text_channel(f"tryout-{tryout_id}-management", overwrites=overwrites)
        self.tryouts[tryout_id]["channel"] = channel

        await channel.send(f"Welcome to the tryout management channel for Tryout ID `{tryout_id}`.\n"
                           f"Host: {ctx.author.mention}\n"
                           f"Use this channel to manage the tryout.")

    @commands.command()
    async def setcohost(self, ctx, tryout_id: int, member: discord.Member):
        """Set a co-host for the tryout."""
        if tryout_id not in self.tryouts:
            await ctx.send("❌ Invalid tryout ID.")
            return

        tryout = self.tryouts[tryout_id]
        if ctx.author != tryout["host"]:
            await ctx.send("❌ Only the host can set a co-host.")
            return

        tryout["co_host"] = member
        channel = tryout["channel"]
        await channel.set_permissions(member, read_messages=True, manage_channels=True)
        await ctx.send(f"✅ {member.mention} has been set as the co-host for Tryout ID `{tryout_id}`.")

    @commands.command()
    async def endtryout(self, ctx, tryout_id: int):
        """End a tryout and process results."""
        if tryout_id not in self.tryouts:
            await ctx.send("❌ Invalid tryout ID.")
            return

        tryout = self.tryouts[tryout_id]
        if ctx.author != tryout["host"] and ctx.author != tryout["co_host"]:
            await ctx.send("❌ Only the host or co-host can end the tryout.")
            return

        passed = [member_id for member_id, points in tryout["participants"].items() if points > 20]
        failed = [member_id for member_id, points in tryout["participants"].items() if points <= 20]

        for member_id in passed:
            member = ctx.guild.get_member(member_id)
            if member:
                await member.send("🎉 Congratulations! You passed the tryout. Please provide your Roblox username:")

                def check_username(m):
                    return m.author == member and isinstance(m.channel, discord.DMChannel)

                try:
                    username_msg = await self.bot.wait_for("message", timeout=300, check=check_username)
                    roblox_username = username_msg.content
                except asyncio.TimeoutError:
                    await member.send("❌ You took too long to respond. Tryout process canceled.")
                    continue

                await member.send("Please provide your desired codename:")

                def check_codename(m):
                    return m.author == member and isinstance(m.channel, discord.DMChannel)

                try:
                    codename_msg = await self.bot.wait_for("message", timeout=300, check=check_codename)
                    codename = codename_msg.content
                except asyncio.TimeoutError:
                    await member.send("❌ You took too long to respond. Tryout process canceled.")
                    continue

                # Send codename for approval
                for approver_id in self.codename_approvers:
                    approver = ctx.guild.get_member(approver_id)
                    if approver:
                        await approver.send(f"Codename approval request:\n"
                                            f"User: {member.mention}\n"
                                            f"Roblox Username: {roblox_username}\n"
                                            f"Desired Codename: {codename}\n\n"
                                            f"Approve or deny using the commands:\n"
                                            f"`!approve {member.id}` or `!deny {member.id} <reason>`")

                await member.send("✅ Your codename has been sent for approval. Please wait for a response.")

        for member_id in failed:
            member = ctx.guild.get_member(member_id)
            if member:
                await member.send("❌ Unfortunately, you did not pass the tryout. Better luck next time!")

        # Clean up
        channel = tryout["channel"]
        await channel.delete()
        del self.tryouts[tryout_id]
        await ctx.send(f"✅ Tryout ID `{tryout_id}` has been ended.")

    @commands.command()
    async def approve(self, ctx, member_id: int):
        """Approve a codename."""
        if ctx.author.id not in self.codename_approvers:
            await ctx.send("❌ You do not have permission to approve codenames.")
            return

        member = ctx.guild.get_member(member_id)
        if not member:
            await ctx.send("❌ Member not found.")
            return

        # Assign roles and update nickname
        recruit_role = discord.utils.get(ctx.guild.roles, name="Recruit")
        official_member_role = discord.utils.get(ctx.guild.roles, name="Official Member")
        unofficial_member_role = discord.utils.get(ctx.guild.roles, name="Unofficial Member")
        visitor_role = discord.utils.get(ctx.guild.roles, name="Visitor")

        if recruit_role:
            await member.add_roles(recruit_role)
        if official_member_role:
            await member.add_roles(official_member_role)
        if unofficial_member_role:
            await member.remove_roles(unofficial_member_role)
        if visitor_role:
            await member.remove_roles(visitor_role)

        # Update nickname
        nickname = f"{member.display_name.split('|')[0].strip()} | {member.display_name.split('|')[-1].strip()}"
        await member.edit(nick=nickname)

        await ctx.send(f"✅ Codename approved for {member.mention}.")

    @commands.command()
    async def deny(self, ctx, member_id: int, *, reason: str):
        """Deny a codename."""
        if ctx.author.id not in self.codename_approvers:
            await ctx.send("❌ You do not have permission to deny codenames.")
            return

        member = ctx.guild.get_member(member_id)
        if not member:
            await ctx.send("❌ Member not found.")
            return

        await member.send(f"❌ Your codename request has been denied for the following reason:\n{reason}\n"
                          f"Please provide a new codename for approval.")

        await ctx.send(f"✅ Codename denied for {member.mention}. Reason: {reason}")

    @commands.command(name="addscore")
    async def addscore(self, ctx, tryout_id: int, member: discord.Member, points: int):
        """Add points to a participant."""
        if tryout_id not in self.tryouts:
            await ctx.send("❌ Invalid tryout ID.")
            return

        tryout = self.tryouts[tryout_id]
        if ctx.author != tryout["host"] and ctx.author != tryout["co_host"]:
            await ctx.send("❌ Only the host or co-host can modify points.")
            return

        if member.id not in tryout["participants"]:
            await ctx.send(f"❌ {member.mention} is not a participant in this tryout.")
            return

        tryout["participants"][member.id] += points
        await ctx.send(f"✅ Added {points} points to {member.mention}.")
        await self.update_management_message(tryout_id)

    @commands.command(name="removescore")
    async def removescore(self, ctx, tryout_id: int, member: discord.Member, points: int):
        """Remove points from a participant."""
        if tryout_id not in self.tryouts:
            await ctx.send("❌ Invalid tryout ID.")
            return

        tryout = self.tryouts[tryout_id]
        if ctx.author != tryout["host"] and ctx.author != tryout["co_host"]:
            await ctx.send("❌ Only the host or co-host can modify points.")
            return

        if member.id not in tryout["participants"]:
            await ctx.send(f"❌ {member.mention} is not a participant in this tryout.")
            return

        tryout["participants"][member.id] -= points
        await ctx.send(f"✅ Removed {points} points from {member.mention}.")
        await self.update_management_message(tryout_id)

    @commands.command(name="addscoreall")
    async def addscoreall(self, ctx, tryout_id: int, points: int):
        """Add points to all participants."""
        if tryout_id not in self.tryouts:
            await ctx.send("❌ Invalid tryout ID.")
            return

        tryout = self.tryouts[tryout_id]
        if ctx.author != tryout["host"] and ctx.author != tryout["co_host"]:
            await ctx.send("❌ Only the host or co-host can modify points.")
            return

        for member_id in tryout["participants"]:
            tryout["participants"][member_id] += points

        await ctx.send(f"✅ Added {points} points to all participants.")
        await self.update_management_message(tryout_id)

    @commands.command(name="removescoreall")
    async def removescoreall(self, ctx, tryout_id: int, points: int):
        """Remove points from all participants."""
        if tryout_id not in self.tryouts:
            await ctx.send("❌ Invalid tryout ID.")
            return

        tryout = self.tryouts[tryout_id]
        if ctx.author != tryout["host"] and ctx.author != tryout["co_host"]:
            await ctx.send("❌ Only the host or co-host can modify points.")
            return

        for member_id in tryout["participants"]:
            tryout["participants"][member_id] -= points

        await ctx.send(f"✅ Removed {points} points from all participants.")
        await self.update_management_message(tryout_id)

    @commands.command()
    async def showpoints(self, ctx, tryout_id: int):
        """Show the points of all participants."""
        if tryout_id not in self.tryouts:
            await ctx.send("❌ Invalid tryout ID.")
            return

        tryout = self.tryouts[tryout_id]
        participants = "\n".join(
            [f"<@{member_id}>: {points} points" for member_id, points in tryout["participants"].items()]
        )
        participants = participants if participants else "No participants yet."

        embed = discord.Embed(
            title=f"Tryout Points - ID `{tryout_id}`",
            description=f"**Participants:**\n{participants}",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Tryout(bot))