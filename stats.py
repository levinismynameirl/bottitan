import discord
from discord.ext import commands, tasks

class ServerStats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.guild_id = 1303444948523155627  # Replace with your server's ID
        self.total_members_channel_id = 1303806216073515008  # Replace with the ID of the Total Members channel
        self.members_channel_id = 1303806219265376258  # Replace with the ID of the Members channel
        self.boosts_channel_id = 1303806223618932776  # Replace with the ID of the Boosts channel

        # Store previous stats to detect changes
        self.previous_total_members = None
        self.previous_members = None
        self.previous_boosts = None

        self.update_stats.start()

    def cog_unload(self):
        self.update_stats.cancel()

    @tasks.loop(minutes=5)
    async def update_stats(self):
        """Update the stats channels every 5 minutes if there are changes."""
        guild = self.bot.get_guild(self.guild_id)
        if not guild:
            print(f"Guild with ID {self.guild_id} not found.")
            return

        # Get the current stats
        total_members = guild.member_count
        members = sum(1 for member in guild.members if not member.bot)
        boosts = guild.premium_subscription_count

        # Check for changes before updating channels
        if total_members != self.previous_total_members:
            total_members_channel = guild.get_channel(self.total_members_channel_id)
            if total_members_channel:
                await total_members_channel.edit(name=f"Total Members: {total_members}")
            self.previous_total_members = total_members

        if members != self.previous_members:
            members_channel = guild.get_channel(self.members_channel_id)
            if members_channel:
                await members_channel.edit(name=f"Members: {members}")
            self.previous_members = members

        if boosts != self.previous_boosts:
            boosts_channel = guild.get_channel(self.boosts_channel_id)
            if boosts_channel:
                await boosts_channel.edit(name=f"Boosts: {boosts}")
            self.previous_boosts = boosts

    @update_stats.before_loop
    async def before_update_stats(self):
        """Wait until the bot is ready before starting the loop."""
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(ServerStats(bot))