import discord
from discord.ext import commands, tasks
import asyncio
import random
import string
from datetime import datetime, timedelta

class AntiRaid(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.join_times = []  # Track member join times
        self.raid_active = False
        self.admin_ids = [920314437179674694, 1133038563047514192]  # Admin IDs to notify
        self.alert_channel_id = 1303811999146315806  # Channel to send raid alerts
        self.muted_role_name = "Muted"  # Name of the mute role
        self.new_members = []  # Track new members during a raid
        self.average_joins_per_minute = 0  # Track average joins per minute

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Triggered when a new member joins the server."""
        if self.raid_active:
            # If a raid is active, immediately mute the new member
            await self.mute_member(member)
            return

        # Add the current time to the join_times list
        self.join_times.append(datetime.now())

        # Update the average joins per minute
        self.update_average_joins()

        # Check for a potential raid
        await self.check_for_raid(member.guild)

    def update_average_joins(self):
        """Update the average joins per minute."""
        one_minute_ago = datetime.now() - timedelta(minutes=1)
        recent_joins = [time for time in self.join_times if time > one_minute_ago]
        self.average_joins_per_minute = len(recent_joins)

    async def check_for_raid(self, guild):
        """Check if the server is experiencing a raid."""
        # Remove join times older than 1 minute
        one_minute_ago = datetime.now() - timedelta(minutes=1)
        self.join_times = [time for time in self.join_times if time > one_minute_ago]

        # Trigger a potential raid if the join rate is 2-3 times the average
        if len(self.join_times) > self.average_joins_per_minute * 2 and not self.raid_active:
            self.raid_active = True
            await self.trigger_potential_raid(guild)

    async def trigger_potential_raid(self, guild):
        """Trigger a potential raid alert."""
        # Set slowmode to 10 seconds for all channels
        for channel in guild.text_channels:
            try:
                await channel.edit(slowmode_delay=10)
            except discord.Forbidden:
                continue

        # Notify admins via DM
        for admin_id in self.admin_ids:
            admin = await self.bot.fetch_user(admin_id)
            try:
                await self.send_raid_confirmation(admin, guild)
            except discord.Forbidden:
                continue

    async def send_raid_confirmation(self, admin, guild):
        """Send a DM to an admin to confirm the raid."""
        confirmation_string = ''.join(random.choices(string.ascii_letters + string.digits, k=10))

        embed = discord.Embed(
            title="Potential Raid Detected",
            description=(
                f"The server **{guild.name}** is experiencing a high influx of members.\n\n"
                f"To confirm the raid, type the following string exactly as shown:\n\n"
                f"**{confirmation_string}**"
            ),
            color=discord.Color.red()
        )
        embed.set_footer(text="This is case-sensitive.")

        await admin.send(embed=embed)

        def check(message):
            return message.author.id == admin.id and message.content == confirmation_string

        while True:
            try:
                confirmation_message = await self.bot.wait_for("message", timeout=300.0, check=check)
                if confirmation_message.content == confirmation_string:
                    await self.start_raid_protection(guild)
                    break
            except asyncio.TimeoutError:
                await admin.send("❌ You did not confirm the raid in time. The raid protection was not activated.")
                await self.activate_soft_raid_protection(guild)
                return

    async def start_raid_protection(self, guild):
        """Start raid protection."""
        # Set slowmode to 5 minutes for all channels
        for channel in guild.text_channels:
            try:
                await channel.edit(slowmode_delay=300)
            except discord.Forbidden:
                continue

        # Notify the alert channel
        alert_channel = guild.get_channel(self.alert_channel_id)
        if alert_channel:
            await alert_channel.send(
                f"@everyone 🚨 **Raid Alert!** The server is currently experiencing a raid. "
                f"All new members will be muted until the raid is resolved."
            )

        # Mute all new members
        for member in self.new_members:
            await self.mute_member(member)

        # Notify admins to stop the raid feature
        for admin_id in self.admin_ids:
            admin = await self.bot.fetch_user(admin_id)
            await self.send_stop_raid_prompt(admin, guild)

    async def activate_soft_raid_protection(self, guild):
        """Activate soft raid protection if no confirmation is received."""
        # Set slowmode to 30 seconds for all channels
        for channel in guild.text_channels:
            try:
                await channel.edit(slowmode_delay=30)
            except discord.Forbidden:
                continue

        # Notify the alert channel
        alert_channel = guild.get_channel(self.alert_channel_id)
        if alert_channel:
            await alert_channel.send(
                "⚠️ **Soft Raid Protection Activated:** The server is experiencing unusual activity. "
                "Admins have not confirmed a raid yet."
            )

    async def send_stop_raid_prompt(self, admin, guild):
        """Send a DM to an admin to stop the raid feature."""
        confirmation_string = ''.join(random.choices(string.ascii_letters + string.digits, k=10))

        embed = discord.Embed(
            title="Stop Raid Protection?",
            description=(
                f"The raid protection for **{guild.name}** is currently active.\n\n"
                f"To stop the raid protection, type the following string exactly as shown:\n\n"
                f"**{confirmation_string}**"
            ),
            color=discord.Color.orange()
        )
        embed.set_footer(text="This is case-sensitive.")

        await admin.send(embed=embed)

        def check(message):
            return message.author.id == admin.id and message.content == confirmation_string

        while True:
            try:
                confirmation_message = await self.bot.wait_for("message", timeout=300.0, check=check)
                if confirmation_message.content == confirmation_string:
                    await self.stop_raid_protection(guild)
                    break
            except asyncio.TimeoutError:
                await admin.send("❌ You did not confirm to stop the raid protection in time.")
                return

    async def stop_raid_protection(self, guild):
        """Stop raid protection."""
        self.raid_active = False

        # Reset slowmode for all channels
        for channel in guild.text_channels:
            try:
                await channel.edit(slowmode_delay=0)
            except discord.Forbidden:
                continue

        # Notify the alert channel
        alert_channel = guild.get_channel(self.alert_channel_id)
        if alert_channel:
            await alert_channel.send("✅ **Raid protection has been deactivated.**")

        # Unmute all new members
        for member in self.new_members:
            await self.unmute_member(member)

        # Clear the list of new members
        self.new_members.clear()

    async def mute_member(self, member):
        """Mute a member by assigning the 'Muted' role."""
        muted_role = discord.utils.get(member.guild.roles, name=self.muted_role_name)
        if not muted_role:
            # Create the Muted role if it doesn't exist
            muted_role = await member.guild.create_role(name=self.muted_role_name)
            for channel in member.guild.channels:
                await channel.set_permissions(muted_role, send_messages=False, speak=False)

        await member.add_roles(muted_role)
        self.new_members.append(member)

    async def unmute_member(self, member):
        """Unmute a member by removing the 'Muted' role."""
        muted_role = discord.utils.get(member.guild.roles, name=self.muted_role_name)
        if muted_role in member.roles:
            await member.remove_roles(muted_role)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def manualraid(self, ctx):
        """Manually activate the raid security system."""
        await self.trigger_potential_raid(ctx.guild)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def testraid(self, ctx):
        """Test the raid security system."""
        # Set slowmode to 2 seconds for all channels
        for channel in ctx.guild.text_channels:
            try:
                await channel.edit(slowmode_delay=2)
            except discord.Forbidden:
                continue

        # Notify the alert channel
        alert_channel = ctx.guild.get_channel(self.alert_channel_id)
        if alert_channel:
            await alert_channel.send(
                "**Raid Test:** This is a test of the raid security system. No action is required."
            )

async def setup(bot):
    await bot.add_cog(AntiRaid(bot))