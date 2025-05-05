import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta

class AntiNuke(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.armed = True  # Anti-nuke system armed state by default on
        self.protected_users = [1133038563047514192, 920314437179674694]  # IDs of users who can arm/disarm
        self.deleted_channels = []  # Track deleted channels for restoration
        self.deleted_roles = []  # Track deleted roles for restoration
        self.pending_channel_deletions = {}  # Track pending channel deletions
        self.pending_role_deletions = {}  # Track pending role deletions
        self.pending_bot_additions = {}  # Track pending bot addition requests
        self.flagged_users = {}  # Track users flagged for excessive permission changes

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        """Triggered when a channel is deleted."""
        if self.armed:
            async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
                if entry.target.id == channel.id:
                    deleter = entry.user
                    break
            else:
                deleter = None

            if channel.id not in self.pending_channel_deletions:
                print(f"⚠️ Unauthorized channel deletion detected: {channel.name} (ID: {channel.id}) by {deleter}")
                self.deleted_channels.append((channel.name, channel.category, channel.position, channel.type, channel.overwrites))
                await self.restore_channels(channel.guild)
                await self.report_unauthorized_action(
                    channel.guild,
                    f"Channel deleted: {channel.name} (ID: {channel.id}) by {deleter.mention if deleter else 'Unknown'}"
                )
            else:
                del self.pending_channel_deletions[channel.id]

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        """Triggered when a role is deleted."""
        if self.armed:
            async for entry in role.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_delete):
                if entry.target.id == role.id:
                    deleter = entry.user
                    break
            else:
                deleter = None

            if role.id not in self.pending_role_deletions:
                print(f"⚠️ Unauthorized role deletion detected: {role.name} (ID: {role.id}) by {deleter}")
                self.deleted_roles.append((role.name, role.permissions, role.color, role.hoist, role.mentionable, role.guild_permissions))
                await self.restore_roles(role.guild)
                await self.report_unauthorized_action(
                    role.guild,
                    f"Role deleted: {role.name} (ID: {role.id}) by {deleter.mention if deleter else 'Unknown'}"
                )
            else:
                del self.pending_role_deletions[role.id]

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Triggered when a member joins the server."""
        if member.bot:
            async for entry in member.guild.audit_logs(limit=1, action=discord.AuditLogAction.bot_add):
                if entry.target.id == member.id:
                    adder = entry.user
                    break
            else:
                adder = None

            if member.id not in self.pending_bot_additions:
                print(f"⚠️ Unauthorized bot addition detected: {member.name} (ID: {member.id}) by {adder}")
                await member.kick(reason="Unauthorized bot addition")
                if adder:
                    await adder.edit(roles=[])
                    await self.report_unauthorized_action(
                        member.guild,
                        f"Bot added: {member.name} (ID: {member.id}) by {adder.mention if adder else 'Unknown'}"
                    )
            else:
                del self.pending_bot_additions[member.id]

    async def restore_channels(self, guild):
        """Restore deleted channels and their permissions."""
        for channel_data in self.deleted_channels:
            name, category, position, channel_type, overwrites = channel_data
            try:
                if channel_type == discord.ChannelType.text:
                    channel = await guild.create_text_channel(name, category=category, position=position)
                elif channel_type == discord.ChannelType.voice:
                    channel = await guild.create_voice_channel(name, category=category, position=position)
                await channel.edit(overwrites=overwrites)
                print(f"✅ Restored channel: {name}")
            except Exception as e:
                print(f"❌ Failed to restore channel {name}: {e}")
        self.deleted_channels.clear()

    async def restore_roles(self, guild):
        """Restore deleted roles and their permissions."""
        for role_data in self.deleted_roles:
            name, permissions, color, hoist, mentionable, guild_permissions = role_data
            try:
                role = await guild.create_role(
                    name=name,
                    permissions=permissions,
                    color=color,
                    hoist=hoist,
                    mentionable=mentionable
                )
                await role.edit(permissions=guild_permissions)
                print(f"✅ Restored role: {name}")
            except Exception as e:
                print(f"❌ Failed to restore role {name}: {e}")
        self.deleted_roles.clear()

    async def report_unauthorized_action(self, guild, message):
        """Report unauthorized actions to protected users."""
        for user_id in self.protected_users:
            user = guild.get_member(user_id)
            if user:
                try:
                    await user.send(f"⚠️ Unauthorized action detected: {message}")
                except discord.Forbidden:
                    print(f"❌ Could not DM user {user_id}")

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def delchannel(self, ctx, channel_id: int, *, reason: str):
        """Request to delete a channel."""
        if ctx.author.id in self.protected_users:
            channel = ctx.guild.get_channel(channel_id)
            if not channel:
                await ctx.send("❌ Channel not found.")
                return

            for user_id in self.protected_users:
                user = ctx.guild.get_member(user_id)
                if user:
                    try:
                        msg = await user.send(
                            f"⚠️ Request to delete channel: {channel.name} (ID: {channel.id})\nReason: {reason}\n"
                            f"React ✅ to approve or ❌ to deny."
                        )
                        await msg.add_reaction("✅")
                        await msg.add_reaction("❌")
                    except discord.Forbidden:
                        print(f"❌ Could not DM user {user_id}")

            self.pending_channel_deletions[channel_id] = ctx.author.id
            await ctx.send(f"✅ Deletion request for channel {channel.name} sent for approval.")
        else:
            await ctx.send("❌ You do not have permission to request channel deletions.")

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def delrole(self, ctx, role_id: int, *, reason: str):
        """Request to delete a role."""
        if ctx.author.id in self.protected_users:
            role = ctx.guild.get_role(role_id)
            if not role:
                await ctx.send("❌ Role not found.")
                return

            for user_id in self.protected_users:
                user = ctx.guild.get_member(user_id)
                if user:
                    try:
                        msg = await user.send(
                            f"⚠️ Request to delete role: {role.name} (ID: {role.id})\nReason: {reason}\n"
                            f"React ✅ to approve or ❌ to deny."
                        )
                        await msg.add_reaction("✅")
                        await msg.add_reaction("❌")
                    except discord.Forbidden:
                        print(f"❌ Could not DM user {user_id}")

            self.pending_role_deletions[role_id] = ctx.author.id
            await ctx.send(f"✅ Deletion request for role {role.name} sent for approval.")
        else:
            await ctx.send("❌ You do not have permission to request role deletions.")

    @commands.command()
    async def addbot(self, ctx, bot_id: int, *, reason: str):
        """Request to add a bot."""
        if ctx.author.id in self.protected_users:
            for user_id in self.protected_users:
                user = ctx.guild.get_member(user_id)
                if user:
                    try:
                        msg = await user.send(
                            f"⚠️ Request to add bot: {bot_id}\nReason: {reason}\n"
                            f"React ✅ to approve or ❌ to deny."
                        )
                        await msg.add_reaction("✅")
                        await msg.add_reaction("❌")
                    except discord.Forbidden:
                        print(f"❌ Could not DM user {user_id}")

            self.pending_bot_additions[bot_id] = (ctx.author.id, datetime.utcnow() + timedelta(minutes=15))
            await ctx.send(f"✅ Bot addition request for bot ID {bot_id} sent for approval.")
        else:
            await ctx.send("❌ You do not have permission to request bot additions.")

async def setup(bot):
    await bot.add_cog(AntiNuke(bot))