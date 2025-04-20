import discord
from discord.ext import commands
import random
import datetime

class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx):
        """Check the bot's latency."""
        latency = round(self.bot.latency * 1000)  # Convert to milliseconds
        await ctx.send(f"🏓 Pong! Latency: {latency}ms")

    @commands.command()
    async def roll(self, ctx, dice: str = "1d6"):
        """Rolls a dice in NdN format (e.g., 2d6)."""
        try:
            rolls, sides = map(int, dice.split("d"))
        except ValueError:
            await ctx.send("❌ Format has to be in NdN (e.g., 2d6).")
            return

        results = [random.randint(1, sides) for _ in range(rolls)]
        await ctx.send(f"🎲 You rolled: {', '.join(map(str, results))} (Total: {sum(results)})")

    @commands.command()
    async def flip(self, ctx):
        """Flips a coin."""
        result = random.choice(["Heads", "Tails"])
        await ctx.send(f"🪙 The coin landed on: **{result}**")

    @commands.command()
    async def choose(self, ctx, *choices):
        """Randomly chooses between multiple options."""
        if not choices:
            await ctx.send("❌ You need to provide some options to choose from!")
            return
        choice = random.choice(choices)
        await ctx.send(f"🤔 I choose: **{choice}**")

    @commands.command()
    async def avatar(self, ctx, member: discord.Member = None):
        """Displays the avatar of a user."""
        member = member or ctx.author
        await ctx.send(f"🖼️ {member.mention}'s avatar: {member.avatar.url}")

    @commands.command()
    async def serverinfo(self, ctx):
        """Displays information about the server."""
        guild = ctx.guild
        embed = discord.Embed(
            title=f"Server Info: {guild.name}",
            color=discord.Color.blue()
        )
        embed.add_field(name="Owner", value=guild.owner, inline=False)
        embed.add_field(name="Members", value=guild.member_count, inline=False)
        embed.add_field(name="Created On", value=guild.created_at.strftime("%B %d, %Y"), inline=False)
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
        await ctx.send(embed=embed)

    @commands.command()
    async def userinfo(self, ctx, member: discord.Member = None):
        """Displays information about a user."""
        member = member or ctx.author
        embed = discord.Embed(
            title=f"User Info: {member.name}",
            color=discord.Color.green()
        )
        embed.add_field(name="ID", value=member.id, inline=False)
        embed.add_field(name="Joined Server", value=member.joined_at.strftime("%B %d, %Y"), inline=False)
        embed.add_field(name="Account Created", value=member.created_at.strftime("%B %d, %Y"), inline=False)
        embed.set_thumbnail(url=member.avatar.url)
        await ctx.send(embed=embed)

    @commands.command()
    async def dadjoke(self, ctx):
        """Sends a random dad joke."""
        jokes = [
            "Why don't skeletons fight each other? They don't have the guts.",
            "What do you call fake spaghetti? An impasta.",
            "How do you organize a space party? You planet.",
            "Did you hear about the kidnapping at the park? They woke up.",
            "I'm reading a book on anti-gravity. It's impossible to put down.",
            "I'm on a seafood diet. I see food and I eat it.",
            "Why don't eggs tell jokes? They might crack up.",
            "I only know 25 letters of the alphabet. I don't know y.",
            "I used to be a baker, but I couldn't make enough dough.",
            "Why don't scientists trust atoms? Because they make up everything.",
            "What did the buffalo say when his son left? Bison.",
            "Why did the scarecrow win an award? Because he was outstanding in his field.",
            "What do you call a bear with no teeth? A gummy bear.",
            "Parallel lines have so much in common. It’s a shame they’ll never meet.",
            "Why don't eggs tell jokes? They might crack up."
        ]
        await ctx.send(f"😂 {random.choice(jokes)}")

    @commands.command()
    async def fact(self, ctx):
        """Sends a random fun fact."""
        facts = [
            "Honey never spoils. Archaeologists have found pots of honey in ancient Egyptian tombs that are over 3,000 years old and still edible!",
            "Octopuses have three hearts.",
            "Bananas are berries, but strawberries aren't.",
            "A group of flamingos is called a 'flamboyance'."
        ]
        await ctx.send(f"📚 Fun Fact: {random.choice(facts)}")

    @commands.command()
    async def reverse(self, ctx, *, text: str):
        """Reverses the given text."""
        reversed_text = text[::-1]
        await ctx.send(f"🔄 {reversed_text}")

    @commands.command()
    async def say(self, ctx, *, message: str):
        """Repeats the user's message."""
        await ctx.send(message)

    @commands.command()
    async def time(self, ctx):
        """Displays the current time."""
        now = datetime.datetime.now()
        await ctx.send(f"🕒 The current time is: {now.strftime('%H:%M:%S')}")

    @commands.command()
    async def rps(self, ctx, choice: str):
        """Play Rock, Paper, Scissors with the bot."""
        choices = ["rock", "paper", "scissors"]
        if choice.lower() not in choices:
            await ctx.send("❌ Please choose rock, paper, or scissors.")
            return
        bot_choice = random.choice(choices)
        result = None
        if choice.lower() == bot_choice:
            result = "It's a tie!"
        elif (choice.lower() == "rock" and bot_choice == "scissors") or \
             (choice.lower() == "paper" and bot_choice == "rock") or \
             (choice.lower() == "scissors" and bot_choice == "paper"):
            result = "You win!"
        else:
            result = "I win!"
        await ctx.send(f"🤖 I chose {bot_choice}. {result}")

    @commands.command()
    async def rate(self, ctx, *, thing: str):
        """Rates something out of 10."""
        rating = random.randint(1, 10)
        await ctx.send(f"🤔 I rate **{thing}** a **{rating}/10**!")

async def setup(bot):
    await bot.add_cog(Misc(bot))