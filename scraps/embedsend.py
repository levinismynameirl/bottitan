import discord
from discord.ext import commands

class EmbedSend(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def sendrules(self, ctx):
        """Send the rules as embeds to the guidelines channel."""
        channel = self.bot.get_channel(1303811292292845621)  # Replace with your guidelines channel ID
        if not channel:
            await ctx.send("❌ Guidelines channel not found. Please check the channel ID.")
            return

        # Ping everyone
        await channel.send("@everyone")

        # Rules as embeds
        rules = [
            {
                "title": "𝐖𝐄𝐋𝐂𝐎𝐌𝐄",
                "description": (
                    "Welcome to Mobile Task Force Titan ~ 1's official Discord server! "
                    "We are a MTF faction in the Roblox game, SCP:RP.\n\n"
                    "Please read the rules below thoroughly and follow them at all times to ensure full operation in our server!"
                ),
                "color": discord.Color.blue()
            },
            {
                "title": "Rule - I: Discord Terms of Service",
                "description": "You are required to know and agree with Discord’s ToS. (https://discord.com/terms)",
                "color": discord.Color.green()
            },
            {
                "title": "Rule - II: Respecting other members",
                "description": "Respect all members regardless of religion, beliefs, gender, race, etc. Refrain from discriminating against people.",
                "color": discord.Color.green()
            },
            {
                "title": "Rule - III: Swearing",
                "description": "Swearing is permitted up to a certain point. Direct swearing (cursing another person) isn’t allowed.",
                "color": discord.Color.green()
            },
            {
                "title": "Rule - IV: Verbal Slurs",
                "description": "We strictly prohibit any type of verbal slurs. Please never say one in any type of context.",
                "color": discord.Color.green()
            },
            {
                "title": "Rule - V: Spamming",
                "description": (
                    "Chat Spamming/Flooding is considered an infraction and will lead to a mute. "
                    "This includes polls with 5 or more answers; giant messages with no relevance to the current subject; "
                    "emoji/sticker/gif spam."
                ),
                "color": discord.Color.green()
            },
            {
                "title": "Rule - VI: Respecting orders given by higher ranks",
                "description": (
                    "You are obligated to respect any order given by a higher rank. "
                    "If you believe the order breaks our rules, take it up higher in the chain of command."
                ),
                "color": discord.Color.green()
            },
            {
                "title": "Rule - VII: NSFW/Adult Content",
                "description": (
                    "Please do not post any Adult/NSFW content in this server as it is strictly prohibited and can result "
                    "in a permanent ban if done. This includes NSFW profile pictures, names, banners, etc."
                ),
                "color": discord.Color.green()
            },
            {
                "title": "Rule - IX: Advertising without proper permission",
                "description": "Any and all forms of advertising are prohibited unless done in specific channels.",
                "color": discord.Color.green()
            },
            {
                "title": "Rule - X: Loud Sounds in Voice Channels",
                "description": (
                    "Please refrain from making any type of loud or disturbing sounds in Voice Channels. "
                    "This includes sounds that could cause potential ear damage."
                ),
                "color": discord.Color.green()
            },
            {
                "title": "Rule - XI: Malicious Content/Computer Malware Sharing",
                "description": "Please do not post any link or file that could harm another member’s device/steal data.",
                "color": discord.Color.green()
            },
            {
                "title": "Rule - XII: Shit Pinging",
                "description": (
                    "Do not ping people randomly. This includes spam pinging a Hi-COM personnel to check an application "
                    "you made (unless specifically stated that you can ping them)."
                ),
                "color": discord.Color.green()
            },
            {
                "title": "Rule - XIII: Drama",
                "description": "Do not start any unnecessary drama or arguments within the server as it is prohibited.",
                "color": discord.Color.green()
            },
            {
                "title": "Rule - XIV: Politics",
                "description": "Do not talk/debate about politics in our server.",
                "color": discord.Color.green()
            },
            {
                "title": "🛈 Additional Information 🛈",
                "description": (
                    "╰┈➤If you believe you or another person were over or under punished, please report to a Hi-COM personnel.\n\n"
                    "╰┈➤If you have any questions about the rules, please ask an appropriate staff member."
                ),
                "color": discord.Color.blue()
            }
        ]

        # Send each rule as an embed
        for rule in rules:
            embed = discord.Embed(
                title=rule["title"],
                description=rule["description"],
                color=rule["color"]
            )
            await channel.send(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def sendprocedures(self, ctx):
        """Send the general procedures as separate embeds to the procedures channel."""
        channel = self.bot.get_channel(1363867306152693930)  # Replace with your procedures channel ID
        if not channel:
            await ctx.send("❌ Procedures channel not found. Please check the channel ID.")
            print("DEBUG: Procedures channel not found. Channel ID:", 1363867306152693930)
            return

        # Debug message to confirm the channel is found
        print("DEBUG: Procedures channel found:", channel.name)

        # General Procedures as a list of numbered procedures
        procedures = [
            {
                "title": "1. Listening to Higher Ranks",
                "description": (
                    "You are obliged to respect a higher rank’s decision when deployed. "
                    "If you believe they ordered you to do something absurd or against protocol, "
                    "take it to the Executive Command Board (ECB)."
                ),
                "color": discord.Color.orange()
            },
            {
                "title": "2. Reacting to Important Announcements",
                "description": (
                    "Any important announcements marked with a ✅ by the message owner in any official unit channel "
                    "must be acknowledged by reacting with the same checkmark emoji."
                ),
                "color": discord.Color.orange()
            },
            {
                "title": "3. Chain of Command in Field Operations",
                "description": (
                    "The highest-ranking operative in a deployed squad assumes command unless otherwise assigned. "
                    "All disputes must be handled post-operation."
                ),
                "color": discord.Color.orange()
            },
            {
                "title": "4. Comms Protocol",
                "description": (
                    "Maintain radio discipline. Only mission-relevant communication is permitted. "
                    "All comms must be concise. Violators will be logged."
                ),
                "color": discord.Color.orange()
            },
            {
                "title": "5. Uniform Code",
                "description": (
                    "Wear your assigned uniform and proper unit insignia while on duty. "
                    "Unauthorized cosmetics are forbidden without Unit Advisor approval."
                ),
                "color": discord.Color.orange()
            },
            {
                "title": "6. Weapon Draw Protocol",
                "description": (
                    "Only draw your weapon during active patrol, breach alerts, or direct engagement orders. "
                    "Do not aim at other Titan-1 members without cause."
                ),
                "color": discord.Color.orange()
            },
            {
                "title": "7. Inter-Unit Respect",
                "description": (
                    "All units are to be treated with professional respect. Equal standing unless otherwise declared by ECB."
                ),
                "color": discord.Color.orange()
            },
            {
                "title": "8. Intel Handling Protocol",
                "description": (
                    "Report all enemy plans, leaks, or POI data immediately via official channels. "
                    "Withholding intel is a protocol breach."
                ),
                "color": discord.Color.orange()
            },
            {
                "title": "9. Silent Entry / Extraction",
                "description": (
                    "Especially for Nightfall and Sentinel units — enter/exit zones quietly. "
                    "Do not alert enemies or compromise stealth."
                ),
                "color": discord.Color.orange()
            },
            {
                "title": "10. Respect the Uniform Off-Duty",
                "description": (
                    "Your actions reflect on Titan-1. Trolling or misconduct while representing Titan-1 can lead to punishment or demotion."
                ),
                "color": discord.Color.orange()
            },
            {
                "title": "11. Operation Approval Protocol",
                "description": (
                    "No operations may begin (raids, assassinations, POI-level missions) without ECB approval."
                ),
                "color": discord.Color.orange()
            }
        ]

        # Send each procedure as a separate embed
        for procedure in procedures:
            embed = discord.Embed(
                title=procedure["title"],
                description=procedure["description"],
                color=procedure["color"]
            )
            await channel.send(embed=embed)

        # Additional Unit-Specific Protocols
        unit_protocols = [
            {
                "title": "🥷 1st Nightfall Unit – Covert Operations Protocol",
                "description": (
                    "_“Strike from the shadows. Eliminate with silence.”_\n"
                    "- Operate as a ghost. Visibility is failure.\n"
                    "- All targets must be ECB or mission-lead approved.\n"
                    "- Use suppressors. Loud weapons are only for emergencies.\n"
                    "- Prioritize headshots, stealth, and silent exits.\n"
                    "- Avoid unnecessary conflict.\n"
                    "- Never reveal your presence unless ordered.\n"
                    "- Assassinations must avoid triggering alarms unless permitted.\n"
                    "- Operate solo or in pairs — no large groups.\n"
                    "- Eliminate witnesses if required. Clean your trail.\n"
                    "- Breach points must be pre-scouted for surprise."
                ),
                "color": discord.Color.purple()
            },
            {
                "title": "🛡 2nd Vanguard Unit – Frontline Combat Protocol",
                "description": (
                    "_“We hold the ground. No one takes it from us.”_\n"
                    "- Seize and secure high-value areas.\n"
                    "- Breach first, clear fast, and hold strong.\n"
                    "- After securing, fortify and defend.\n"
                    "- Use barricades and crossfire lanes if possible.\n"
                    "- Never abandon position without orders.\n"
                    "- Be flexible — offense to defense instantly.\n"
                    "- Call threats fast — request medics or Sentinel backup.\n"
                    "- You control the battlefield’s tempo.\n"
                    "- Always prepare for second waves. Stay stocked."
                ),
                "color": discord.Color.purple()
            },
            {
                "title": "🛡‍🔥 3rd Sentinel Unit – Escort and Defense Protocol",
                "description": (
                    "_“You don’t talk. You don’t flinch. You don’t fail.”_\n"
                    "- Never break squad leader’s formation.\n"
                    "- Your life is second to the POI’s.\n"
                    "- No talking during guard duty, unless to report threats.\n"
                    "- Remain still, alert, and composed.\n"
                    "- If approached by unauthorized personnel:\n"
                    "  • Issue: `Back off` (once)\n"
                    "  • Two warnings max. Then: warning shot.\n"
                    "  • If they’re armed: One warning only.\n"
                    "  • If they aim: Terminate immediately.\n"
                    "- No arguments. Silence is authority.\n"
                    "- Never leave POIs unattended — not for a second.\n"
                    "- You are the shield. You may die, but the POI must not.\n"
                    "- Secure all perimeters at all times.\n"
                    "- For POI meetings:\n"
                    "  • Escort without exception.\n"
                    "  • Take position at the entrance.\n"
                    "  • Deny entry to all without explicit POI or Hi-COM permission.\n"
                    "  • Warn unauthorized entrants once. Escalate as per protocol."
                ),
                "color": discord.Color.purple()
            }
        ]

        # Send each unit-specific protocol as a separate embed
        for protocol in unit_protocols:
            embed = discord.Embed(
                title=protocol["title"],
                description=protocol["description"],
                color=protocol["color"]
            )
            await channel.send(embed=embed)


async def setup(bot):
    await bot.add_cog(EmbedSend(bot))