import discord
from discord.ext import commands
from datetime import datetime, timedelta

class ActivityReport(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def activityreport(self, ctx):
        """Generate an activity report for all members with the 'Official Member' role."""
        official_member_role = ctx.guild.get_role(1346557689303662633)  # Replace with the ID of the 'Official Member' role
        loa_role = ctx.guild.get_role(1313895372828967054)  # Replace with the ID of the 'LOA' role

        if not official_member_role:
            await ctx.send("❌ 'Official Member' role not found. Please check the role ID.")
            return

        report = []
        now = datetime.utcnow()
        seven_days_ago = now - timedelta(days=7)

        for member in ctx.guild.members:
            if official_member_role in member.roles:
                # Calculate days in the server
                days_in_server = (now - member.joined_at).days if member.joined_at else "Unknown"

                # Check LOA status
                loa_status = "Yes" if loa_role in member.roles else "No"

                # Count messages sent in the past 7 days
                message_count = 0
                for channel in ctx.guild.text_channels:
                    if channel.permissions_for(ctx.guild.me).read_messages:
                        try:
                            async for message in channel.history(after=seven_days_ago, limit=1000):
                                if message.author == member:
                                    message_count += 1
                        except discord.Forbidden:
                            continue

                # Calculate last active time (in hours)
                last_active = "Unknown"
                for channel in ctx.guild.text_channels:
                    if channel.permissions_for(ctx.guild.me).read_messages:
                        try:
                            async for message in channel.history(limit=1):
                                if message.author == member:
                                    last_active = (now - message.created_at).total_seconds() // 3600
                                    break
                        except discord.Forbidden:
                            continue

                # Add member's data to the report
                report.append(
                    f"**{member.display_name}**\n"
                    f"- Last Active: {last_active} hours ago\n"
                    f"- Messages Sent (7 days): {message_count}\n"
                    f"- Days in Server: {days_in_server}\n"
                    f"- LOA: {loa_status}\n"
                )

        # Send the report
        if report:
            embed = discord.Embed(
                title="Activity Report",
                description="\n\n".join(report[:10]),  # Limit to the first 10 members to avoid exceeding embed limits
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ No members with the 'Official Member' role found.")

async def setup(bot):
    await bot.add_cog(ActivityReport(bot))