import discord
from discord.ext import commands
from discord.ui import Button, View
from datetime import datetime, timedelta
import asyncio
import time
import json

class Tryout(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tryouts = {}  # Store tryout data by tryout ID
        self.codename_approvers = [1133038563047514192, 920314437179674694]  # Replace with approver IDs
        self.pending_approvals = {}  # Store pending codename approvals
        self.TRYOUT_PING_ROLE_ID = 1307035073383759964
        self.pool = None  # Will be set when database connection is established

    async def save_tryout_to_db(self, tryout_id: int):
        """Save tryout data to database."""
        tryout = self.tryouts[tryout_id]
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO tryouts (
                    tryout_id, host_id, cohost_id, start_time, participants
                ) VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (tryout_id) 
                DO UPDATE SET 
                    cohost_id = $3,
                    participants = $5
            """, tryout_id, 
                tryout["host"].id,
                tryout["co_host"].id if tryout["co_host"] else None,
                tryout["start_time"],
                json.dumps({str(k): v for k, v in tryout["participants"].items()})
            )

    async def end_tryout_in_db(self, tryout_id: int):
        """Mark tryout as ended in database with final scores."""
        tryout = self.tryouts[tryout_id]
        async with self.pool.acquire() as conn:
            await conn.execute("""
                UPDATE tryouts 
                SET status = 'ended',
                    end_time = CURRENT_TIMESTAMP,
                    participants = $1
                WHERE tryout_id = $2
            """, 
                json.dumps({str(k): v for k, v in tryout["participants"].items()}),
                tryout_id
            )

    async def load_tryouts_from_db(self):
        """Load active tryouts from database on bot startup."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM tryouts WHERE status = 'active'")
            for row in rows:
                self.tryouts[row['tryout_id']] = {
                    "host": await self.bot.fetch_user(row['host_id']),
                    "co_host": await self.bot.fetch_user(row['cohost_id']) if row['cohost_id'] else None,
                    "participants": {int(k): v for k, v in json.loads(row['participants']).items()},
                    "start_time": row['start_time']
                }

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

    async def get_next_tryout_id(self):
        """Get the next available tryout ID from the database."""
        async with self.pool.acquire() as conn:
            # Get the highest tryout_id from the database
            result = await conn.fetchval("SELECT MAX(tryout_id) FROM tryouts")
            return (result or 0) + 1  # If no tryouts exist, start with 1

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

        # Get the next tryout ID from database
        try:
            tryout_id = await self.get_next_tryout_id()
        except Exception as e:
            await ctx.send("❌ Failed to generate tryout ID. Please try again.")
            print(f"Error generating tryout ID: {e}")
            return

        start_time = datetime.utcnow() + timedelta(minutes=minutes_until_start)
        self.tryouts[tryout_id] = {
            "host": ctx.author,
            "co_host": None,
            "participants": {},
            "start_time": start_time,
        }
        await self.save_tryout_to_db(tryout_id)  # Save initial tryout data

        embed = discord.Embed(
            title="Tryout Announcement",
            description=f"A tryout is starting at **{start_time.strftime('%H:%M')} UTC**.\n"
                        f"There are **12 spaces** available.\n"
                        f"Tryout ID: `{tryout_id}`\n\n"
                        f"**Participants:**\nNo participants yet.",
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

            self.tryouts[tryout_id]["participants"][interaction.user.id] = 10
            await self.save_tryout_to_db(tryout_id)  # Save updated participants
            remaining_spots = 12 - len(self.tryouts[tryout_id]["participants"])
            await interaction.response.send_message("✅ You have joined the tryout.", ephemeral=True)

            # Update announcement message
            participants = "\n".join([f"<@{member_id}>" for member_id in self.tryouts[tryout_id]["participants"].keys()])
            updated_embed = discord.Embed(
                title="Tryout Announcement",
                description=f"A tryout is starting at **{start_time.strftime('%H:%M')} UTC**.\n"
                            f"**Host:** {ctx.author.mention}\n"
                            f"There are **{remaining_spots} spots remaining** out of 12.\n"
                            f"Tryout ID: `{tryout_id}`\n\n"
                            f"**Participants:**\n{participants}",
                color=discord.Color.blue()
            )
            updated_embed.set_footer(text="You must have the 'Visitor' role to join.")
            await announcement_message.edit(embed=updated_embed)

        async def leave_callback(interaction):
            if interaction.user.id not in self.tryouts[tryout_id]["participants"]:
                await interaction.response.send_message("❌ You are not in the tryout.", ephemeral=True)
                return

            del self.tryouts[tryout_id]["participants"][interaction.user.id]  # Remove participant
            await self.save_tryout_to_db(tryout_id)  # Save updated participants
            await interaction.response.send_message("✅ You have left the tryout.", ephemeral=True)

            # Update the announcement message with the current participants
            participants = "\n".join(
                [f"{interaction.guild.get_member(member_id).name}: {points} points"
                 for member_id, points in self.tryouts[tryout_id]["participants"].items()]
            )
            participants = participants if participants else "No participants yet."
            updated_embed = discord.Embed(
                title="Tryout Announcement",
                description=f"A tryout is starting at **{start_time.strftime('%H:%M')} UTC**.\n"
                            f"There are **12 spaces** available.\n"
                            f"Tryout ID: `{tryout_id}`\n\n"
                            f"**Participants:**\n{participants}",
                color=discord.Color.blue()
            )
            updated_embed.set_footer(text="You must have the 'Visitor' role to join.")
            await announcement_message.edit(embed=updated_embed)

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

        # Send the initial announcement message with role ping
        tryout_ping_role = ctx.guild.get_role(self.TRYOUT_PING_ROLE_ID)
        announcement_message = await tryout_channel.send(
            content=f"{tryout_ping_role.mention}" if tryout_ping_role else None,
            embed=embed, 
            view=view
        )

        # Wait until the tryout starts
        await asyncio.sleep(minutes_until_start * 60)

        # Disable buttons and update announcement message
        view.clear_items()  # Remove all buttons
        participants = "\n".join(
            [f"<@{member_id}>: {points} points" for member_id, points in self.tryouts[tryout_id]["participants"].items()]
        )
        participants = participants if participants else "No participants yet."
        updated_embed = discord.Embed(
            title="Tryout In Progress",
            description=f"This tryout has started at **{start_time.strftime('%H:%M')} UTC**.\n"
                        f"**Host:** {ctx.author.mention}\n"
                        f"Tryout ID: `{tryout_id}`\n\n"
                        f"**Participants:**\n{participants}",
            color=discord.Color.green()
        )
        await announcement_message.edit(embed=updated_embed, view=view)

        # Create tryout management channel with host ping
        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            ctx.author: discord.PermissionOverwrite(read_messages=True, manage_channels=True),
        }
        channel = await ctx.guild.create_text_channel(f"tryout-{tryout_id}-management", overwrites=overwrites)
        self.tryouts[tryout_id]["channel"] = channel

        # Prepare the management message with host ping
        await channel.send(f"{ctx.author.mention} Your tryout has started!")

        # Prepare the list of participants
        participants = "\n".join(
            [f"<@{member_id}>: {points} points" for member_id, points in self.tryouts[tryout_id]["participants"].items()]
        )
        participants = participants if participants else "No participants yet."

        # Prepare the list of commands
        commands_list = """
**Available Commands:**
- `!setcohost <tryout_id> <member>`: Set a co-host for the tryout.
- `!addscore <tryout_id> <member> <points>`: Add points to a participant.
- `!removescore <tryout_id> <member> <points>`: Remove points from a participant.
- `!addscoreall <tryout_id> <points>`: Add points to all participants.
- `!removescoreall <tryout_id> <points>`: Remove points from all participants.
- `!showpoints <tryout_id>`: Show the points of all participants.
- `!endtryout <tryout_id>`: End the tryout and process results.
"""

        # Create the embed
        embed = discord.Embed(
            title=f"Tryout Management - ID `{tryout_id}`",
            description=f"**Host:** {ctx.author.mention}\n"
                        f"**Co-Host:** None\n\n"
                        f"**Participants:**\n{participants}\n\n"
                        f"{commands_list}",
            color=discord.Color.green()
        )

        # Send the embed to the management channel
        management_message = await channel.send(embed=embed)
        self.tryouts[tryout_id]["management_message"] = management_message

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
        await self.save_tryout_to_db(tryout_id)  # Save updated co-host
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

        passed = [member_id for member_id, points in tryout["participants"].items() if points >= 20]
        failed = [member_id for member_id, points in tryout["participants"].items() if points < 20]

        # Store pending approvals
        self.pending_approvals = {}

        for member_id in passed:
            member = ctx.guild.get_member(member_id)
            if member:
                try:
                    # Ask for Roblox username
                    await member.send("🎉 Congratulations! You passed the tryout. Please provide your Roblox username:")
                    roblox_response = await self.bot.wait_for(
                        "message",
                        timeout=300,
                        check=lambda m: m.author == member and isinstance(m.channel, discord.DMChannel)
                    )
                    roblox_username = roblox_response.content

                    # Ask for desired codename
                    await self.ask_for_codename(member, roblox_username)

                except asyncio.TimeoutError:
                    await member.send("❌ You took too long to respond. Please contact an administrator.")

        for member_id in failed:
            member = ctx.guild.get_member(member_id)
            if member:
                await member.send("❌ Unfortunately, you did not pass the tryout. Better luck next time!")

        # Clean up
        channel = tryout["channel"]
        await channel.delete()
        await self.end_tryout_in_db(tryout_id)  # Save final state
        del self.tryouts[tryout_id]
        await ctx.send(f"✅ Tryout ID `{tryout_id}` has been ended.")

    async def ask_for_codename(self, member, roblox_username, previous_denied=None):
        """Ask for codename and handle approval process."""
        if previous_denied:
            await member.send(f"Your previous codename was denied. Reason: {previous_denied}\nPlease provide a new codename:")
        else:
            await member.send("Please provide your desired codename:")

        try:
            codename_response = await self.bot.wait_for(
                "message",
                timeout=300,
                check=lambda m: m.author == member and isinstance(m.channel, discord.DMChannel)
            )
            codename = codename_response.content

            # Store in pending approvals
            self.pending_approvals[member.id] = {
                "codename": codename,
                "roblox_username": roblox_username
            }

            # Send approval requests to approvers
            for approver_id in self.codename_approvers:
                approver = member.guild.get_member(approver_id)
                if approver:
                    embed = discord.Embed(
                        title="Codename Approval Request",
                        description=f"User: {member.mention}\n"
                                    f"Roblox Username: {roblox_username}\n"
                                    f"Desired Codename: {codename}\n\n"
                                    f"Use `!approve {member.id}` to approve\n"
                                    f"Use `!deny {member.id} <reason>` to deny",
                        color=discord.Color.blue()
                    )
                    await approver.send(embed=embed)

            await member.send("✅ Your codename has been sent for approval. Please wait for a response.")

        except asyncio.TimeoutError:
            await member.send("❌ You took too long to respond. Please contact an administrator.")

    @commands.command()
    async def approve(self, ctx, member_id: int):
        """Approve a codename."""
        try:
            # Check if approver is authorized
            if ctx.author.id not in self.codename_approvers:
                await ctx.send("❌ You do not have permission to approve codenames.")
                return

            if member_id not in self.pending_approvals:
                await ctx.send("❌ No pending approval found for this user.")
                return

            # Get the guild from the bot's cached guilds
            guild = None
            for g in self.bot.guilds:
                if any(member.id == ctx.author.id for member in g.members):
                    guild = g
                    break

            if not guild:
                await ctx.send("❌ Couldn't find the server.")
                return

            member = guild.get_member(member_id)
            if not member:
                await ctx.send("❌ Member not found.")
                return

            approval_data = self.pending_approvals[member_id]
            nickname = f"\"{approval_data['codename']}\" | {approval_data['roblox_username']}"

            # Get roles
            recruit_role = discord.utils.get(guild.roles, name="Recruit")
            official_role = discord.utils.get(guild.roles, name="Official Member")
            visitor_role = discord.utils.get(guild.roles, name="Visitor")
            unofficial_role = discord.utils.get(guild.roles, name="Unofficial Member")

            if not recruit_role or not official_role:
                await ctx.send("❌ Required roles not found.")
                return

            try:
                await member.edit(nick=nickname)
                await member.add_roles(recruit_role)
                await member.add_roles(official_role)
                if visitor_role: await member.remove_roles(visitor_role)
                if unofficial_role: await member.remove_roles(unofficial_role)

                await member.send(f"✅ Your codename has been approved! Your nickname has been updated to: {nickname}")
                await ctx.send(f"✅ Approved codename for {member.mention}")
                
                # Clean up pending approval
                del self.pending_approvals[member_id]

            except discord.Forbidden as e:
                await ctx.send(f"❌ Permission error: {str(e)}")
            except Exception as e:
                await ctx.send(f"❌ An error occurred: {str(e)}")

        except Exception as e:
            await ctx.send(f"❌ An unexpected error occurred: {str(e)}")

    @commands.command()
    async def deny(self, ctx, member_id: int, *, reason: str):
        """Deny a codename."""
        if ctx.author.id not in self.codename_approvers:
            await ctx.send("❌ You do not have permission to deny codenames.")
            return

        if member_id not in self.pending_approvals:
            await ctx.send("❌ No pending approval found for this user.")
            return

        member = ctx.guild.get_member(member_id)
        if not member:
            await ctx.send("❌ Member not found.")
            return

        approval_data = self.pending_approvals[member_id]
        await self.ask_for_codename(member, approval_data['roblox_username'], reason)
        await ctx.send(f"✅ Denied codename for {member.mention}")

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
        await self.save_tryout_to_db(tryout_id)  # Save updated participants
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
        await self.save_tryout_to_db(tryout_id)  # Save updated participants
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

        await self.save_tryout_to_db(tryout_id)  # Save updated participants
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

        await self.save_tryout_to_db(tryout_id)  # Save updated participants
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

    @commands.command()
    async def helptt(self, ctx):
        """Show all tryout-related commands. Only works in tryout management channels."""
        # Check if the command is used in a tryout management channel
        if not ctx.channel.name.startswith("tryout-") or not ctx.channel.name.endswith("-management"):
            await ctx.send("❌ This command can only be used in tryout management channels.")
            return

        embed = discord.Embed(
            title="Tryout System Commands",
            description="All available commands for managing tryouts.",
            color=discord.Color.blue()
        )

        # Host Management
        embed.add_field(
            name="🎮 Host Commands",
            value="""
`!setcohost <tryout_id> <member>` - Set another member as co-host
`!endtryout <tryout_id>` - End the tryout and process results
            """,
            inline=False
        )

        # Score Management
        embed.add_field(
            name="📊 Score Commands",
            value="""
`!addscore <tryout_id> <member> <points>` - Add points to a participant
`!removescore <tryout_id> <member> <points>` - Remove points from a participant
`!addscoreall <tryout_id> <points>` - Add points to all participants
`!removescoreall <tryout_id> <points>` - Remove points from all participants
`!showpoints <tryout_id>` - Display current points of all participants
            """,
            inline=False
        )

        embed.set_footer(text="Only the host and co-host can use these commands")
        await ctx.send(embed=embed)

async def setup(bot):
    cog = Tryout(bot)
    cog.pool = bot.pool  # Assuming you've set bot.pool in your main bot file
    await cog.load_tryouts_from_db()  # Load any active tryouts
    await bot.add_cog(cog)

#just to restart the bot
