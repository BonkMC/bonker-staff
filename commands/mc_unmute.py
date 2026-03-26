from interactions import slash_command, slash_option, SlashContext, Embed, OptionType

from bot_instance import staff_role_check
from utils import colors
from utils.server_utils import is_server_online, send_command_with_response


@slash_command(name="mc-unmute", description="Unmute a player on the server")
@slash_option(
    name="username",
    description="The Minecraft username to unmute",
    required=True,
    opt_type=OptionType.STRING
)
@staff_role_check(exclude=["Owner", "Co-Owner", "Management", "Administrator", "Senior Moderator"], exclude_acts_as_include=True)
async def handle_mc_unmute_command(ctx: SlashContext, username: str):
    await ctx.defer()
    
    if not await is_server_online():
        embed = Embed(
            title="Server Offline",
            description="The server is currently offline. Please try again later.",
            color=colors.DiscordColors.RED
        )
        await ctx.send(embeds=embed)
        return
    
    lines = await send_command_with_response(f"unmute {username}", timeout=3.0)
    
    not_muted = any("Target is not muted" in line for line in lines)
    
    if not_muted:
        embed = Embed(
            title="Player Not Muted",
            description=f"**{username}** is not currently muted.",
            color=colors.DiscordColors.YELLOW
        )
    else:
        embed = Embed(
            title="Player Unmuted",
            description=f"**{username}** has been unmuted.",
            color=colors.DiscordColors.GREEN
        )
    
    await ctx.send(embeds=embed)
