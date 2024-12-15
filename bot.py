import discord
from discord.ext.commands import Bot
from discord.ext import commands, tasks
from discord import app_commands
import os
import re
import json
import asyncio
from datetime import datetime as dt
from datetime import timezone
import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from discord_message_extractor import extract_past_month_messages
from summarization import get_messages, summarize_messages

intents = discord.Intents.default()
intents.members = True
intents.reactions = True
intents.message_content = True
intents.messages = True
bot = commands.Bot(command_prefix= '$', intents = intents)

CONFIG_FILE = 'config.json'
DEBUG_MODE = False
COLLECTION_FLAG = False
POST_FLAG = False
TODAY = dt.now(timezone.utc)
PAST_MONTH = TODAY.replace(month=TODAY.month-1) if TODAY.month > 1 else TODAY.replace(year=TODAY.year-1, month=12)

# Message collection will happen on the penultimate day of the month, update the flag accordingly
if TODAY.month == 2 and TODAY.day == 27:
    COLLECTION_FLAG = True
# 30th day of the month for months with 31 days
elif TODAY.day == 29 and TODAY.month in [4, 6, 9, 11]:
    COLLECTION_FLAG = True
elif TODAY.day == 30 and TODAY.month in [1, 3, 5, 7, 8, 10, 12]:
    COLLECTION_FLAG = True
else:
    COLLECTION_FLAG = False

# POST_FLAG updated on the first day of the month
if TODAY.day == 1:
    POST_FLAG = True

def load_config():
    """  Load configuration from JSON file """
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Config file not found.")
        return {}

def save_config(config):
    """Saves the configuration to the JSON file."""
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

async def replace_emojis(text):
    """Replaces Discord custom emojis with their names in a string."""
    return re.sub(r"<:(\w+):\d+>", r"\1", text)

async def check_summary_role(guild, role_name = "Monthly Bot Summary", role_color = discord.Color(0x00ff00)):
    """Check if role related to monthly summaries exists on the server."""
    role = discord.utils.get(guild.roles, name=role_name)
    if role is None:
        role = await guild.create_role(name=role_name, color=role_color)
    return role

@bot.event
async def on_ready():
    global cfg 
    cfg = load_config()
    for config in cfg:
        guild_id, _, announcement_channel_id, emoji, role_name, _ = config
        announcement_channel = bot.get_channel(announcement_channel_id)
        if announcement_channel:
            try:
                messages = await announcement_channel.history(limit=None).flatten()
                if messages:
                    announcement_message = messages[0]
                    role = discord.utils.get(bot.get_guild(guild_id).roles, name=role_name)
                    if role:
                        bot.loop.create_task(monitor_reactions(bot, guild_id, announcement_channel.id, announcement_message.id, emoji, role.id))
            except discord.Forbidden:
                print(f"Missing permissions to access the message or manage roles in {announcement_channel.name}.")
    print(f'{bot.user} has connected to Discord!')
    print(f'Bot has access to {len(bot.guilds)} guilds')

async def generate_summaries(overwrite=False):
    """ Function that generates summaries for each guild """
    mode = 'w' if overwrite else 'a'
    for guild in bot.guilds:
        # Get role name from config
        role_name = cfg[str(guild.id)]['role_name']
        messages = get_messages(guild.id)
        summary = summarize_messages(guild.id, messages, role_name)
        try:
            os.chdir(f'summarizations')
        except FileNotFoundError:
            os.mkdir(f'summarizations')
            os.chdir(f'summarizations')
        with open(f'{guild.id}_{PAST_MONTH.year}_{PAST_MONTH.month}.txt', mode, encoding='utf-8') as f:
            f.write(summary)

