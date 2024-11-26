# Discord Music Bot

A simple Discord bot that plays audio from YouTube videos in voice channels.

## Prerequisites

- Python 3.8 or higher
- FFmpeg installed on your system
- Discord Bot Token

## Installation

1. Install FFmpeg:

   - **macOS**: `brew install ffmpeg`
   - **Windows**: Download from [FFmpeg website](https://ffmpeg.org/download.html)
   - **Linux**: `sudo apt-get install ffmpeg`

2. Install Python dependencies:

```bash
pip install -r requirements.txt
```

3. Set up your Discord bot:
   - Go to [Discord Developer Portal](https://discord.com/developers/applications)
   - Create a new application
   - Go to the Bot section and create a bot
   - Copy the bot token
   - Replace 'YOUR_BOT_TOKEN' in bot.py with your actual token
   - Enable MESSAGE CONTENT INTENT in the Bot section

## Usage

1. Start the bot:

```bash
python bot.py
```

2. Commands:
   - `!play [YouTube URL]` - Plays audio from the YouTube video
   - `!stop` - Stops playing and disconnects the bot

## Notes

- The bot will automatically join your voice channel when you use the play command
- You must be in a voice channel to use the play command
- The bot will stream audio instead of downloading to save space
