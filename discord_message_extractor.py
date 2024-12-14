import discord
import datetime
from datetime import datetime as dt

async def extract_past_month_messages(guild, channel):
    """
    Extracts messages from a specific channel for the entire past month.

    Args:
        guild: The guild object representing the Discord server.
        channel: The text channel object where you want to extract messages.
    """
    now = dt.now(datetime.timezone.utc)
    past_month = now - datetime.timedelta(days=now.day - 1)
    all_messages = []
    async for message in channel.history(limit=None, after=past_month):
        # Check if message is within the desired month
        if message.created_at.month == now.month and message.created_at.year == now.year:
            all_messages.append(message)
        else:
        # Exit loop as soon as messages go beyond the month
            break
    return all_messages