@tasks.loop(time = datetime.time(hour=0, minute=0, second=0)) # Run the task at midnight UTC
async def monthly_message_extraction(overwrite= False):
    mode = 'w' if overwrite else 'a'
    now = dt.now(datetime.timezone.utc)
    if not DEBUG_MODE and not COLLECTION_FLAG:
        return
    for guild in bot.guilds:
        try:
            os.chdir(f'message_logs/{guild.id}_message_logs')
        except FileNotFoundError:
            os.mkdir(f'message_logs/{guild.id}_message_logs')
            os.chdir(f'message_logs/{guild.id}_message_logs')
        for channel in guild.text_channels:
            if channel.name == 'bot-testing':
                continue
            try:
                messages = await extract_past_month_messages(guild, channel, now)
                print(f"Extracted {len(messages)} messages from {channel.name} in {guild.name}")
                if messages:
                    with open(f'{channel.id}_{now.year}_{now.month}.txt', mode, encoding='utf-8') as f:
                        for message in messages:
                            #message = await parse_messages(message)
                            content = await replace_emojis(message.clean_content)
                            f.write(f"{message.author.name}: {content}\n")
            except discord.errors.Forbidden:
                print(f"Bot does not have permission to read messages in {channel.name} in {guild.name}")
            except Exception as e:
                print(f"An error occurred while processing {channel.name} in {guild.name}: {e}")
    # Generate summaries for each guild
    await generate_summaries(overwrite)

@tasks.loop(time = datetime.time(hour=0, minute=0, second=0)) # Run the task at midnight UTC
async def post_summary():
    """ Post the summary to the specified channel """
    now = dt.now(datetime.timezone.utc)
    if not DEBUG_MODE and not POST_FLAG:
        return
    for guild in bot.guilds:
        guild_id = guild.id
        fn = f'summarizations/{guild_id}_{PAST_MONTH.year}_{PAST_MONTH.month}.txt'
        role_name = cfg[str(guild_id)]['role_name']
        channel_name = cfg[str(guild_id)]['channel_to_post_summary']
        channel = discord.utils.get(guild.text_channels, name=channel_name)
        if channel is None:
            raise Exception(f"Channel {channel_name} not found.")
        role = discord.utils.get(guild.roles, name=role_name)
        if role is None:
            raise Exception(f"Role {role_name} not found.")
        with open(fn, 'r', encoding='utf-8') as f:
            summary = f.read()
        # Post summary to channel
        await channel.send(f"{role.mention} {summary}")

@monthly_message_extraction.before_loop
async def before():
    await bot.wait_until_ready()

async def setup_hook():
    scheduler = AsyncIOScheduler()
    monthly_message_extraction.start()
    scheduler.start()

bot.setup_hook = setup_hook

@bot.command()
async def setup_role_post(ctx, channel_to_post_to = 'monthly-summaries', announcement_channel_name = 'announcements', emoji = '\ud83d\uddd3\ufe0f', role_name = "Monthly Bot Summary", role_color = discord.Color(0x00ff00)):
    """ Setup role for monthly summary posts """
    
    guild = ctx.guild

    # Create role if it doesn't exist
    role = await check_summary_role(guild, role_name, role_color)
    await ctx.send(f"Role {role.name} created successfully.")

    # Create channel to post summary
    if str(channel_to_post_to) not in [channel.name for channel in guild.text_channels]:
        await guild.create_text_channel(str(channel_to_post_to))
        await ctx.send(f"Channel {channel_to_post_to} created successfully.")
    else:
        await ctx.send(f"Channel {channel_to_post_to} already exists.")

    # Create announcement post
    if str(announcement_channel_name) not in [channel.name for channel in guild.text_channels]:
        await guild.create_text_channel(str(announcement_channel_name))
        await ctx.send(f"Channel {announcement_channel_name} created successfully.")
    try:
        await ctx.send(f"Attempting to post announcement in {announcement_channel_name}")
        announcement_message = await announcement_channel_name.send(f"React with {emoji} to get the {role.mention} role!")
        await announcement_message.add_reaction(emoji)
        bot.loop.create_task(monitor_reactions(bot, guild.id, announcement_channel_name.id, announcement_message.id, emoji, role.id))
        
    except discord.Forbidden:
        await ctx.send("Bot does not have permission to add roles.")
    except Exception as e:
        print(f"An error occurred while adding role: {e}")

