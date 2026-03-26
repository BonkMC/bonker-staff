from interactions import slash_command, slash_option, OptionType, SlashContext, Embed, SlashCommandChoice
from utils import colors
from pydactyl import PterodactylClient
from bot_instance import staff_role_check,AppConfig_obj  # Import role_check from bot_instance

key = AppConfig_obj.get_bonk_panel_api_key()
api = PterodactylClient('https://panel.bonkmc.org', key)

@slash_command(
    name="execute",
    description="Execute a command in the console"
)
@slash_option(
    name="command",
    description="The command you would like to execute",
    required=True,
    opt_type=OptionType.STRING
)
@staff_role_check(exclude=["Manager", "Admin", "Owner", "Developer"], exclude_acts_as_include=True)
async def handle_execute_command(ctx: SlashContext, command):
    srv_id = "0"
    try:
        api.client.servers.send_console_command(srv_id, command)
        await ctx.send(
            embeds=Embed(
                title="Command Executed",
                description=f"The command `{command}` has been executed in console.",
                color=colors.DiscordColors.GREEN
            )
        )
    except:
        await ctx.send(
            embeds=Embed(
                title="Command Failed",
                description=f"The command `{command}` failed to execute in console.",
                color=colors.DiscordColors.RED
            )
        )

