from interactions import slash_command, SlashContext, Embed, OptionType, slash_option
import asyncio
from datetime import datetime, timedelta

from bot_instance import bot
from utils import colors
from utils.constants import (
    CODE_RED_CHANNEL_ID, 
    CODE_RED_ALLOWED_ROLES, 
    CODE_RED_PING_ROLES,
    HIGHER_UPS_ROLE_ID,
    DEVELOPER_ROLE_ID
)

code_red_cooldowns = {}

def code_red_role_check():
    async def predicate(ctx: SlashContext):
        user_roles = [int(role.id) for role in ctx.author.roles]
        return any(role_id in user_roles for role_id in CODE_RED_ALLOWED_ROLES)
    return predicate


@slash_command(name="code-red", description="Issue a code red alert for critical issues")
@slash_option(
    name="ongoing_issue",
    description="Describe the critical issue that requires immediate attention",
    required=True,
    opt_type=OptionType.STRING
)
async def handle_code_red_command(ctx: SlashContext, ongoing_issue: str):
    current_time = datetime.now()
    user_id = ctx.author.id
    
    if user_id in code_red_cooldowns:
        last_used = code_red_cooldowns[user_id]
        cooldown_end = last_used + timedelta(hours=12)
        
        if current_time < cooldown_end:
            time_left = cooldown_end - current_time
            hours_left = int(time_left.total_seconds() // 3600)
            minutes_left = int((time_left.total_seconds() % 3600) // 60)
            
            cooldown_embed = Embed(
                title="⏰ Code Red Cooldown",
                description=f"You must wait {hours_left}h {minutes_left}m before using this command again.",
                color=colors.DiscordColors.YELLOW
            )
            await ctx.send(embeds=cooldown_embed, ephemeral=True)
            return
    
    if not await code_red_role_check()(ctx):
        error_embed = Embed(
            title="❌ Access Denied",
            description="You don't have permission to use this command.",
            color=colors.DiscordColors.RED
        )
        await ctx.send(embeds=error_embed, ephemeral=True)
        return

    code_red_embed = Embed(
        title="🚨 CODE RED ALERT 🚨",
        description=f"**Issued by:** {ctx.author.mention}\n**Issue:** {ongoing_issue}",
        color=colors.DiscordColors.DARK_RED
    )
    
    code_red_embed.add_field(
        name="💬 Discussion",
        value="Please use the thread below for staff discussion and updates",
        inline=False
    )
    
    code_red_embed.set_footer(text="Code Red Alert System", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
    
    code_red_channel = bot.get_channel(CODE_RED_CHANNEL_ID)
    if not code_red_channel:
        error_embed = Embed(
            title="❌ Error",
            description="Code red channel not found. Please check bot permissions.",
            color=colors.DiscordColors.RED
        )
        await ctx.send(embeds=error_embed, ephemeral=True)
        return
    
    role_mentions = f"<@&{HIGHER_UPS_ROLE_ID}> <@&{DEVELOPER_ROLE_ID}>"
    
    alert_message = await code_red_channel.send(
        content=role_mentions,
        embeds=code_red_embed
    )
    
    thread = await alert_message.create_thread(
        name=f"Code Red Discussion - {ctx.author.display_name}",
        auto_archive_duration=1440
    )
    
    thread_embed = Embed(
        title="💬 Staff Discussion Thread",
        description="This thread is for discussing the code red alert and coordinating response efforts.",
        color=colors.DiscordColors.BLUE
    )
    await thread.send(embeds=thread_embed)
    
    await dm_role_members(ctx, CODE_RED_PING_ROLES, ctx.author, ongoing_issue)
    
    code_red_cooldowns[user_id] = current_time
    
    confirmation_embed = Embed(
        title="✅ Code Red Alert Sent",
        description=f"Your code red alert has been sent to <#{CODE_RED_CHANNEL_ID}> and relevant staff have been notified.",
        color=colors.DiscordColors.GREEN
    )
    confirmation_embed.add_field(
        name="Thread Created",
        value=f"[Join Discussion](https://discord.com/channels/{ctx.guild.id}/{thread.id})",
        inline=False
    )
    
    await ctx.send(embeds=confirmation_embed, ephemeral=True)


async def dm_role_members(ctx: SlashContext, role_ids: list[int], issuer, issue_description: str):
    dm_embed = Embed(
        title="🚨 Code Red Alert Notification",
        description=f"**{issuer.display_name}** has issued a code red alert.",
        color=colors.DiscordColors.DARK_RED
    )
    dm_embed.add_field(name="Issue Description", value=issue_description, inline=False)
    dm_embed.add_field(name="Channel", value=f"<#{CODE_RED_CHANNEL_ID}>", inline=True)
    dm_embed.set_footer(text="Please check the code red channel for more details and discussion.")

    guild = ctx.guild
    if not guild:
        print("No guild on ctx")
        return

    members_to_dm = set()

    fetched = []
    try:
        fetched = [m async for m in guild.fetch_members(limit=None)]
        print(f"Fetched {len(fetched)} guild members")
    except Exception as e:
        print(f"fetch_members not available / failed: {e}")

    if fetched:
        for member in fetched:
            if getattr(member.user, "bot", False):
                continue
            member_roles = {int(r.id) for r in member.roles}
            if any(rid in member_roles for rid in role_ids):
                members_to_dm.add(member)
    else:
        print("Falling back to role.members (cache-dependent)")
        for role_id in role_ids:
            role = guild.get_role(role_id)
            if not role:
                print(f"Role not found in cache: {role_id}")
                continue
            for member in getattr(role, "members", []):
                if getattr(member.user, "bot", False):
                    continue
                members_to_dm.add(member)

    print(f"Total members to DM (including issuer): {len(members_to_dm)}")

    print(f"Total members to DM (final): {len(members_to_dm)}")

    if members_to_dm:
        dm_tasks = [send_dm_safely(m, dm_embed) for m in members_to_dm]
        results = await asyncio.gather(*dm_tasks, return_exceptions=True)
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"DM task {i} failed: {result}")
    else:
        print("No DM tasks to execute")


async def send_dm_safely(member, embed):
    try:
        await member.send(embeds=embed)
    except Exception as e:
        print(f"Failed to DM {member.display_name}: {e}")
        pass
