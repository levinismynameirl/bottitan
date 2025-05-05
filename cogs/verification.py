import discord
from discord.ext import commands
import random
import string
from captcha.image import ImageCaptcha
import tempfile
import asyncio
import os

# Role IDs
ROLE_ID_UNOFFICIAL_PERSONNEL = 1303661603006447736  # Replace with your actual role ID
ROLE_ID_AWAITING_TRYOUT = 1303662669626081300  # Replace with your actual role ID

class CaptchaVerification(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log_channel_id = 1310173771633791037  # Replace with your log channel ID

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Trigger CAPTCHA verification when a new member joins."""
        try:
            # Generate CAPTCHA
            captcha_text = self.generate_captcha_text()
            captcha_image = self.generate_captcha_image(captcha_text)

            # Create DM channel
            try:
                dm_channel = await member.create_dm()
            except discord.Forbidden:
                print(f"Could not send DM to {member}. Ensure the user has DMs enabled.")
                return

            # Create embed with CAPTCHA
            embed = discord.Embed(
                title="CAPTCHA Verification",
                description=(
                    "Hello! To prove you are not a bot, please complete this CAPTCHA verification test.\n\n"
                    "Type the text shown in the image below. You may retake this test as many times as needed until you get it right."
                ),
                color=discord.Color.blue()
            )
            embed.set_image(url="attachment://captcha.png")

            # Send the embed with the CAPTCHA image
            await dm_channel.send(embed=embed, file=discord.File(captcha_image, "captcha.png"))

            # Wait for the user's response
            def check_captcha(m):
                return m.author == member and m.channel == dm_channel

            try:
                captcha_response = await self.bot.wait_for("message", timeout=120.0, check=check_captcha)
                if captcha_response.content.strip().upper() == captcha_text.upper():
                    # Correct CAPTCHA
                    await dm_channel.send("✅ Correct! You have passed the CAPTCHA verification.")
                    await member.add_roles(
                        discord.Object(id=ROLE_ID_UNOFFICIAL_PERSONNEL),
                        discord.Object(id=ROLE_ID_AWAITING_TRYOUT)
                    )
                    await dm_channel.send("✅ Verification complete! You now have access to the server.")
                    await self.log_verification_result(member, success=True)
                else:
                    # Incorrect CAPTCHA
                    await dm_channel.send("❌ Incorrect CAPTCHA. Please try again.")
                    await self.log_verification_result(member, success=False)
                    await self.on_member_join(member)  # Restart the process
            except asyncio.TimeoutError:
                await dm_channel.send("❌ You took too long to respond. Please try again.")
                await self.log_verification_result(member, success=False)
                await self.on_member_join(member)  # Restart the process
        finally:
            # Clean up the CAPTCHA image file
            if captcha_image:
                try:
                    os.remove(captcha_image)
                except Exception as e:
                    print(f"Error deleting CAPTCHA image: {e}")

    async def log_verification_result(self, member, success):
        """Log the result of the CAPTCHA verification."""
        log_channel = self.bot.get_channel(self.log_channel_id)
        if not log_channel:
            print("Log channel not found. Please check the channel ID.")
            return

        embed = discord.Embed(
            title="CAPTCHA Verification Result",
            description=(
                f"**User:** {member.mention}\n"
                f"**Result:** {'✅ Passed' if success else '❌ Failed'}"
            ),
            color=discord.Color.green() if success else discord.Color.red(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text=f"User ID: {member.id}")
        await log_channel.send(embed=embed)

    def generate_captcha_text(self):
        """Generate random text for the CAPTCHA."""
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

    def generate_captcha_image(self, text):
        """Generate a CAPTCHA image."""
        image = ImageCaptcha()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
            image_path = temp_file.name
            image.write(text, image_path)
        return image_path

    @commands.command(name="testcaptcha")
    @commands.has_permissions(administrator=True)  # Restrict to administrators or specific roles
    async def testcaptcha(self, ctx, member: discord.Member):
        """Manually trigger CAPTCHA verification for a specific user."""
        try:
            # Generate CAPTCHA
            captcha_text = self.generate_captcha_text()
            captcha_image = self.generate_captcha_image(captcha_text)

            # Create DM channel
            try:
                dm_channel = await member.create_dm()
            except discord.Forbidden:
                await ctx.send(f"❌ Could not send DM to {member.mention}. Ensure the user has DMs enabled.")
                return

            # Create embed with CAPTCHA
            embed = discord.Embed(
                title="CAPTCHA Verification (Test)",
                description=(
                    "Hello! This is a test CAPTCHA verification. Please type the text shown in the image below."
                ),
                color=discord.Color.blue()
            )
            embed.set_image(url="attachment://captcha.png")

            # Send the embed with the CAPTCHA image
            await dm_channel.send(embed=embed, file=discord.File(captcha_image, "captcha.png"))

            # Wait for the user's response
            def check_captcha(m):
                return m.author == member and m.channel == dm_channel

            try:
                captcha_response = await self.bot.wait_for("message", timeout=120.0, check=check_captcha)
                if captcha_response.content.strip().upper() == captcha_text.upper():
                    # Correct CAPTCHA
                    await dm_channel.send("✅ Correct! You have passed the CAPTCHA verification.")
                    await ctx.send(f"✅ {member.mention} successfully passed the CAPTCHA test.")
                    await self.log_verification_result(member, success=True)
                else:
                    # Incorrect CAPTCHA
                    await dm_channel.send("❌ Incorrect CAPTCHA. Please try again.")
                    await ctx.send(f"❌ {member.mention} failed the CAPTCHA test.")
                    await self.log_verification_result(member, success=False)
            except asyncio.TimeoutError:
                await dm_channel.send("❌ You took too long to respond. Please try again.")
                await ctx.send(f"❌ {member.mention} did not respond in time.")
                await self.log_verification_result(member, success=False)
        finally:
            # Clean up the CAPTCHA image file
            if captcha_image:
                try:
                    os.remove(captcha_image)
                except Exception as e:
                    print(f"Error deleting CAPTCHA image: {e}")

async def setup(bot):
    await bot.add_cog(CaptchaVerification(bot))