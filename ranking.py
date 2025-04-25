import discord
from discord.ext import commands, tasks
from datetime import datetime
import asyncio
import asyncpg
import os
from database import create_pool, initialize_database

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
    @commands.has_role(Official_Member)
    async def startshift(self, ctx):
        try:
            dm = await ctx.author.create_dm()
            embed = discord.Embed(
                title="Start Shift",
                description="React ✅ to start or ❌ to cancel.\n⚠️ Video proof required.",
                color=discord.Color.orange()
            )
            msg = await dm.send(embed=embed)
            await msg.add_reaction("✅")
            await msg.add_reaction("❌")

            def check(reaction, user): 
                return user == ctx.author and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == msg.id

            reaction, _ = await self.bot.wait_for("reaction_add", timeout=60, check=check)

            if str(reaction.emoji) == "✅":
                start_time = datetime.utcnow()
                self.active_shifts[ctx.author.id] = start_time

                progress_embed = discord.Embed(
                    title="Shift In Progress",
                    description="⏸️ Pause | ▶️ Resume | ⏹️ Stop\n⚠️ Video proof required.",
                    color=discord.Color.green()
                )
                progress_embed.add_field(name="Minutes Since Start", value="0", inline=False)
                shift_msg = await dm.send(embed=progress_embed)
                await shift_msg.add_reaction("⏸️")
                await shift_msg.add_reaction("▶️")
                await shift_msg.add_reaction("⏹️")

                self.shift_embeds[ctx.author.id] = shift_msg
                paused = False

                @tasks.loop(minutes=1)
                async def update_embed():
                    if ctx.author.id in self.active_shifts:
                        elapsed_time = datetime.utcnow() - self.active_shifts[ctx.author.id]
                        minutes = elapsed_time.total_seconds() // 60
                        progress_embed.set_field_at(0, name="Minutes Since Start", value=str(int(minutes)), inline=False)
                        await shift_msg.edit(embed=progress_embed)

                update_embed.start()

                def shift_check(r, u): 
                    return u == ctx.author and str(r.emoji) in ["⏸️", "▶️", "⏹️"] and r.message.id == shift_msg.id

                while True:
                    r, _ = await self.bot.wait_for("reaction_add", check=shift_check)
                    if r.emoji == "⏸️":
                        if not paused:
                            paused = True
                            update_embed.stop()
                            await dm.send("⏸️ Paused.")
                        else:
                            await dm.send("❌ Already paused.")
                    elif r.emoji == "▶️":
                        if paused:
                            paused = False
                            update_embed.start()
                            await dm.send("▶️ Resumed.")
                        else:
                            await dm.send("❌ Already running.")
                    elif r.emoji == "⏹️":
                        update_embed.stop()
                        elapsed = datetime.utcnow() - self.active_shifts.pop(ctx.author.id)
                        minutes = int(elapsed.total_seconds() // 60)
                        print(f"DEBUG: Shift ended for user_id {ctx.author.id}. Minutes: {minutes}")  # Debugging message
                        await self.add_shift_points(ctx.author.id, minutes, minutes)
                        await dm.send(f"⏹️ Stopped. You earned {minutes} points.")
                        break
            else:
                await dm.send("❌ Shift start canceled.")

        except asyncio.TimeoutError:
            await ctx.send("❌ Timed out.")
        except discord.Forbidden:
            await ctx.send("❌ I couldn't DM you. Enable DMs.")

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

async def setup(bot):
    cog = Ranking(bot)
    await bot.add_cog(cog)
    await cog.setup_db()  # Ensure the database is set up when the cog is loaded
    print("✅ Ranking cog loaded and database set up.")