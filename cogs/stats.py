import discord
from discord.ext import commands, tasks
import logging

class ServerStats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.guild_id = 1303444948523155627
        self.total_members_channel_id = 1303806216073515008
        self.members_channel_id = 1303806219265376258
        self.boosts_channel_id = 1303806223618932776

        # Initialize stats as None
        self.previous_total_members = None
        self.previous_members = None
        self.previous_boosts = None

        # Start the task
        self.first_update = True
        self.update_stats.start()

    def cog_unload(self):
        self.update_stats.cancel()

    async def force_update_channels(self, guild):
        """Force update all channels once"""
        try:
            total_members = guild.member_count
            members = sum(1 for member in guild.members if not member.bot)
            boosts = guild.premium_subscription_count

            # Update total members
            total_members_channel = guild.get_channel(self.total_members_channel_id)
            if total_members_channel:
                await total_members_channel.edit(name=f"Total Members: {total_members}")
                self.previous_total_members = total_members

            # Update members
            members_channel = guild.get_channel(self.members_channel_id)
            if members_channel:
                await members_channel.edit(name=f"Members: {members}")
                self.previous_members = members

            # Update boosts
            boosts_channel = guild.get_channel(self.boosts_channel_id)
            if boosts_channel:
                await boosts_channel.edit(name=f"Boosts: {boosts}")
                self.previous_boosts = boosts

            print(f"Stats updated - Total: {total_members}, Members: {members}, Boosts: {boosts}")
            return True

        except discord.Forbidden:
            print("Missing permissions to edit channels")
            return False
        except Exception as e:
            print(f"Error updating stats: {str(e)}")
            return False

    @tasks.loop(minutes=5)
    async def update_stats(self):
        """Update the stats channels every 5 minutes if there are changes."""
        try:
            guild = self.bot.get_guild(self.guild_id)
            if not guild:
                print(f"Guild with ID {self.guild_id} not found.")
                return

            # Force update on first run
            if self.first_update:
                await self.force_update_channels(guild)
                self.first_update = False
                return

            # Get current stats
            total_members = guild.member_count
            members = sum(1 for member in guild.members if not member.bot)
            boosts = guild.premium_subscription_count

            # Check for changes and update
            if total_members != self.previous_total_members:
                channel = guild.get_channel(self.total_members_channel_id)
                if channel:
                    await channel.edit(name=f"Total Members: {total_members}")
                    print(f"Updated total members: {total_members}")
                self.previous_total_members = total_members

            if members != self.previous_members:
                channel = guild.get_channel(self.members_channel_id)
                if channel:
                    await channel.edit(name=f"Members: {members}")
                    print(f"Updated members: {members}")
                self.previous_members = members

            if boosts != self.previous_boosts:
                channel = guild.get_channel(self.boosts_channel_id)
                if channel:
                    await channel.edit(name=f"Boosts: {boosts}")
                    print(f"Updated boosts: {boosts}")
                self.previous_boosts = boosts

        except Exception as e:
            print(f"Error in update_stats: {str(e)}")

    @update_stats.before_loop
    async def before_update_stats(self):
        """Wait until the bot is ready before starting the loop."""
        await self.bot.wait_until_ready()
        print("Stats update loop is starting...")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def forceupdate(self, ctx):
        """Force update the stats channels."""
        guild = self.bot.get_guild(self.guild_id)
        if guild:
            success = await self.force_update_channels(guild)
            if success:
                await ctx.send("✅ Stats channels have been forcefully updated.")
            else:
                await ctx.send("❌ Failed to update stats channels.")
        else:
            await ctx.send("❌ Guild not found.")

async def setup(bot):
    await bot.add_cog(ServerStats(bot))