import asyncio
import aiohttp
import discord
import os
import datetime
import tmdbsimple as tmdb
import jishaku

from discord.ext import commands
from dotenv import load_dotenv
from models.db import BorrowingRecordDB, BookDB, BorrowingStatus, AsyncSessionLocal, engine, Base
from models import (
    Book
)

from utils import (
    EC_SERVER_ID,
    RECORD_CHANNEL_ID,
    LIBRARIAN_ROLE,
    PATRON_ROLE,
    BOT_CHANNEL_ID
)
import os

# Load the .env file, you need to make a .env file with the TOKEN variable
load_dotenv()

tmdb.API_KEY = os.environ["TMDB_API_KEY"]
bot = commands.Bot(command_prefix=commands.when_mentioned_or("ec!"), intents=discord.Intents.all())
patron_role: discord.Role = None
librarian_role: discord.Role = None
record_channel: discord.TextChannel = None
bot_channel: discord.TextChannel = None

DEBUGING = False

@bot.event
async def on_ready():
    global patron_role, librarian_role, record_channel, bot_channel

    bot.patron_role = bot.get_guild(EC_SERVER_ID).get_role(PATRON_ROLE)
    bot.librarian_role = bot.get_guild(EC_SERVER_ID).get_role(LIBRARIAN_ROLE)
    bot.record_channel = bot.get_channel(RECORD_CHANNEL_ID)
    bot.bot_channel = bot.get_channel(BOT_CHANNEL_ID)
    bot.session = aiohttp.ClientSession()
    
    await bot.load_extension("jishaku")
    print(f"Loaded jishaku!")
    for cog in os.listdir('./cogs'):
        if cog.endswith('.py') == True:
            await bot.load_extension(f'cogs.{cog[:-3]}')
            print(f"Loaded {cog}")
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("Successfuly fetched books!")
    print(f"Logged in as {bot.user}")

@bot.event
async def on_command_error(ctx: commands.Context, error):
    if isinstance(error, commands.CommandOnCooldown):
        if await bot.is_owner(ctx.author):
            await ctx.reinvoke() # Bypass cooldown by reinvoking the command
        else:
            await ctx.send(
                f"Hold on there! Someone is using this command\nPlease wait in line for <t:{round(datetime.datetime.now().timestamp()) + error.retry_after:.1f}:R>",
                delete_after=5,
            )
    else:
        await ctx.send(f"Error: {error}")
        raise error


if __name__=='__main__':
    os.environ["JISHAKU_NO_UNDERSCORE"] = "true"
    os.environ["JISHAKU_RETAIN"] = "true"
    bot.run(os.environ["TOKEN"], reconnect=True)
