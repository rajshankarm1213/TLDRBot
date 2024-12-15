import os
import google.generativeai as genai
from datetime import datetime as dt
import discord

def get_messages(guild_id):
    """
    Get all messages from a specific guild.

    Args:
        guild_id: The unique identifier for the guild.

    Returns:
        A list of all messages from the guild.
    """
    messages = []
    try:
        for file in os.listdir(f'message_logs/{guild_id}_message_logs'):
            with open(f'message_logs/{guild_id}_message_logs/{file}', 'r', encoding='utf-8') as f:
                messages.extend(f.readlines())
    except Exception as e:
        print(f"An error occurred while reading messages from {guild_id}: {e}")
        print(os.getcwd())
    return messages



def summarize_messages(guild_id, messages, role):
    """
        Summarizes the messages from a guild using the Hugging Face pipeline.

        Args:
            guild_id: The unique identifier for the guild.
            messages: A list of messages from a guild.
        
        Returns:
            A summary of the messages.
    """
    genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"""
    <s>[INST] I have a long string of Discord chat logs from an entire month. I need a summary of all the events that occured as if a blog writer is writing about a group of people as a narrator.

    Instructions:
    *   Give the episode a title that reflects the main themes of the month.
    *   Present the key events, discussions, and announcements in a conversational tone as if the writer is talking to the reader.
    *   Maintain an engaging and informative tone.
    *   Focus on the most significant topics and avoid unnecessary details.
    *   Include a closing statement that summarizes the main takeaways from the month.
    *   The summary should contain 1700-1800 characters including punctuation. The character count should not exceed 1800 characters no matter what.
    *  Don't leave too much space between sentences and paragraphs. Don't use too many line breaks or too much punctuation.
    *  Try to use nicknames whenever possible to make the summary more engaging and to reduce the word count.

    Chat Logs:
    {messages}
    [/INST]
    """
    while(True):
        response = model.generate_content(prompt)
        if len(f"{role.mention} {response.text}") <= 2000:
            break
    # Export to txt file
    now = dt.now()
    with open(f'summarizations/{guild_id}_{now.year}_{now.month}.txt', 'a', encoding='utf-8') as f:
        f.write(response.text)
    return response.text 



