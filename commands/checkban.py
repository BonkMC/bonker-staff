from interactions import slash_command, slash_option, SlashContext, Embed, OptionType

from bot_instance import staff_role_check
from utils import colors
from utils.ban_utils import check_player_ban
from utils.server_utils import is_server_online


@slash_command(name="checkban", description="Check if a player is banned")
@slash_option(
    name="username",
    description="The Minecraft username to check",
    required=True,
    opt_type=OptionType.STRING
)
@staff_role_check()
async def handle_checkban_command(ctx: SlashContext, username: str):
    await ctx.defer()
    
    if not await is_server_online():
        embed = Embed(
            title="Server Offline",
            description="The server is currently offline. Please try again later.",
            color=colors.DiscordColors.RED
        )
        await ctx.send(embeds=embed)
        return
    
    result = await check_player_ban(username)
    
    if not result.is_banned:
        embed = Embed(
            title="Player Not Banned",
            description=f"**{username}** is not currently banned.",
            color=colors.DiscordColors.GREEN
        )
        await ctx.send(embeds=embed)
        return
    
    embed = Embed(
        title="Player Banned",
        description=f"**{result.username}** is currently banned.",
        color=colors.DiscordColors.RED
    )
    embed.add_field(name="Banned By", value=result.banned_by or "Unknown", inline=True)
    embed.add_field(name="Reason", value=result.reason or "No reason provided", inline=True)
    embed.add_field(name="Banned On", value=result.banned_on or "Unknown", inline=True)
    
    if result.permanent:
        embed.add_field(name="Duration", value="Permanent", inline=True)
    else:
        until_str = result.banned_until or "Unknown"
        if result.duration_remaining:
            until_str += f"\n({result.duration_remaining} remaining)"
        embed.add_field(name="Banned Until", value=until_str, inline=True)
    
    embed.add_field(name="Server", value=result.server or "Unknown", inline=True)
    embed.add_field(name="Scope", value=result.scope or "Unknown", inline=True)
    
    flags = []
    if result.ip_ban:
        flags.append("IP Ban")
    if result.silent:
        flags.append("Silent")
    if flags:
        embed.add_field(name="Flags", value=", ".join(flags), inline=True)
    
    await ctx.send(embeds=embed)
