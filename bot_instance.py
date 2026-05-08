from utils import config
from interactions import Client, check, SlashContext, Embed, Intents, listen
from interactions.api.events import CommandError, Startup
from interactions.client.errors import CommandCheckFailure
import asyncio
import json
import traceback
from dotenv import load_dotenv

load_dotenv()

AppConfig_obj = config.AppConfig(use_updated_system=True)
token = AppConfig_obj.get_bot_key()

bot = Client(
    token=token,
    sync_interactions=True,
    intents=Intents.DEFAULT | Intents.GUILD_MEMBERS,
    fetch_members=True,
)


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
    if isinstance(event.error, CommandCheckFailure):
        return

    error_msg = "".join(traceback.format_exception(type(event.error), event.error, event.error.__traceback__))
    if len(error_msg) > 4000:
        error_msg = error_msg[:4000] + "..."
    embed = Embed(
        title="Error",
        description=f"```\n{error_msg}\n```",
        color=0xFF0000
    )
    try:
        await event.ctx.send(embed=embed, ephemeral=True)
    except Exception:
        pass


def _is_known_reaction_cache_bug(context: dict) -> bool:
    exc = context.get("exception")
    if not isinstance(exc, (TypeError, AttributeError)):
        return False

    fut = context.get("future")
    coro_qualname = ""
    get_coro = getattr(fut, "get_coro", None)
    if get_coro is not None:
        try:
            coro = get_coro()
            coro_qualname = getattr(coro, "__qualname__", "") or ""
        except Exception:
            coro_qualname = ""

    return any(
        marker in coro_qualname
        for marker in ("ReactionEvents", "_handle_message_reaction_change", "_on_raw_message_reaction")
    )


@listen(Startup)
async def _install_loop_exception_handler():
    loop = asyncio.get_running_loop()
    previous_handler = loop.get_exception_handler()

    def handler(loop, context):
        if _is_known_reaction_cache_bug(context):
            return
        if previous_handler is not None:
            previous_handler(loop, context)
        else:
            loop.default_exception_handler(context)

    loop.set_exception_handler(handler)
