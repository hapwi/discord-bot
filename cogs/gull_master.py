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
        self.last_response = {}  # Dictionary to track last response time per user
        self.cooldown_seconds = 15  # Increased cooldown period
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
                
            # Check cooldown
            user_id = message.author.id
            current_time = datetime.now()
            if user_id in self.last_response:
                time_since_last = current_time - self.last_response[user_id]
                if time_since_last.total_seconds() < self.cooldown_seconds:
                    remaining = self.cooldown_seconds - time_since_last.total_seconds()
                    await message.channel.send(f"Slow down! Wait {int(remaining)} more seconds.")
                    return

            try:
                self.processing = True  # Set processing flag
                # Show typing indicator while generating response
                async with message.channel.typing():
                    # Get the user's message content without the mention
                    user_message = message.content.replace(f'<@{self.bot.user.id}>', '').strip()
                    
                    # Call LM Studio API with heavily optimized parameters
                    response = await self.client.chat.completions.create(
                        model="llama-3.1-8b-lexi-uncensored-v2",
                        messages=[
                            {"role": "system", "content": "You are a rude Discord bot. ONE SHORT SENTENCE ONLY. Be insulting and sarcastic."},
                            {"role": "user", "content": user_message}
                        ],
                        temperature=0.4,  # Even more focused
                        max_tokens=25,    # Very short responses
                        top_p=0.2,        # Minimal token consideration
                        presence_penalty=1.0,  # Maximum length penalty
                        frequency_penalty=1.0,  # Maximum repetition penalty
                        seed=42  # Fixed seed for more consistent performance
                    )
                    
                    # Clean and validate the response
                    cleaned_response = response.choices[0].message.content.strip()
                    if not any(cleaned_response.endswith(p) for p in ('!', '?', '.')):
                        cleaned_response += '!'
                        
                    await message.channel.send(cleaned_response)
                    
                    # Update last response time
                    self.last_response[user_id] = current_time
                    
                    # Force garbage collection after processing
                    gc.collect()
                    
            except Exception as e:
                await message.channel.send(f"Error: {str(e)}")
            finally:
                self.processing = False  # Reset processing flag
            
async def setup(bot):
    await bot.add_cog(GullMaster(bot)) 