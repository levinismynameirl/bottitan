import discord
from discord.ext import commands
import asyncio
from datetime import datetime, timedelta


"""

WARNING:


THE LINES BELOW MAY CONTAIN SLURS OR OTHER OFFENSIVE LANGUAGE.
THEY ARE ONLY HERE FOR AUTOMOD PURPOSES.

PROCEED WITH CAUTION.



SKIP TO LINE 107 FOR THE CODE.





















YOU HAVE BEEN WARNED.






























































"""


class AutoMod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bad_words = [
            "cunt", "whore"
            "nigger", "nigga", "niga", "retard", "slut", "thisisatestbadwordtoseeifthebotworks"
        ]  # Add actual bad words here
        self.muted_role_name = "Muted"  # Name of the mute role

    @commands.Cog.listener()
    async def on_message(self, message):
        """Detect bad words in messages."""
        if message.author.bot:
            return  # Ignore bot messages

        # Check for bad words
        if any(bad_word in message.content.lower() for bad_word in self.bad_words):
            await message.delete()  # Delete the message
            await self.handle_bad_word(message)

    async def handle_bad_word(self, message):
        """Handle a message containing bad words."""
        guild = message.guild
        user = message.author

        # Delete the message containing the bad word
        await message.delete()

        # Get the warning channel
        warning_channel = self.bot.get_channel(1310173771633791037)  # Replace with your warning channel ID
        if not warning_channel:
            print("Warning channel not found. Please check the channel ID.")
            return

        # Notify admins in the warning channel
        admin_roles = [1303797966657814579, 1303798167799599175]  # Replace with actual role IDs
        admin_mentions = " ".join([role.mention for role in guild.roles if role.id in admin_roles])

        embed = discord.Embed(
            title="Bad Word Detected",
            description=(
                f"**User:** {user.mention}\n"
                f"**Message:** {message.content}\n\n"
                f"Choose an action for this user:\n"
                f"1️⃣ Mute\n"
                f"2️⃣ Kick\n"
                f"3️⃣ Ban"
            ),
            color=discord.Color.red()
        )
        embed.set_footer(text="React with the appropriate emoji to take action.")

        # Send the embed to the warning channel
        notification_message = await warning_channel.send(admin_mentions, embed=embed)

        # Add reaction options
        await notification_message.add_reaction("1️⃣")  # Mute
        await notification_message.add_reaction("2️⃣")  # Kick
        await notification_message.add_reaction("3️⃣")  # Ban

        def check(reaction, user):
            return (
                user != self.bot.user
                and str(reaction.emoji) in ["1️⃣", "2️⃣", "3️⃣"]
                and reaction.message.id == notification_message.id
            )

        try:
            reaction, admin_user = await self.bot.wait_for("reaction_add", timeout=300.0, check=check)
        except asyncio.TimeoutError:
            await warning_channel.send("❌ No action was taken in time.")
            return

        # Handle the selected action
        if str(reaction.emoji) == "1️⃣":
            await self.mute_user(message, admin_user)
        elif str(reaction.emoji) == "2️⃣":
            await self.kick_user(message, admin_user)
        elif str(reaction.emoji) == "3️⃣":
            await self.ban_user(message, admin_user)

    async def mute_user(self, message, admin_user):
        """Mute the user."""
        guild = message.guild
        user = message.author

        # Ask for mute duration
        await message.channel.send(f"{admin_user.mention}, how long should the mute last? (e.g., `10m`, `1h`, `1d`)")

        def duration_check(m):
            return m.author == admin_user and m.channel == message.channel

        try:
            duration_message = await self.bot.wait_for("message", timeout=300.0, check=duration_check)
            duration = self.parse_duration(duration_message.content)
        except asyncio.TimeoutError:
            await message.channel.send("❌ No duration was provided. Mute canceled.")
            return
        except ValueError:
            await message.channel.send("❌ Invalid duration format. Mute canceled.")
            return

        # Ask for a reason
        await message.channel.send(f"{admin_user.mention}, please provide a reason for the mute:")

        def reason_check(m):
            return m.author == admin_user and m.channel == message.channel

        try:
            reason_message = await self.bot.wait_for("message", timeout=300.0, check=reason_check)
            reason = reason_message.content
        except asyncio.TimeoutError:
            await message.channel.send("❌ No reason was provided. Mute canceled.")
            return

        # Mute the user
        muted_role = discord.utils.get(guild.roles, name=self.muted_role_name)
        if not muted_role:
            muted_role = await guild.create_role(name=self.muted_role_name)
            for channel in guild.channels:
                await channel.set_permissions(muted_role, send_messages=False, speak=False)

        await user.add_roles(muted_role)
        await message.channel.send(f"✅ {user.mention} has been muted for {duration_message.content}. Reason: {reason}")

        # Notify the user
        try:
            await user.send(f"You have been muted in **{guild.name}** for {duration_message.content}. Reason: {reason}")
        except discord.Forbidden:
            pass

        # Unmute the user after the duration
        await asyncio.sleep(duration)
        await user.remove_roles(muted_role)
        await message.channel.send(f"✅ {user.mention} has been unmuted.")

    async def kick_user(self, message, admin_user):
        """Kick the user."""
        guild = message.guild
        user = message.author

        # Ask for a reason
        await message.channel.send(f"{admin_user.mention}, please provide a reason for the kick:")

        def reason_check(m):
            return m.author == admin_user and m.channel == message.channel

        try:
            reason_message = await self.bot.wait_for("message", timeout=300.0, check=reason_check)
            reason = reason_message.content
        except asyncio.TimeoutError:
            await message.channel.send("❌ No reason was provided. Kick canceled.")
            return

        # Kick the user
        await user.kick(reason=reason)
        await message.channel.send(f"✅ {user.mention} has been kicked. Reason: {reason}")

        # Notify the user
        try:
            await user.send(f"You have been kicked from **{guild.name}**. Reason: {reason}")
        except discord.Forbidden:
            pass

    async def ban_user(self, message, admin_user):
        """Ban the user."""
        guild = message.guild
        user = message.author

        # Ask for a reason
        await message.channel.send(f"{admin_user.mention}, please provide a reason for the ban:")

        def reason_check(m):
            return m.author == admin_user and m.channel == message.channel

        try:
            reason_message = await self.bot.wait_for("message", timeout=300.0, check=reason_check)
            reason = reason_message.content
        except asyncio.TimeoutError:
            await message.channel.send("❌ No reason was provided. Ban canceled.")
            return

        # Ban the user
        await user.ban(reason=reason)
        await message.channel.send(f"✅ {user.mention} has been banned. Reason: {reason}")

        # Notify the user
        try:
            await user.send(f"You have been banned from **{guild.name}**. Reason: {reason}")
        except discord.Forbidden:
            pass

    def parse_duration(self, duration_str):
        """Parse a duration string into seconds."""
        unit_multipliers = {"m": 60, "h": 3600, "d": 86400}
        try:
            unit = duration_str[-1]
            value = int(duration_str[:-1])
            return value * unit_multipliers[unit]
        except (ValueError, KeyError):
            raise ValueError("Invalid duration format")

async def setup(bot):
    await bot.add_cog(AutoMod(bot))