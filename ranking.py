import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
import asyncio
import asyncpg

DATABASE_URL = "postgresql://postgres:jAHFxyiZVaVQAujHMPOLBtlMHZTbllTa@postgres.railway.internal:5432/railway"

async def initialize_database():
    """Initialize the PostgreSQL database."""
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS points (
            user_id BIGINT PRIMARY KEY,
            points INT DEFAULT 0
        );
    """)
    await conn.close()
    print("✅ Database initialized successfully.")

class Ranking(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_shifts = {}  # Tracks active shifts for users
        self.shift_embeds = {}  # Tracks the embed messages for active shifts

    async def connect_db(self):
        """Connect to the database."""
        return await asyncpg.connect(DATABASE_URL)

    @commands.command()
    @commands.has_role("Official Member")
    async def startshift(self, ctx):
        """Start a shift."""
        # Send a DM to the user for confirmation
        try:
            dm_channel = await ctx.author.create_dm()
            embed = discord.Embed(
                title="Start Shift",
                description=(
                    "React with ✅ to start your shift or ❌ to cancel.\n\n"
                    "⚠️ **Important:** You must always have video proof of your shift, as you may be asked for it."
                ),
                color=discord.Color.orange()
            )
            message = await dm_channel.send(embed=embed)
            await message.add_reaction("✅")
            await message.add_reaction("❌")

            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == message.id

            reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
            if str(reaction.emoji) == "✅":
                # Start the shift
                start_time = datetime.utcnow()
                self.active_shifts[ctx.author.id] = start_time

                # Send an embed that updates every minute
                embed = discord.Embed(
                    title="Shift In Progress",
                    description=(
                        "Your shift has started. React below to control your shift:\n"
                        "⏸️ **Pause**\n"
                        "▶️ **Resume**\n"
                        "⏹️ **Stop**\n\n"
                        "⚠️ **Important:** You must always have video proof of your shift, as you may be asked for it."
                    ),
                    color=discord.Color.green()
                )
                embed.add_field(name="Minutes Since Start", value="0", inline=False)
                shift_message = await dm_channel.send(embed=embed)
                await shift_message.add_reaction("⏸️")
                await shift_message.add_reaction("▶️")
                await shift_message.add_reaction("⏹️")

                self.shift_embeds[ctx.author.id] = shift_message

                # Update the embed every minute
                @tasks.loop(minutes=1)
                async def update_embed():
                    if ctx.author.id in self.active_shifts:
                        elapsed_time = datetime.utcnow() - self.active_shifts[ctx.author.id]
                        minutes = elapsed_time.total_seconds() // 60
                        embed.set_field_at(0, name="Minutes Since Start", value=str(int(minutes)), inline=False)
                        await shift_message.edit(embed=embed)

                update_embed.start()

                # Handle reactions for pause, resume, and stop
                paused = False

                def shift_check(reaction, user):
                    return user == ctx.author and str(reaction.emoji) in ["⏸️", "▶️", "⏹️"] and reaction.message.id == shift_message.id

                while True:
                    reaction, user = await self.bot.wait_for("reaction_add", check=shift_check)

                    if str(reaction.emoji) == "⏸️":
                        if not paused:
                            paused = True
                            update_embed.stop()
                            await dm_channel.send("⏸️ Your shift has been paused.", delete_after=5)
                        else:
                            await dm_channel.send("❌ Your shift is already paused.", delete_after=5)

                    elif str(reaction.emoji) == "▶️":
                        if paused:
                            paused = False
                            update_embed.start()
                            await dm_channel.send("▶️ Your shift has been resumed.", delete_after=5)
                        else:
                            await dm_channel.send("❌ Your shift is already active.", delete_after=5)

                    elif str(reaction.emoji) == "⏹️":
                        update_embed.stop()
                        elapsed_time = datetime.utcnow() - self.active_shifts.pop(ctx.author.id)
                        minutes = int(elapsed_time.total_seconds() // 60)

                        # Add points to the user
                        await self.add_points(ctx.author.id, minutes)

                        await dm_channel.send(
                            f"⏹️ Your shift has been stopped. You earned {minutes} points.\n"
                            "⚠️ **Important:** You must always have video proof of your shift, as you may be asked for it."
                        )
                        break

            elif str(reaction.emoji) == "❌":
                await dm_channel.send("❌ Shift start canceled.")
        except asyncio.TimeoutError:
            await ctx.send("❌ You took too long to respond. Shift start canceled.")
        except discord.Forbidden:
            await ctx.send("❌ I could not send you a DM. Please enable DMs and try again.")

    async def add_points(self, user_id, points):
        """Add points to a user."""
        conn = await self.connect_db()
        await conn.execute(
            """
            INSERT INTO points (user_id, points)
            VALUES ($1, $2)
            ON CONFLICT (user_id) DO UPDATE
            SET points = points + $2
            """,
            user_id, points
        )
        await conn.close()

    @commands.command()
    async def points(self, ctx, member: discord.Member = None):
        """View the points of a user."""
        member = member or ctx.author
        conn = await self.connect_db()
        row = await conn.fetchrow("SELECT points FROM points WHERE user_id = $1", member.id)
        await conn.close()

        points = row["points"] if row else 0
        await ctx.send(f"**{member.display_name}** has **{points}** points.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def addpoints(self, ctx, member: discord.Member, points: int):
        """Add points to a user (Administrator only)."""
        await self.add_points(member.id, points)
        await ctx.send(f"✅ Added {points} points to {member.mention}.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def removepoints(self, ctx, member: discord.Member, points: int):
        """Remove points from a user (Administrator only)."""
        conn = await self.connect_db()
        await conn.execute(
            """
            UPDATE points
            SET points = points - $1
            WHERE user_id = $2
            """,
            points, member.id
        )
        await conn.close()
        await ctx.send(f"✅ Removed {points} points from {member.mention}.")

async def setup(bot):
    await bot.add_cog(Ranking(bot))