import discord
from discord.ext import commands, tasks
import random
import datetime
import asyncio

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
    async def reminder(self, ctx, time: str, *, reminder: str):
        """Set a reminder (e.g., !reminder 10m Take a break)."""
        try:
            duration = self.parse_duration(time)
        except ValueError:
            await ctx.send("❌ Invalid time format. Use `10s`, `5m`, `1h`, etc.")
            return

        await ctx.send(f"⏰ Reminder set for {time}. I'll remind you to: {reminder}")
        await asyncio.sleep(duration)
        await ctx.send(f"🔔 {ctx.author.mention}, reminder: {reminder}")

    def parse_duration(self, time_str):
        """Parse a duration string into seconds."""
        unit_multipliers = {"s": 1, "m": 60, "h": 3600}
        unit = time_str[-1]
        value = int(time_str[:-1])
        return value * unit_multipliers[unit]

    @commands.command()
    async def trivia(self, ctx):
        """Start a trivia game."""
        questions = [
            {
                "question": "What is the capital of France?",
                "options": ["1. Paris", "2. London", "3. Berlin", "4. Madrid"],
                "answer": "1"
            },
            {
                "question": "Who wrote 'To Kill a Mockingbird'?",
                "options": ["1. Harper Lee", "2. J.K. Rowling", "3. Ernest Hemingway", "4. Mark Twain"],
                "answer": "1"
            },
            {
                "question": "What is the largest planet in our solar system?",
                "options": ["1. Earth", "2. Mars", "3. Jupiter", "4. Saturn"],
                "answer": "3"
            },
            {
                "question": "What year did World War II end?",
                "options": ["1. 1942", "2. 1945", "3. 1948", "4. 1950"],
                "answer": "2"
            },
            {
                "question": "What is the chemical symbol for water?",
                "options": ["1. H2O", "2. CO2", "3. O2", "4. NaCl"],
                "answer": "1"
            }
        ]

        question = random.choice(questions)
        embed = discord.Embed(
            title="Trivia Time!",
            description=f"{question['question']}\n\n" + "\n".join(question["options"]),
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            answer = await self.bot.wait_for("message", timeout=30.0, check=check)
            if answer.content == question["answer"]:
                await ctx.send("🎉 Correct!")
            else:
                await ctx.send(f"❌ Wrong! The correct answer was {question['answer']}.")
        except asyncio.TimeoutError:
            await ctx.send("⏰ Time's up! You didn't answer in time.")

    @commands.command()
    async def guess(self, ctx):
        """Play a number guessing game."""
        number = random.randint(1, 100)
        await ctx.send("🎲 I'm thinking of a number between 1 and 100. Can you guess it?")

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.isdigit()

        while True:
            try:
                guess = await self.bot.wait_for("message", timeout=30.0, check=check)
                guess = int(guess.content)
                if guess < number:
                    await ctx.send("🔼 Higher!")
                elif guess > number:
                    await ctx.send("🔽 Lower!")
                else:
                    await ctx.send(f"🎉 Correct! The number was {number}.")
                    break
            except asyncio.TimeoutError:
                await ctx.send(f"⏰ Time's up! The number was {number}.")
                break

    @commands.command()
    async def dice_duel(self, ctx, opponent: discord.Member):
        """Challenge another user to a dice duel."""
        await ctx.send(f"🎲 {ctx.author.mention} challenges {opponent.mention} to a dice duel!")

        player_roll = random.randint(1, 6)
        opponent_roll = random.randint(1, 6)

        await ctx.send(f"{ctx.author.mention} rolled a {player_roll}.")
        await ctx.send(f"{opponent.mention} rolled a {opponent_roll}.")

        if player_roll > opponent_roll:
            await ctx.send(f"🎉 {ctx.author.mention} wins!")
        elif player_roll < opponent_roll:
            await ctx.send(f"🎉 {opponent.mention} wins!")
        else:
            await ctx.send("🤝 It's a tie!")

    @commands.command()
    async def scramble(self, ctx):
        """Play a word scramble game."""
        words = ["python", "discord", "bot", "programming", "developer", "apple", "snake", "banana", "orange", "pig", "computer", "code", "java", "mouse", "keyboard", "monitor", "cloud", "server", "network", "wifi", "robot", "android", "software", "hardware", "binary", "laptop", "engineer", "script", "terminal", "compile", "debug", "function", "variable", "loop", "condition", "algorithm", "array", "list", "dictionary", "string",
"integer", "float", "boolean", "package", "module", "github", "repository", "commit", "push", "pull",
"branch", "merge", "clone", "token", "api", "request", "response", "json", "xml", "url",
"socket", "firewall", "encryption", "cyber", "security", "malware", "phishing", "trojan", "hacker", "firefox",
"chrome", "browser", "search", "engine", "google", "bing", "yahoo", "internet", "web", "page",
"html", "css", "javascript", "framework", "react", "vue", "angular", "node", "express", "database",
"mysql", "sqlite", "postgres", "mongodb", "query", "index", "table", "row", "column", "data"
] 
        word = random.choice(words)
        scrambled = "".join(random.sample(word, len(word)))

        await ctx.send(f"🔤 Unscramble this word: **{scrambled}**")

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            answer = await self.bot.wait_for("message", timeout=30.0, check=check)
            if answer.content.lower() == word:
                await ctx.send("🎉 Correct!")
            else:
                await ctx.send(f"❌ Wrong! The correct word was **{word}**.")
        except asyncio.TimeoutError:
            await ctx.send(f"⏰ Time's up! The correct word was **{word}**.")

async def setup(bot):
    await bot.add_cog(Misc(bot))