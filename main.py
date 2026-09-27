import asyncio
import aiohttp
import discord
import os
import datetime
import tmdbsimple as tmdb
import jishaku

from discord.ext import commands, tasks
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
        
    if not check_due_records.is_running():
        check_due_records.start()
    print(f"Logged in as {bot.user}")

@tasks.loop(hours=12)
async def check_due_records():
    async with AsyncSessionLocal() as session:
        not_alerted = await BorrowingRecordDB.get_all_current_not_alerted(session)
        today = datetime.date.today()

        for record in not_alerted:
            if not record.due_date:
                continue

            # Check if 1 day before due date (due_date - today == 1 day)
            days_until_due = (record.due_date.date() - today).days

            if days_until_due == 1:
                book = await BookDB.get_by_id(session, record.book_isbn, True)
                book_title = book.title if book else record.book_isbn

                user = bot.get_user(record.user_id)
                if not user:
                    try:
                        user = await bot.fetch_user(record.user_id)
                    except Exception:
                        user = None

                if user:
                    em = (
                        discord.Embed(
                            title="📚 Library Due Date Reminder",
                            description=(
                                f"Dear {bot.librarian_role.mention},\n\n"
                                f"This is a friendly reminder that {user.mention} borrowed book **{book_title}** "
                                f"is due tomorrow (<t:{int(record.due_date.timestamp())}:D>)!\n\n"
                                f"Please return it to the Language Room (Ruang Bahasa) or request a renewal."
                            ),
                            color=discord.Color.yellow(),
                            timestamp=datetime.datetime.now(),
                        )
                    )

                    if book and hasattr(book, "get_cover_url") and book.get_cover_url("large"):
                        em.set_thumbnail(url=book.get_cover_url("large"))

                    await bot.record_channel.send(f"{bot.librarian_role.mention} Tolong dianuhkan biar gak anuh apa kali", embed=em, reference=discord.MessageReference(message_id=record.message_id, channel_id=bot.record_channel.id))

                    record.alerted = True
                    await session.commit()

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
