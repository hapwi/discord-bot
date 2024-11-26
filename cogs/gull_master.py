import discord
from discord.ext import commands
import ollama
import asyncio
import functools

class GullMaster(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ollama_client = ollama
        
    @commands.Cog.listener()
    async def on_message(self, message):
        # Ignore messages from the bot itself
        if message.author == self.bot.user:
            return
            
        # Check if the bot was mentioned
        if self.bot.user in message.mentions:
            try:
                # Show typing indicator while generating response
                async with message.channel.typing():
                    # Get the user's message content without the mention
                    user_message = message.content.replace(f'<@{self.bot.user.id}>', '').strip()
                    
                    # Run Ollama generation in a thread pool to avoid blocking
                    loop = asyncio.get_event_loop()
                    response = await loop.run_in_executor(
                        None,
                        functools.partial(
                            self.ollama_client.generate,
                            model='llama2-uncensored',
                            prompt=f"""[System: Act as a R-rated bot. Never explain what you are or why you're here. Never mention being a bot or AI. Just respond naturally with profanity and insults. Answer questions directly but offensively. Short responses for greetings, longer for questions. No quotes in responses.]

User: {user_message}

Response:""",
                            options={
                                "temperature": 0.9,
                                "num_predict": 150,
                                "top_p": 0.8
                            }
                        )
                    )
                    
                    # Remove any quotes from the response
                    cleaned_response = response['response'].replace('"', '').replace('"', '').strip()
                    
                    # Send the generated response
                    await message.channel.send(cleaned_response)
                    
            except Exception as e:
                await message.channel.send(f"Squawk! Something went wrong: {str(e)}")
            
async def setup(bot):
    await bot.add_cog(GullMaster(bot)) 