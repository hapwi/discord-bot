import discord
from discord.ext import commands
import yt_dlp
import asyncio
from asyncio import timeout
from discord.ui import Button, View

# YouTube DL options
YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'extractaudio': True,
    'audioformat': 'mp3',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
}

# FFmpeg options
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

# Create YT DLP client
ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=True):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        
        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **FFMPEG_OPTIONS), data=data)

class MusicPlayer:
    def __init__(self, ctx):
        self.bot = ctx.bot
        self.guild = ctx.guild
        self.channel = ctx.channel
        self.queue = []
        self.current = None
        self.next = asyncio.Event()
        self.bot.loop.create_task(self.player_loop())

    async def player_loop(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            self.next.clear()
            if not self.queue:
                try:
                    async with timeout(180):  # 3 minute timeout
                        await self.next.wait()
                except asyncio.TimeoutError:
                    return self.destroy()
                
            if len(self.queue) > 0:
                self.current = self.queue.pop(0)
                self.guild.voice_client.play(self.current, after=lambda _: self.bot.loop.call_soon_threadsafe(self.next.set))
                await self.channel.send(f'🎵 Now playing: {self.current.title}')
                await self.next.wait()

    def destroy(self):
        return self.bot.loop.create_task(self.guild.voice_client.disconnect())

class MusicControlView(View):
    def __init__(self, ctx):
        super().__init__(timeout=None)
        self.ctx = ctx

    @discord.ui.button(emoji="⏯️", style=discord.ButtonStyle.blurple)
    async def play_pause_button(self, interaction: discord.Interaction, button: Button):
        if not self.ctx.voice_client:
            return await interaction.response.send_message("❌ Not connected to a voice channel!", ephemeral=True)
            
        if self.ctx.voice_client.is_playing():
            self.ctx.voice_client.pause()
            await interaction.response.send_message("⏸️ Paused the music", ephemeral=True)
        elif self.ctx.voice_client.is_paused():
            self.ctx.voice_client.resume()
            await interaction.response.send_message("▶️ Resumed the music", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Nothing is playing!", ephemeral=True)

    @discord.ui.button(emoji="⏭️", style=discord.ButtonStyle.blurple)
    async def skip_button(self, interaction: discord.Interaction, button: Button):
        if not self.ctx.voice_client or not self.ctx.voice_client.is_playing():
            return await interaction.response.send_message("❌ Nothing to skip!", ephemeral=True)
            
        self.ctx.voice_client.stop()
        await interaction.response.send_message("⏭️ Skipped the song", ephemeral=True)

    @discord.ui.button(emoji="🔄", style=discord.ButtonStyle.blurple)
    async def queue_button(self, interaction: discord.Interaction, button: Button):
        if not hasattr(self.ctx.cog, 'players') or self.ctx.guild.id not in self.ctx.cog.players or not self.ctx.cog.players[self.ctx.guild.id].queue:
            return await interaction.response.send_message("📝 Queue is empty!", ephemeral=True)
            
        queue_list = "\n".join([f"{i+1}. {song.title}" for i, song in enumerate(self.ctx.cog.players[self.ctx.guild.id].queue)])
        await interaction.response.send_message(f"📝 **Current Queue:**\n{queue_list}", ephemeral=True)

    @discord.ui.button(emoji="⏹️", style=discord.ButtonStyle.red)
    async def stop_button(self, interaction: discord.Interaction, button: Button):
        if not self.ctx.voice_client:
            return await interaction.response.send_message("❌ Not connected to a voice channel!", ephemeral=True)
            
        if hasattr(self.ctx.cog, 'players') and self.ctx.guild.id in self.ctx.cog.players:
            self.ctx.cog.players[self.ctx.guild.id].queue.clear()
            del self.ctx.cog.players[self.ctx.guild.id]
            
        await self.ctx.voice_client.disconnect()
        await interaction.response.send_message("👋 Disconnected the bot", ephemeral=True)
        self.stop()

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.players = {}

    @commands.command(name='play')
    async def play(self, ctx, *, query=None):
        """Plays audio from a YouTube URL or search query, or resumes paused audio"""
        if not ctx.author.voice:
            return await ctx.send("❌ You need to be in a voice channel to use this command!")

        channel = ctx.author.voice.channel

        if ctx.voice_client is None:
            await channel.connect()
        elif ctx.voice_client.channel != channel:
            await ctx.voice_client.move_to(channel)

        if query is None and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            return await ctx.send("▶️ Resumed playback!")
        elif query is None:
            return await ctx.send("❌ Please provide a song to play!")

        try:
            async with ctx.typing():
                player = await YTDLSource.from_url(query, loop=self.bot.loop)
                
                if ctx.guild.id not in self.players:
                    self.players[ctx.guild.id] = MusicPlayer(ctx)
                
                self.players[ctx.guild.id].queue.append(player)
                
                if not ctx.voice_client.is_playing():
                    self.players[ctx.guild.id].next.set()
                    view = MusicControlView(ctx)
                    await ctx.send(f"🎵 Now playing: **{player.title}**\n\n*Use the buttons below to control playback:*", view=view)
                else:
                    await ctx.send(f'🎵 Added to queue: {player.title}')

        except Exception as e:
            await ctx.send(f'❌ An error occurred: {str(e)}')

    @commands.command(name='skip')
    async def skip(self, ctx):
        """Skips the current song"""
        if not ctx.voice_client or not ctx.voice_client.is_playing():
            return await ctx.send("❌ Nothing is playing right now!")
        
        ctx.voice_client.stop()
        await ctx.send("⏭️ Skipped the current song!")
        
        if ctx.guild.id in self.players and self.players[ctx.guild.id].queue:
            self.players[ctx.guild.id].next.set()

    @commands.command(name='stop')
    async def stop(self, ctx):
        """Pauses/Resumes the current song"""
        if not ctx.voice_client:
            return await ctx.send("❌ I'm not playing anything!")
            
        if ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send("⏸️ Paused the current song! Use `g!play` to resume.")
        elif ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.send("▶️ Resumed playback!")
        else:
            await ctx.send("❌ Nothing is playing right now!")

    @commands.command(name='dc')
    async def dc(self, ctx):
        """Stops playing music, clears the queue, and disconnects the bot"""
        if not ctx.voice_client:
            return await ctx.send("❌ I'm not connected to a voice channel!")
        
        if ctx.guild.id in self.players:
            self.players[ctx.guild.id].queue.clear()
            del self.players[ctx.guild.id]
        
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Disconnected from voice channel!")

    @commands.command(name='queue')
    async def queue(self, ctx):
        """Shows the current music queue"""
        if ctx.guild.id not in self.players or not self.players[ctx.guild.id].queue:
            return await ctx.send("📝 The queue is empty!")
        
        queue_list = "\n".join([f"{i+1}. {song.title}" for i, song in enumerate(self.players[ctx.guild.id].queue)])
        await ctx.send(f"📝 **Current Queue:**\n{queue_list}")

async def setup(bot):
    await bot.add_cog(Music(bot)) 