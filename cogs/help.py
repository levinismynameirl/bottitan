import discord
from discord.ext import commands
from typing import Optional, Dict, List

class CustomHelp(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.remove_command('help')  # Remove default help command
        
        # Define category descriptions
        self.categories = {
            "Moderation": "Server moderation and management commands",
            "Tryout": "Tryout system and management",
            "Ranking": "Points and shift management",
            "Utility": "General utility commands",
            "Stats": "Server statistics",
            "Security": "Server security and protection",
            "Verification": "User verification system"
        }
        
        # Define commands and their categories
        self.command_categories = {
            # Moderation Commands
            "lock": "Moderation",
            "unlock": "Moderation",
            "slowmode": "Moderation",
            "clear": "Moderation",
            "kick": "Moderation",
            "ban": "Moderation",
            "unban": "Moderation",
            "timeout": "Moderation",
            "mute": "Moderation",
            "unmute": "Moderation",
            
            # Tryout Commands
            "tryoutstart": "Tryout",
            "setcohost": "Tryout",
            "endtryout": "Tryout",
            "addscore": "Tryout",
            "removescore": "Tryout",
            "addscoreall": "Tryout",
            "removescoreall": "Tryout",
            "showpoints": "Tryout",
            "helptt": "Tryout",
            "approve": "Tryout",
            "deny": "Tryout",
            
            # Ranking Commands
            "startshift": "Ranking",
            "points": "Ranking",
            "addpoints": "Ranking",
            "removepoints": "Ranking",
            "loa": "Ranking",
            
            # Utility Commands
            "ping": "Utility",
            "roll": "Utility",
            "flip": "Utility",
            "reminder": "Utility",
            "trivia": "Utility",
            "guess": "Utility",
            "dice_duel": "Utility",
            "scramble": "Utility",
            
            # Security Commands
            "manualraid": "Security",
            "testraid": "Security",
            
            # Verification Commands
            "testcaptcha": "Verification"
        }

    def can_run_command(self, ctx: commands.Context, command: commands.Command) -> bool:
        """Check if user can run a command"""
        try:
            return command.can_run(ctx)
        except:
            return False

    @commands.command()
    async def help(self, ctx, category_or_command: Optional[str] = None):
        """Show help for all commands or a specific category/command."""
        
        if not category_or_command:
            # Show main help menu with categories
            embed = discord.Embed(
                title="Bot Help Menu",
                description="Use `!help <category>` to view commands in a category\nUse `!help <command>` for detailed command help",
                color=discord.Color.blue()
            )
            
            # Group commands by category and check permissions
            categorized_commands: Dict[str, List[commands.Command]] = {}
            for cmd in self.bot.commands:
                if not cmd.hidden and self.can_run_command(ctx, cmd):
                    category = self.command_categories.get(cmd.name, "Miscellaneous")
                    if category not in categorized_commands:
                        categorized_commands[category] = []
                    categorized_commands[category].append(cmd)
            
            # Add non-empty categories to embed
            for category, commands_list in categorized_commands.items():
                if commands_list:
                    command_names = [f"`{cmd.name}`" for cmd in commands_list]
                    embed.add_field(
                        name=f"{category} Commands",
                        value=f"{self.categories.get(category, 'Various commands')}\n{', '.join(command_names)}",
                        inline=False
                    )
            
        elif category_or_command in self.categories:
            # Show commands in specific category
            category = category_or_command
            embed = discord.Embed(
                title=f"{category} Commands",
                description=self.categories[category],
                color=discord.Color.green()
            )
            
            for cmd in self.bot.commands:
                if (self.command_categories.get(cmd.name) == category 
                    and not cmd.hidden 
                    and self.can_run_command(ctx, cmd)):
                    embed.add_field(
                        name=f"!{cmd.name} {cmd.signature}",
                        value=cmd.help or "No description available.",
                        inline=False
                    )
                    
        else:
            # Show help for specific command
            cmd = self.bot.get_command(category_or_command)
            if cmd and not cmd.hidden and self.can_run_command(ctx, cmd):
                embed = discord.Embed(
                    title=f"Command: !{cmd.name}",
                    description=cmd.help or "No description available.",
                    color=discord.Color.green()
                )
                
                # Add usage
                embed.add_field(
                    name="Usage",
                    value=f"!{cmd.name} {cmd.signature}",
                    inline=False
                )
                
                # Add aliases if any
                if cmd.aliases:
                    embed.add_field(
                        name="Aliases",
                        value=", ".join(cmd.aliases),
                        inline=False
                    )
                
                # Add category
                category = self.command_categories.get(cmd.name, "Miscellaneous")
                embed.add_field(
                    name="Category",
                    value=category,
                    inline=False
                )
            else:
                embed = discord.Embed(
                    title="Error",
                    description="Command or category not found or you don't have permission to use it.",
                    color=discord.Color.red()
                )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(CustomHelp(bot))