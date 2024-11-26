import discord
from discord.ext import commands
import os
import certifi
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set SSL certificate path for Python
os.environ['SSL_CERT_FILE'] = certifi.where()

# Load opus library
if not discord.opus.is_loaded():
    try:
        discord.opus.load_opus('opus')
    except OSError:
        try:
            discord.opus.load_opus('/opt/homebrew/lib/libopus.dylib')
        except OSError:
            print("Could not load opus library. Audio functionality may not work.")

# Bot configuration
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='g!', intents=intents)

@bot.event
async def on_ready():
    print(f'Bot is ready! Logged in as {bot.user.name}')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="g!play | g!skip | g!stop | g!dc"))

async def load_extensions():
    """Load all extensions/cogs"""
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py') and not filename.startswith('__'):
            await bot.load_extension(f'cogs.{filename[:-3]}')
            print(f'Loaded extension: {filename[:-3]}')

async def main():
    """Main function to run the bot"""
    async with bot:
        await load_extensions()
        await bot.start(os.getenv('DISCORD_TOKEN'))

if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 