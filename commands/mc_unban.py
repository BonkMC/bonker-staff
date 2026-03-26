from interactions import slash_command, slash_option, SlashContext, Embed, OptionType

from bot_instance import staff_role_check
from utils import colors
from utils.server_utils import is_server_online, send_command_with_response


@slash_command(name="mc-unban", description="Unban a player from the server")
@slash_option(
    name="username",
    description="The Minecraft username to unban",
    required=True,
    opt_type=OptionType.STRING
)
@staff_role_check(exclude=["Owner", "Co-Owner", "Management", "Administrator", "Senior Moderator"], exclude_acts_as_include=True)
async def handle_mc_unban_command(ctx: SlashContext, username: str):
    await ctx.defer()
    
    if not await is_server_online():
        embed = Embed(
            title="Server Offline",
            description="The server is currently offline. Please try again later.",
            color=colors.DiscordColors.RED
        )
        await ctx.send(embeds=embed)
        return
    
    lines = await send_command_with_response(f"unban {username}", timeout=3.0)
    
    not_banned = any("Target is not banned" in line for line in lines)
    ban_revoked = any("Ban has been Revoked" in line for line in lines)
    
    if not_banned:
        embed = Embed(
            title="Player Not Banned",
            description=f"**{username}** is not currently banned.\nIf they try to reconnect, they will be unbanned.",
            color=colors.DiscordColors.YELLOW
        )
    elif ban_revoked:
        embed = Embed(
            title="Player Unbanned",
            description=f"**{username}**'s ban has been revoked.",
            color=colors.DiscordColors.GREEN
        )
    else:
        embed = Embed(
            title="Unban Sent",
            description=f"Unban command sent for **{username}**.",
            color=colors.DiscordColors.GREEN
        )
    
    await ctx.send(embeds=embed)
