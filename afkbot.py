import discord
from discord.ext import commands, tasks
import asyncio
import logging

# set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

idVoiceChannel = XXXXXX  # afk voice channel ID
idChannel = XXXXX  # text channel ID
idRole = XXXXXX  # AFK role ID

usersAFK = {}  # stores user id and reason
originalVC = {}  # stores user's original voice channel before AFK
inactiveUser = {}  # tracks inactivity
trackedUser = None  # tracks a specific user


@bot.event
async def on_ready():
    logging.info(f"logged in as {bot.user}")
    check_inactive_user.start()


@bot.event
async def on_voice_state_update(member, before, after):
    global trackedUser
    logging.info(f"voice update detected for {member.name}.")
    if trackedUser and member.id == trackedUser:
        if after.channel and after.channel.id != idVoiceChannel and after.self_mute:
            inactiveUser[member.id] = asyncio.get_event_loop().time()
            logging.info(
                f"{member.name} timestamp updated for inactivity tracking.")
        elif after.channel is None or not after.self_mute:
            inactiveUser.pop(member.id, None)


@tasks.loop(minutes=3)
async def check_inactive_user():
    global trackedUser
    if not trackedUser:
        return

    current_time = asyncio.get_event_loop().time()
    if trackedUser in inactiveUser and current_time - inactiveUser[trackedUser] > 180:
        guild = bot.guilds[0]
        member = guild.get_member(trackedUser)
        if member and member.voice and member.voice.channel:
            afk_role = discord.utils.get(guild.roles, id=idRole)
            afk_voice_channel = discord.utils.get(
                guild.voice_channels, id=idVoiceChannel
            )
            if afk_role and afk_voice_channel:
                originalVC[member.id] = member.voice.channel.id
                await member.add_roles(afk_role)
                logging.info(f"Moving {member.name} to afk channel.")
                try:
                    await member.move_to(afk_voice_channel)
                    inactiveUser.pop(member.id, None)
                    logging.info(f"{member.name} moved to afk channel.")
                except discord.Forbidden:
                    logging.error(
                        f"cannot move {member.name}, missing permissions.")
                usersAFK[member.id] = "automatic afk"
                await bot.get_channel(idChannel).send(
                    f"{member.mention} was moved to the afk voice chat."
                )


@bot.command()
async def autoafk(ctx, member: discord.Member = None):
    """set or remove the only user being tracked for automatic AFK"""
    global trackedUser
    if trackedUser == member.id:
        trackedUser = None
        await ctx.send(f"{member.mention} is not being tracked anymore.")
    else:
        trackedUser = member.id
        await ctx.send(f"{member.mention} is being tracked.")
    logging.info(f"tracking status changed for {member.name}.")


@bot.command()
async def afk(ctx, member: discord.Member = None, *, reason="no reason."):
    """afk role to a user with a custom message"""
    if member is None:
        member = ctx.author

    afk_role = discord.utils.get(ctx.guild.roles, id=idRole)

    if member != ctx.author and not ctx.author.guild_permissions.manage_messages:
        await ctx.send("you don't have permission for this.")
        return

    if afk_role in member.roles:
        await ctx.send(f"{member.mention} already afk.")
        return

    try:
        await member.add_roles(afk_role)
        usersAFK[member.id] = reason
        await ctx.send(f"{member.mention} is afk, reason: {reason}")

        if (
            member.voice
            and member.voice.channel
            and member.voice.channel.id != idVoiceChannel
        ):
            afk_voice_channel = discord.utils.get(
                ctx.guild.voice_channels, id=idVoiceChannel
            )
            if afk_voice_channel:
                originalVC[member.id] = member.voice.channel.id
                logging.info(f"moving {member.name} to afk channel.")
                try:
                    await member.move_to(afk_voice_channel)
                    logging.info(f"{member.name} moved to afk channel.")
                except discord.Forbidden:
                    logging.error(
                        f"cannot move {member.name}, missing permissions.")
                await ctx.send(f"{member.mention} was moved to the afk voice chat.")
    except discord.Forbidden:
        await ctx.send("i don't have permission for this.")


@bot.command()
async def back(ctx, member: discord.Member = None):
    """removes afk role from a user (or yourself)"""
    if member is None:
        member = ctx.author

    afk_role = discord.utils.get(ctx.guild.roles, id=idRole)

    if member != ctx.author and not ctx.author.guild_permissions.manage_messages:
        await ctx.send("you don't have permission to this.")
        return

    if member.id in usersAFK:
        reason = usersAFK.pop(member.id)
        await member.remove_roles(afk_role)
        await ctx.send(f"{member.mention} is back (was afk because: {reason})")
        logging.info(f"{member.name} returned from AFK: {reason}")

        if member.id in originalVC:
            original_channel = bot.get_channel(originalVC.pop(member.id))
            if original_channel:
                await member.move_to(original_channel)
                await member.edit(mute=False)


@bot.event
async def on_message(message):
    """automatically removes afk role when a user sends a message"""
    if message.author.bot:
        return

    member = message.author
    afk_role = discord.utils.get(message.guild.roles, id=idRole)

    if member.id in usersAFK:
        try:
            reason = usersAFK.pop(member.id)
            await member.remove_roles(afk_role)
            await message.channel.send(
                f"{member.mention} is back (was afk because: {reason})"
            )
            logging.info(
                f"{member.name} returned from afk by sending a message.")

            if member.id in originalVC:
                original_channel = bot.get_channel(originalVC.pop(member.id))
                if original_channel:
                    await member.move_to(original_channel)
                    await member.edit(mute=False)
        except discord.Forbidden:
            await message.channel.send(f"i can't remove the role of {member.mention}.")

    await bot.process_commands(message)


# run
bot.run("BOT_TOKEN")
