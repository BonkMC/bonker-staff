from interactions import slash_command, slash_option, OptionType, SlashContext, Embed
from utils import colors
from bot_instance import staff_role_check  # Import role_check from bot_instance

@slash_command(name="dm", description="Send a direct message as the bot.")
@slash_option(
    name="user",
    description="Who do you want to send the message to?",
    required=True,
    opt_type=OptionType.USER
)
@slash_option(
    name="message",
    description="What message would you like to send?",
    required=True,
    opt_type=OptionType.STRING
)
@staff_role_check(exclude=["Owner", "Co-Owner", "Management", "Developer"], exclude_acts_as_include=True)
async def handle_dm_command(ctx: SlashContext, user, message: str):
    user = ctx.guild.get_member(user)
    embed = Embed(description=message, color=colors.DiscordColors.BLUE)
    await user.send(embeds=embed)
    await ctx.send(f"DM sent to {user.display_name}!\n\nMessage contents: {message}", ephemeral=True)
