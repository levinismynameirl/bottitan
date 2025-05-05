import discord
from discord.ext import commands, tasks
from datetime import datetime
import asyncio
import asyncpg
import os
from database import create_pool, initialize_database
from discord.ui import View, Button

Official_Member = 1346557689303662633  # Replace with the actual role ID

class Ranking(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_shifts = {}
        self.shift_embeds = {}
        self.pool = None  # DB pool

    async def setup_db(self):
        if not self.pool:
            try:
                print("DEBUG: Initializing database connection pool...")  # Debugging message
                self.pool = await create_pool()
                await initialize_database(self.pool)
                print("DEBUG: Database connection pool initialized.")  # Debugging message
            except Exception as e:
                print(f"❌ Failed to initialize database: {e}")

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.pool:
            await self.setup_db()
            print("✅ Connected to the database.")

    async def add_points(self, user_id: int, amount: int):
        """Add points to a user."""
        async with self.pool.acquire() as conn:
            try:
                user_id = str(user_id)  # Convert user_id to string
                print(f"DEBUG: Adding {amount} points to user_id {user_id}")  # Debugging message
                await conn.execute("""
                    INSERT INTO points (user_id, points)
                    VALUES ($1, $2)
                    ON CONFLICT (user_id)
                    DO UPDATE SET points = points.points + EXCLUDED.points;
                """, user_id, amount)
                print(f"DEBUG: Successfully added {amount} points to user_id {user_id}")  # Debugging message
            except Exception as e:
                print(f"❌ Failed to add points for user_id {user_id}: {e}")

    async def get_points(self, user_id: int) -> int:
        """Fetch points for a user."""
        async with self.pool.acquire() as conn:
            try:
                user_id = str(user_id)  # Convert user_id to string
                print(f"DEBUG: Fetching points for user_id {user_id}")  # Debugging message
                row = await conn.fetchrow("SELECT points FROM points WHERE user_id = $1;", user_id)
                points = row['points'] if row else 0
                print(f"DEBUG: Points fetched for user_id {user_id}: {points}")  # Debugging message
                return points
            except Exception as e:
                print(f"❌ Failed to fetch points for user_id {user_id}: {e}")
                return 0

    async def set_points(self, user_id: int, amount: int):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO points (user_id, points)
                VALUES ($1, $2)
                ON CONFLICT (user_id)
                DO UPDATE SET points = $2;
            """, user_id, amount)

    async def add_shift_points(self, user_id: int, points: int, minutes: int):
        """Add points and update the time column for a user after a shift."""
        async with self.pool.acquire() as conn:
            try:
                user_id = str(user_id)  # Convert user_id to string
                print(f"DEBUG: Adding {points} points and {minutes} minutes to user_id {user_id}")  # Debugging message
                await conn.execute("""
                    INSERT INTO points (user_id, points)
                    VALUES ($1, $2)
                    ON CONFLICT (user_id)
                    DO UPDATE SET points = points.points + EXCLUDED.points;
                """, user_id, points)
                print(f"DEBUG: Successfully added {points} points and {minutes} minutes to user_id {user_id}")  # Debugging message
            except Exception as e:
                print(f"❌ Failed to add shift points for user_id {user_id}: {e}")

    @commands.command()
    @commands.has_role(Official_Member)  # Replace with the actual role name or ID
    async def startshift(self, ctx):
        """Start a shift."""
        try:
            # Check if the user already has an active shift
            if ctx.author.id in self.active_shifts:
                await ctx.send("❌ You already have an active shift. Please stop your current shift before starting a new one.")
                return

            # Create confirmation view with buttons
            confirm_view = View(timeout=60)
            confirm_button = Button(style=discord.ButtonStyle.green, label="Start Shift", emoji="✅")
            cancel_button = Button(style=discord.ButtonStyle.red, label="Cancel", emoji="❌")
            
            confirm_view.add_item(confirm_button)
            confirm_view.add_item(cancel_button)
            
            # Define what happens when each button is pressed
            async def confirm_callback(interaction):
                if interaction.user != ctx.author:
                    return
                
                await interaction.response.defer()  # Acknowledge the interaction
                
                # Start the shift
                start_time = datetime.utcnow()
                self.active_shifts[ctx.author.id] = start_time
                
                # Create shift control view with buttons
                control_view = View(timeout=None)  # Persistent view
                pause_button = Button(style=discord.ButtonStyle.blurple, label="Pause", emoji="⏸️")
                resume_button = Button(style=discord.ButtonStyle.green, label="Resume", emoji="▶️", disabled=True)
                stop_button = Button(style=discord.ButtonStyle.red, label="Stop", emoji="⏹️")
                
                control_view.add_item(pause_button)
                control_view.add_item(resume_button)
                control_view.add_item(stop_button)
                
                progress_embed = discord.Embed(
                    title="Shift In Progress",
                    description="Use the buttons below to control your shift.\n⚠️ You may be asked to provide video proof of each shift up to a week after the shift ends. (This is a requirement for all shifts.)",
                    color=discord.Color.green()
                )
                progress_embed.add_field(name="Minutes Since Start", value="0", inline=False)
                
                # Send the shift control panel
                shift_msg = await interaction.followup.send(embed=progress_embed, view=control_view)
                
                paused = False
                
                @tasks.loop(minutes=1)
                async def update_embed():
                    if ctx.author.id in self.active_shifts:
                        elapsed_time = datetime.utcnow() - self.active_shifts[ctx.author.id]
                        minutes = elapsed_time.total_seconds() // 60
                        progress_embed.set_field_at(0, name="Minutes Since Start", value=str(int(minutes)), inline=False)
                        try:
                            await shift_msg.edit(embed=progress_embed)
                        except discord.NotFound:
                            update_embed.cancel()
                
                update_embed.start()
                
                # Define button callbacks
                async def pause_callback(interaction):
                    nonlocal paused
                    if interaction.user != ctx.author:
                        return
                    
                    await interaction.response.defer()
                    
                    if not paused:
                        paused = True
                        update_embed.stop()
                        pause_button.disabled = True
                        resume_button.disabled = False
                        await shift_msg.edit(view=control_view)
                        await interaction.followup.send("⏸️ Shift paused.")
                    else:
                        await interaction.followup.send("❌ Already paused.")
                
                async def resume_callback(interaction):
                    nonlocal paused
                    if interaction.user != ctx.author:
                        return
                    
                    await interaction.response.defer()
                    
                    if paused:
                        paused = False
                        update_embed.start()
                        pause_button.disabled = False
                        resume_button.disabled = True
                        await shift_msg.edit(view=control_view)
                        await interaction.followup.send("▶️ Shift resumed.")
                    else:
                        await interaction.followup.send("❌ Already running.")
                
                async def stop_callback(interaction):
                    if interaction.user != ctx.author:
                        return
                    
                    await interaction.response.defer()
                    
                    update_embed.stop()
                    control_view.stop()
                    
                    for item in control_view.children:
                        item.disabled = True
                    await shift_msg.edit(view=control_view)
                    
                    elapsed = datetime.utcnow() - self.active_shifts.pop(ctx.author.id)
                    minutes = int(elapsed.total_seconds() // 60)
                    print(f"DEBUG: Shift ended for user_id {ctx.author.id}. Minutes: {minutes}")
                    
                    await self.add_shift_points(ctx.author.id, minutes, minutes)
                    await interaction.followup.send(f"⏹️ Shift stopped. You earned {minutes} points.")
                
                # Attach callbacks to buttons
                pause_button.callback = pause_callback
                resume_button.callback = resume_callback
                stop_button.callback = stop_callback
                
                # Stop the confirmation view since we've started the shift
                confirm_view.stop()
            
            async def cancel_callback(interaction):
                if interaction.user != ctx.author:
                    return
                await interaction.response.send_message("❌ Shift start canceled.")
                confirm_view.stop()
            
            # Attach callbacks to confirmation buttons
            confirm_button.callback = confirm_callback
            cancel_button.callback = cancel_callback
            
            # Create and send the confirmation message
            dm = await ctx.author.create_dm()
            embed = discord.Embed(
                title="Start Shift",
                description="Click the button below to start or cancel.\n⚠️ Video proof required.",
                color=discord.Color.orange()
            )
            await dm.send(embed=embed, view=confirm_view)
            
            # Wait for the view to timeout or stop
            await confirm_view.wait()
            
            if not confirm_view.is_finished():
                await dm.send("❌ Timed out.")
                
        except discord.Forbidden:
            await ctx.send("❌ I couldn't DM you. Enable DMs.")
        except Exception as e:
            print(f"❌ Error in startshift command: {e}")
            await ctx.send(f"❌ An error occurred: {e}")

    @commands.command()
    async def points(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        print(f"DEBUG: Fetching points for {member.display_name} (ID: {member.id})")  # Debugging message
        points = await self.get_points(member.id)
        print(f"DEBUG: Points for {member.display_name}: {points}")  # Debugging message
        await ctx.send(f"**{member.display_name}** has **{points}** points.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def addpoints(self, ctx, member: discord.Member, amount: int):
        await self.add_points(member.id, amount)
        await ctx.send(f"✅ Added {amount} points to {member.mention}.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def removepoints(self, ctx, member: discord.Member, amount: int):
        current = await self.get_points(member.id)
        new_points = max(0, current - amount)
        await self.set_points(member.id, new_points)
        await ctx.send(f"✅ Removed {amount} points from {member.mention}.")

    async def get_loa_users(self):
        """Fetch users on LOA from the database or other storage."""
        # Replace this with your actual logic to fetch LOA users
        # For example, if stored in a database:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("SELECT user_id FROM loa_users;")
            return [row["user_id"] for row in rows]

async def setup(bot):
    cog = Ranking(bot)
    await bot.add_cog(cog)
    await cog.setup_db()  # Ensure the database is set up when the cog is loaded
    print("✅ Ranking cog loaded and database set up.")