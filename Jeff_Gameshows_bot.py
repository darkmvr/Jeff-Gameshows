import discord
from discord.ext import tasks, commands
import feedparser
import asyncio
import os
import datetime
from flask import Flask
import threading
import random

# --- Flask keep-alive server ---
app = Flask("JeffBot")

@app.route("/")
def home():
    return random.choice([
        "JeffBot is alive and kicking!",
        "Showcases incoming! JeffBot is watching.",
        "Jeff says: Stay hype, streamers!",
        "JeffBot checking the pulse of game reveals.",
        "Countdowns and announcements - JeffBot on duty!"
    ]), 200

def run_flask():
    app.run(host="0.0.0.0", port=8080)

# Start Flask in a separate thread so it doesn't block the bot
threading.Thread(target=run_flask, daemon=True).start()

# --- Discord Bot Setup ---
TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))

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

jeff_quotes = [
    "Ready to hype up some game reveals!",
    "Countdowns are Jeff’s jam. Stay tuned!",
    "Streaming news coming in hot! 🔥",
    "Jeff says: Let’s get those popcorns ready!",
    "World premieres? Jeff’s got you covered.",
    "Almost showtime! Grab your snacks!",
    "New trailers? Jeff’s eyes are glued!",
    "Surprises incoming. Jeff loves surprises.",
    "Streaming hype level: OVER 9000!",
    "Jeff’s got the exclusive scoop!",
    "Time to spill some gaming tea ☕",
    "Let’s get this show on the road!",
    "Jeff reporting live: hype is real.",
    "Get hyped! Big reveals ahead.",
    "Ready, set, stream! Jeff’s countdown started.",
    "Don’t blink or you’ll miss it!",
    "Gaming world, brace yourselves!",
    "Jeff’s got the hot takes ready.",
    "Bring the hype, bring the energy!",
    "Streaming news — Jeff’s favorite news.",
    # ... (Add as many more as you want)
]

jeff_statuses = [
    "counting down to the next big stream",
    "scouting game reveals",
    "brewing hype for announcements",
    "watching trailers like a hawk",
    "checking out the latest streams",
    "on standby for world premieres",
    "scanning feeds for exclusive news",
    "ready to drop announcements",
    "hyped for Nintendo Direct",
    "waiting for Xbox Showcase",
    "tracking Summer Game Fest",
    "loading the hype train",
    "stream alerts incoming",
    "getting those hype muscles ready",
    "sitting tight, hype on max",
    "game news in progress",
    "watching announcements closely",
    "Jeffbot’s streaming radar is on",
    "pinging stream alerts",
    "game reveals incoming",
]

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    await bot.change_presence(activity=discord.Game(random.choice(jeff_statuses)))
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
    if channel is None:
        print(f"Could not find channel with ID {CHANNEL_ID}")
        return
    embed = discord.Embed(
        title=f"🎮 {entry.title}",
        url=entry.link,
        description=f"Jeff says: '{random.choice(jeff_quotes)}'",
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
    if channel is None:
        print(f"Could not find channel with ID {CHANNEL_ID}")
        return
    if minutes_left == 0:
        msg = f"🚨 **It's LIVE!**\n▶️ [Watch here]({link})\nJeff says: 'LET'S GO. World Premieres are loading... 🎬'"
    else:
        msg = f"⏱️ **Reminder: Showcase starts in {minutes_left} minutes!**\n🔗 [Stream Link]({link})\nJeff says: 'Grab your snacks and hydrate. It’s almost showtime.'"
    await channel.send(msg)

def estimate_event_time(entry):
    # Dummy placeholder: always set event 2 days from now
    return datetime.datetime.utcnow() + datetime.timedelta(days=2)

bot.run(TOKEN)
