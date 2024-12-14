import discord
from discord.ext.commands import Bot
from discord.ext import commands
from discord import app_commands
import os
from discord_message_extractor import extract_past_month_messages
from datetime import datetime as dt
import datetime

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.messages = True
bot = commands.Bot(intents = intents)

POST_FLAG = False
TODAY = dt.today(datetime.timezone.utc)
PAST_MONTH = TODAY.replace(month=TODAY.month-1) if TODAY.month > 1 else TODAY.replace(year=TODAY.year-1, month=12)


# Check if today is the first of the month. If so, turn on the flag.
if TODAY.day == 1:
    POST_FLAG = True

# Example usage with error handling
@bot.command()
async def get_past_month_chats(ctx, channel_name: str):
    try:
        channel = discord.utils.get(ctx.guild.text_channels, name=channel_name)
        if not channel:
            raise ValueError(f"Channel '{channel_name}' not found.")
        messages = await extract_past_month_messages(ctx.guild, channel)
    # Process or store the extracted messages (messages list)
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

bot.run(os.getenv('DISCORD_TOKEN'))