async def monitor_reactions(bot, guild_id, channel_id, message_id, emoji, role_id):
    """Monitors reactions on a message and assigns a role. Uses IDs."""
    guild = bot.get_guild(guild_id)
    if not guild:
        print(f"Guild with ID {guild_id} not found, stopping monitoring.")
        return

    channel = guild.get_channel(channel_id)
    if not channel:
        print(f"Channel with ID {channel_id} not found in {guild.name}, stopping monitoring.")
        return

    role = guild.get_role(role_id)
    if not role:
        print(f"Role with ID {role_id} not found in {guild.name}, stopping monitoring.")
        return

    try:
        while True:
            try:
                message = await channel.fetch_message(message_id)
                reaction = discord.utils.get(message.reactions, emoji=emoji)

                if reaction:
                    users = await reaction.users().flatten()
                    for user in users:
                        if user != bot.user and role not in user.roles:
                            await user.add_roles(role)
                            print(f"Assigned {role.name} to {user.name}")
                await asyncio.sleep(60)
            except discord.NotFound:
                print("Message deleted, stopping reaction monitoring.")
                break
            except discord.Forbidden:
                print("Missing permissions to access the message or manage roles, stopping monitoring.")
                break
            except Exception as e:
                print(f"An error occurred during reaction monitoring: {e}")
                break
    except Exception as e:
        print(f"An error occurred while setting up the monitor: {e}")

async def post_summary(channel, summary, role_name):
    """ Post the summary to the specified channel """
    role = discord.utils.get(channel.guild.roles, name=role_name)
    if role is None:
        await channel.send("Role not found.")
        return
    await channel.send(f"{role.mention} {summary}")


@bot.command()
@commands.has_permissions(administrator=True) # For admins only
async def setup(ctx, channel_to_post_summary: discord.TextChannel, announcement_channel: discord.TextChannel, emoji_to_react_to: str, role_name: str = "Monthly Bot Summary", role_color: str = '0x00ff00'):
    """ Setup the bot """
    guild = ctx.guild

    color = discord.Colour.from_str(role_color)
    if color is None:
        await ctx.send("Invalid color code.")

    role = await check_summary_role(guild, role_name, color)
    if role is None:
        await ctx.send("Could not create or find the specified role. Please try again.")
        return  
    await setup_role_post(ctx, channel_to_post_summary, announcement_channel, emoji_to_react_to, role_name, role_color)
    # Save config for this guild
    cfg[str(guild.id)] = {
        'channel_to_post_summary': channel_to_post_summary.id,
        'announcement_channel': announcement_channel.id,
        'emoji_to_react_to': emoji_to_react_to,
        'role_name': role_name,
        'role_color': role_color
    }
    save_config(cfg)
    await ctx.send("Setup complete.")


@bot.command()
@commands.is_owner()
async def extract(ctx):
    """ Manually run message extraction """
    global DEBUG_MODE
    DEBUG_MODE = True
    try:
        await ctx.send("Manually running message extraction")
    except Exception as e:
        print(f"An error occurred while running message extraction: {e}")
    await monthly_message_extraction(overwrite=True)
    print("Message extraction complete.")
    await ctx.send("Message extraction complete.")

@bot.command()
@commands.is_owner()
async def summarize(ctx, role_name = "Monthly Bot Summary"):
    """ Summarize messages from the past month """
    guild_id = ctx.guild.id
    messages = get_messages(guild_id)
    role = await check_summary_role(ctx.guild, role_name)
    async with ctx.typing():
        summary = summarize_messages(guild_id, messages, role)
        await ctx.send(summary)


@bot.command()
@commands.is_owner()
async def post(ctx, channel_name, role_name= "Monthly Bot Summary"):
    """ Post the summary to the specified channel """
    now = dt.now(datetime.timezone.utc)
    guild = ctx.guild
    global DEBUG_MODE
    DEBUG_MODE = True
    channel = discord.utils.get(guild.text_channels, name=channel_name)
    role = discord.utils.get(guild.roles, name=role_name)
    if channel is None:
        await ctx.send("Channel not found.")
        return
    if role is None:
        await ctx.send("Role not found. Creating role with default settings, please edit it later with the setup command.")
        role = await check_summary_role(guild)
    async with channel.typing():
        fn = f'summarizations/{guild.id}_{now.year}_{now.month}.txt'
        with open(fn, 'r', encoding='utf-8') as f:
            summary = f.read()
        print(len(f"{role.mention} {summary}"))
        await channel.send(f"{role.mention} {summary}")

bot.run(os.getenv('DISCORD_TOKEN'))