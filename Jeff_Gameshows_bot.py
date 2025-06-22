import discord
import feedparser
import asyncio
import aiohttp
import datetime
from discord.ext import tasks, commands
import os

TOKEN = os.getenv('DISCORD_BOT_TOKEN')
CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID'))

SHOW_FEEDS = [
    'https://www.gematsu.com/feed',
    'https://www.ign.com/feed',
    'https://blog.playstation.com/feed/',
    'https://www.nintendo.com/whatsnew/feed/',
    'https://news.xbox.com/en-us/feed/'
]

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

posted_links = set()
reminder_schedule = {}

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    check_feeds.start()
    countdown_reminders.start()

@tasks.loop(minutes=15)
async def check_feeds():
    for url in SHOW_FEEDS:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            title_lower = entry.title.lower()
            if any(keyword in title_lower for keyword in [
                "nintendo direct", "state of play", "game awards",
                "xbox showcase", "summer game fest", "gamescom"
            ]):
                if entry.link not in posted_links:
                    posted_links.add(entry.link)
                    event_time = estimate_event_time(entry)
                    if event_time:
                        reminder_schedule[entry.link] = event_time
                    await post_announcement(entry, event_time)

async def post_announcement(entry, event_time):
    channel = bot.get_channel(CHANNEL_ID)
    embed = discord.Embed(
        title=f"🎮 {entry.title}",
        url=entry.link,
        description="Jeff says: 'Get ready for world premieres, surprises, and maybe some gamer tears. 🎤'",
        color=0xff0000
    )
    embed.set_author(name="JeffBot - Showcase Summoner", icon_url="https://i.imgur.com/jUxx1VQ.png")
    embed.set_thumbnail(url="https://i.imgur.com/oM3gQNa.png")
    if event_time:
        embed.add_field(name="📅 Date", value=f"<t:{int(event_time.timestamp())}:F>", inline=False)
        embed.set_footer(text="Countdown reminders set! ⏳")
    else:
        embed.add_field(name="📅 Date", value="(Not detected)", inline=False)
        embed.set_footer(text="Exact time unknown. Stay tuned!")
    embed.add_field(name="🔗 Watch Here", value=f"[Click to watch]({entry.link})", inline=False)
    await channel.send(embed=embed)

@tasks.loop(minutes=1)
async def countdown_reminders():
    now = datetime.datetime.utcnow()
    to_remove = []
    for link, event_time in reminder_schedule.items():
        minutes_left = int((event_time - now).total_seconds() / 60)
        if minutes_left in [60, 15, 0]:
            await send_reminder(link, minutes_left)
        if minutes_left <= 0:
            to_remove.append(link)
    for link in to_remove:
        reminder_schedule.pop(link, None)

async def send_reminder(link, minutes_left):
    channel = bot.get_channel(CHANNEL_ID)
    if minutes_left == 0:
        msg = f"🚨 **It's LIVE!**\n▶️ [Watch here]({link})\nJeff says: 'LET'S GO. World Premieres are loading... 🎬'"
    else:
        msg = f"⏱️ **Reminder: Showcase starts in {minutes_left} minutes!**\n🔗 [Stream Link]({link})\nJeff says: 'Grab your snacks and hydrate. It’s almost showtime.'"
    await channel.send(msg)

def estimate_event_time(entry):
    return datetime.datetime.utcnow() + datetime.timedelta(days=2)

bot.run(TOKEN)
