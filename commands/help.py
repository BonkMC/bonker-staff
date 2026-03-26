from interactions import slash_command, SlashContext, Embed
from utils import colors
from bot_instance import staff_role_check


@slash_command(name="help", description="View available staff commands")
@staff_role_check()
async def handle_help_command(ctx: SlashContext):
    embed = Embed(
        title="Staff Commands",
        description="Here are the available staff commands and their permissions.",
        color=colors.DiscordColors.BLUE
    )
    
    embed.add_field(
        name="All Staff (Trainee+)",
        value=(
            "`/checkban <username>` - Check if a player is banned\n"
            "`/help` - View this help message"
        ),
        inline=False
    )
    
    embed.add_field(
        name="Helper+",
        value="`/code-red <issue>` - Issue a code red alert",
        inline=False
    )
    
    embed.add_field(
        name="Senior Moderator+",
        value=(
            "`/mc-unban <username>` - Unban a player\n"
            "`/mc-unmute <username>` - Unmute a player"
        ),
        inline=False
    )
    
    embed.add_field(
        name="Management+",
        value=(
            "`/unregister <username>` - Unregister a player from nLogin\n"
            "`/dm <user> <message>` - Send a DM as the bot"
        ),
        inline=False
    )
    
    await ctx.send(embeds=embed, ephemeral=True)
