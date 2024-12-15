[![Ko-fi](https://img.shields.io/badge/Ko--fi-Support%20Me-red?style=flat-square&logo=ko-fi)](https://ko-fi.com/rajshankar#) [![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-blue?style=flat-square&logo=linkedin)](https://www.linkedin.com/in/rajshankarm) [![License](https://img.shields.io/github/license/yourusername/yourrepo?style=flat-square)](https://github.com/rajshankarm1213/TLDRBot/blob/main/LICENSE) [![Contributors](https://img.shields.io/github/contributors/yourusername/yourrepo?style=flat-square)](https://github.com/rajshankarm1213/TLDRBot/graphs/contributors)


# TLDRBot

TLDRBot is a Discord bot that generates a monthly summary of all the happenings on the server on the 1st of every month. It is best used for small to medium-sized servers with not more than 20-30 people.

## Features

- Automatically collects messages from all text channels in the server.
- Generates a summary of the collected messages.
- Posts the summary to a specified channel on the 1st of every month.
- Allows manual extraction and summarization of messages.
- Configurable role and channel settings for posting summaries.

## Installation

1. Invite the bot to your server using the following link:
    [Invite TLDRBot](https://discord.com/oauth2/authorize?client_id=1317749879337910283)

## Deploy Bot Locally

1. Clone the repository:
    ```sh
    git clone https://github.com/yourusername/TLDRBot.git
    cd TLDRBot
    ```

2. Create a virtual environment and activate it:
    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. Install the required packages:
    ```sh
    pip install -r requirements.txt
    ```

4. Create a [`.env`](.env ) file in the root directory and add your Discord bot token and Google API key:
    ```env
    DISCORD_TOKEN=your_discord_token
    GOOGLE_API_KEY=your_google_api_key
    ```

5. Run the bot:
    ```sh
    python bot.py
    ```

## Configuration

- Use the `$setup` command to configure the bot for your server:
    ```sh
    !setup <channel_to_post_summary> <announcement_channel> <emoji_to_react_to> <role_name> <role_color>
    ```

`<emoji_to_react_to>` should be a Unicode string. For role names with more than one word, use quotation marks. 

- Example:
    ```sh
    !setup summaries announcements \ud83d\uddd3\ufe0f "Monthly Bot Summary" 0x00ff00
    ```

## Issues/Requests

If you face any issues with the bot, please feel free to raise an issue on GitHub. I will try to resolve it as soon as possible. For any feature requests, feel to reach out to me on Discord: gunjou1213.