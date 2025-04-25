print("Starting the bot...")
print("-------------------------------")

print("Importing required libraries...")
import discord
import asyncio
from discord.ext import commands
from dotenv import load_dotenv
import os
from ranking import initialize_database
print("Libraries imported successfully.")

# Load environment variables from .env file
print("Loading environment variables...")
load_dotenv()
print("Environment variables loaded.")

# Get the bot token from the environment variable
print("Fetching Discord token...")
TOKEN = os.getenv("DISCORD_TOKEN")
print("Discord token fetched.")
if not TOKEN:
    raise ValueError("No token provided. Please set the DISCORD_TOKEN environment variable.")

print("Initializing intents...")
# Enable required intents
intents = discord.Intents.default()
intents.message_content = True  # Required for message commands
intents.members = True  # Required to fetch members
print("Intents initialized.")

# Create bot instance
print("Creating bot instance...")
bot = commands.Bot(command_prefix="!", intents=intents)
print("Bot instance created.")

# Load extensions (cogs) before the bot starts
print("Loading all files...")
async def load_extensions():
    """Loads all extensions (cogs) before running the bot."""
    await bot.load_extension("moderation")  # Load the Moderation cog
    await bot.load_extension("ranking")  # Load the Ranking cog
    await bot.load_extension("misc")  # Load the Misc cog
    await bot.load_extension("antiraid")  # Load the AntiRaid cog
    await bot.load_extension("automod")  # Load the AutoMod cog
    await bot.load_extension("verification")  # Load the Captcha cog
    await bot.load_extension("embedsend")  # Load the EmbedSend cog
    await bot.load_extension("stats")  # Load the ServerStats cog
    await bot.load_extension("activityreport")  # Load the ActivityReport cog
print("All files loaded successfully.")

# Event when the bot is ready
print("Setting up event listeners...")
print("Setting up database...")
@bot.event
async def on_ready():
    await initialize_database()  # Initialize the PostgreSQL database
    print(f"✅ Logged in as {bot.user}")
print("Event listeners set up successfully.")
print("Database set up successfully.")
print("Bot is ready to run.")
print("-------------------------------")

print("Main function starting...")
# Main entry point to run the bot
async def main():
    # Load extensions before starting the bot
    await load_extensions()
    print("Main function executed successfully.")

    # Start the bot using its token (using environment variable for safety)
    
    await bot.start(TOKEN)
    

# Run the bot
print("Running the bot...")
print("Bot is running.")
print("-------------------------------")
print("Bot succesfully started")
if __name__ == "__main__":
    asyncio.run(main())  # Run the async main function

