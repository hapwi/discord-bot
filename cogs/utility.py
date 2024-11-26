import discord
from discord.ext import commands

class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='ping')
    async def ping(self, ctx):
        """Check the bot's latency"""
        latency = round(self.bot.latency * 1000)
        await ctx.send(f'🏓 Pong! Latency: {latency}ms')

    @commands.command(name='info')
    async def info(self, ctx):
        """Display information about the bot"""
        embed = discord.Embed(
            title="Bot Information",
            description="A Discord music bot with various features!",
            color=discord.Color.blue()
        )
        embed.add_field(name="Prefix", value="`g!`", inline=True)
        embed.add_field(name="Creator", value="Gull Master", inline=True)
        embed.add_field(name="Commands", value="`g!help` for a list of commands", inline=False)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Utility(bot)) 