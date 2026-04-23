from interactions import slash_command, slash_option, SlashContext, Embed, OptionType

from bot_instance import staff_role_check
from utils import colors
from utils.server_utils import is_server_online, send_server_command


@slash_command(name="unregister", description="Unregister a player from nLogin")
@slash_option(
    name="username",
    description="The Minecraft username to unregister",
    required=True,
    opt_type=OptionType.STRING
)
@staff_role_check(exclude=["Owner", "Co-Owner", "Management","Administrator"], exclude_acts_as_include=True)
async def handle_unregister_command(ctx: SlashContext, username: str):
    await ctx.defer()
    
    if not await is_server_online():
        embed = Embed(
            title="Server Offline",
            description="The server is currently offline. Please try again later.",
            color=colors.DiscordColors.RED
        )
        await ctx.send(embeds=embed)
        return
    
    success = await send_server_command(f"nlogin unregister {username}")
    
    if success:
        embed = Embed(
            title="Player Unregistered",
            description=f"**{username}** has been unregistered from nLogin.",
            color=colors.DiscordColors.GREEN
        )
    else:
        embed = Embed(
            title="Command Failed",
            description="Failed to send the unregister command. Please try again.",
            color=colors.DiscordColors.RED
        )
    
    await ctx.send(embeds=embed)
