import discord
from discord.ext.commands import Bot
from discord.ext import commands, tasks
from discord import app_commands
import os
import re
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



async def replace_emojis(text):
    """Replaces Discord custom emojis with their names in a string."""
    return re.sub(r"<:(\w+):\d+>", r"\1", text)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print(f'Bot has access to {len(bot.guilds)} guilds')
    print(f'{guild.name} (id: {guild.id})' for guild in bot.guilds)

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


@monthly_message_extraction.before_loop
async def before():
    await bot.wait_until_ready()

async def setup_hook():
    scheduler = AsyncIOScheduler()
    monthly_message_extraction.start()
    scheduler.start()

bot.setup_hook = setup_hook

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
async def summarize(ctx):
    """ Summarize messages from the past month """
    guild_id = ctx.guild.id
    messages = get_messages(guild_id)
    summary = summarize_messages(guild_id, messages)
    await ctx.send(summary)

bot.run(os.getenv('DISCORD_TOKEN'))