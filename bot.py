# -*- coding: utf-8 -*-
import discord
import random
from discord import app_commands
from discord.ext import commands
from datetime import timedelta
from datetime import datetime

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

def is_admin():
    async def predicate(interaction: discord.Interaction):
        return interaction.user.guild_permissions.moderate_members

    return app_commands.check(predicate)


async def log_action(guild: discord.Guild, message: str):
    log_channel = guild.get_channel(LOG_CHANNEL_ID)
    if log_channel:
        await log_channel.send(message)


# Automoderation
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    print(f"Skipped Automoderation in {ignored_channels}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash commands")
    except Exception as e:
        print(f"Sync error: {e}")


# Auto-detect banned words in chat
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    if message.channel.id in ignored_channels:
        return  # skip moderation in this channel

    if any(word in message.content.lower() for word in banned_words):
        try:
            await message.delete()
            await message.author.send(
                "Hey bud, mind your language!"
            )
            print(f"Direct Message sent to {message.author}")
        except discord.Forbidden:
            print(f"Could not DM {message.author}")

    await bot.process_commands(message)


# SLASH COMMANDS

# /warn (manual)
@bot.tree.command(name="warn", description="Warn a user with a DM.")
@is_admin()
@app_commands.describe(member="The user to warn", reason="Reason for the warning")
async def warn(interaction: discord.Interaction, member: discord.Member, reason: str = "Warned by Moderator"):
    try:
        await member.send(f"You have been warned for: {reason}")
        await interaction.response.send_message(f"{member.mention} has been warned.", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message(" Could not DM that user.", ephemeral=True)


# /mute
@bot.tree.command(name="mute", description="Mute (timeout) a user for a number of minutes.")
@is_admin()
@app_commands.describe(member="The user to mute", minutes="Minutes to mute")
async def mute(interaction: discord.Interaction, member: discord.Member, minutes: int = 1440):
    try:
        minutes = max(1, int(minutes))
        duration = discord.utils.utcnow() + timedelta(minutes=minutes)
        await member.timeout(duration, reason="Muted by moderator")
        await interaction.response.send_message(
            f"{member.mention} muted for {minutes} minutes.", ephemeral=True
        )
        await log_action(interaction.guild, f"{member} was muted by {interaction.user} for {minutes} minutes.")
    except Exception as e:
        await interaction.response.send_message(f"Could not mute: {e}", ephemeral=True)


# /ban
@bot.tree.command(name="ban", description="Ban a user from the server.")
@is_admin()
@app_commands.describe(member="The user to ban", reason="Reason for the ban")
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    try:
        await member.ban(reason=reason)
        await interaction.response.send_message(f"{member.mention} has been banned.", ephemeral=True)
        await log_action(interaction.guild, f"{member} was banned by {interaction.user} for: {reason}")
    except Exception as e:
        await interaction.response.send_message(f"Could not ban: {e}", ephemeral=True)


# /checkperms
@bot.tree.command(name="checkperms", description="Check your server permissions")
async def checkperms(interaction: discord.Interaction):
    perms = interaction.user.guild_permissions
    allowed = [name.replace("_", " ").title() for name, value in perms if value]  # format nicely

    # Split into multiple lines so you can read
    chunk_size = 10
    chunks = [allowed[i:i + chunk_size] for i in range(0, len(allowed), chunk_size)]
    message = "\n".join(", ".join(chunk) for chunk in chunks)

    await interaction.response.send_message(f"Your permission(s) is(are) :\n{message}", ephemeral=True)


# /help
@bot.tree.command(name="help", description="Intro on how Chiptuner command works")
async def help(interaction: discord.Interaction):
    await interaction.response.send_message(
        "/ban: Ban a member (Requires Moderater rights) \n/mute: Mute a member (Requires Moderator rights) \n/warn: "
        "Warn a member (Requires Moderator rights) \n/checkperms: Check your permissions in a server \n/tips: Recieve "
        "a random tip",
        ephemeral=True)
