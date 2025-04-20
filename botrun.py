import discord
import asyncio
from discord.ext import commands
from dotenv import load_dotenv
import os
from ranking import initialize_database

# Load environment variables from .env file
print("Loading environment variables...")
load_dotenv()
print("Environment variables loaded.")

# Get the bot token from the environment variable
TOKEN = os.getenv("DISCORD_TOKEN")

# Enable required intents
intents = discord.Intents.default()
intents.message_content = True  # Required for message commands
intents.members = True  # Required to fetch members

# Create bot instance
bot = commands.Bot(command_prefix="!", intents=intents)

# Load extensions (cogs) before the bot starts
async def load_extensions():
    """Loads all extensions (cogs) before running the bot."""
    await bot.load_extension("moderation")  # Load the Moderation cog
    await bot.load_extension("ranking")  # Load the Ranking cog
    await bot.load_extension("misc")  # Load the Misc cog
    await bot.load_extension("antiraid")  # Load the AntiRaid cog
    await bot.load_extension("automod")  # Load the AutoMod cog

# Event when the bot is ready
@bot.event
async def on_ready():
    await initialize_database()  # Initialize the PostgreSQL database
    print(f"✅ Logged in as {bot.user}")

# Main entry point to run the bot
async def main():
    # Load extensions before starting the bot
    await load_extensions()

    # Start the bot using its token (using environment variable for safety)
    await bot.start(TOKEN)

# Run the bot
if __name__ == "__main__":
    asyncio.run(main())  # Run the async main function
