from utils import config
from interactions import Client, check, SlashContext, Embed, listen
from interactions.api.events import CommandError
import os
from dotenv import load_dotenv
import json
import traceback

load_dotenv()

AppConfig_obj = config.AppConfig(use_updated_system=True)
token = AppConfig_obj.get_bot_key()
bot = Client(token=token, sync_interactions=True)


# Role check decorator for role-specific commands
def staff_role_check(exclude: list = [], exclude_acts_as_include: bool = False):
    async def predicate(ctx: SlashContext):
        with open('data/roleslist.json') as f:
            roles_dict = json.load(f)
        check_roles = []
        for role, role_ids in roles_dict.items():
            if not exclude_acts_as_include and role in exclude:
                continue
            check_roles.extend(role_ids)
        user_roles = [int(i.id) for i in ctx.author.roles]
        has_permission = any(role_id in user_roles for role_id in check_roles)
        if not has_permission:
            embed = Embed(
                title="Permission Denied",
                description="You do not have permission to use this command.",
                color=0xFF0000
            )
            await ctx.send(embed=embed, ephemeral=True)
        return has_permission

    return check(predicate)


@listen(CommandError, disable_default_listeners=True)
async def on_command_error(event: CommandError):
    error_msg = "".join(traceback.format_exception(type(event.error), event.error, event.error.__traceback__))
    if len(error_msg) > 4000:
        error_msg = error_msg[:4000] + "..."
    embed = Embed(
        title="Error",
        description=f"```\n{error_msg}\n```",
        color=0xFF0000
    )
    await event.ctx.send(embed=embed, ephemeral=True)
