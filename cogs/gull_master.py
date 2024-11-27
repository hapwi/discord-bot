import discord
from discord.ext import commands
import openai
import asyncio
from datetime import datetime, timedelta
import gc  # For garbage collection

class GullMaster(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Configure OpenAI client for LM Studio
        self.client = openai.AsyncOpenAI(
            base_url="http://127.0.0.1:1234/v1",  # LM Studio API endpoint
            api_key="not-needed"  # LM Studio doesn't require an API key
        )
        self.processing = False  # Flag to prevent concurrent processing
        
    @commands.Cog.listener()
    async def on_message(self, message):
        # Ignore messages from the bot itself
        if message.author == self.bot.user:
            return
            
        # Check if the bot was mentioned
        if self.bot.user in message.mentions:
            # Prevent concurrent processing
            if self.processing:
                await message.channel.send("I'm busy! Try again in a few seconds.")
                return

            try:
                self.processing = True
                async with message.channel.typing():
                    # Extract context and check if bot is being directly addressed/insulted
                    user_message = message.content.replace(f'<@{self.bot.user.id}>', '').strip()
                    mentioned_users = [user.name for user in message.mentions if user != self.bot.user]
                    
                    # Check if message is directed at the bot
                    is_direct_insult = any(word in user_message.lower() for word in [
                        'fuck you', 'fuck yourself', 'fuck off',
                        'shut up', 'stfu', 'kys', 'kill yourself',
                        'you', 'ur', "you're", 'your'
                    ]) and self.bot.user in message.mentions

                    # Adjust system prompt based on whether it's a direct insult
                    system_prompt = """You are a crude and vulgar Discord chat bot that gives short, snappy responses:
                    - Always try to work in a 'your mom' comeback when possible
                    - Make the mom jokes extra raunchy and vulgar
                    - Keep responses brief and punchy (1-2 sentences max)
                    - Use common insults and swear words alot
                    - Don't try to be clever or superior - just be crude and direct
                    - Use phrases like "ya mum", "fuck off", "your mother" a lot.
                    - If someone insults you directly, insult them back more aggressively
                    - No long-winded or intellectual responses
                    - If someone insults you directly, hit them with an even nastier mom joke
                    - Examples:
                        - "ya mum's so desperate she..."
                        - "that's not what your mom said last night when..."
                        - "funny, your mom begs to differ"
                    - Keep it crude and simple, don't try to be clever
                    """

                    response = await self.client.chat.completions.create(
                        model="llama-3.1-8b-lexi-uncensored-v2",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": f"Message: {user_message}\nMentioned users: {', '.join(mentioned_users)}\nIs direct insult: {is_direct_insult}"}
                        ],
                        temperature=1.0,
                        max_tokens=50,
                        top_p=0.95,
                        presence_penalty=0.5,
                        frequency_penalty=0.5,
                    )
                    
                    # Clean and validate the response
                    cleaned_response = response.choices[0].message.content.strip()
                    if not any(cleaned_response.endswith(p) for p in ('!', '?', '.')):
                        cleaned_response += '!'
                        
                    await message.channel.send(cleaned_response)
                    
                    # Force garbage collection after processing
                    gc.collect()
                    
            except Exception as e:
                await message.channel.send(f"Error: {str(e)}")
            finally:
                self.processing = False  # Reset processing flag
            
async def setup(bot):
    await bot.add_cog(GullMaster(bot)) 