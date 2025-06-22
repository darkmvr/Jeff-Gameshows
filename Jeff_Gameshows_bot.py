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
app = Flask("")

@app.route("/")
def home():
    return random.choice([
        "JeffBot is live and ready to hype your showcases!",
        "The countdown continues... Jeff is watching.",
        "JeffBot online! Time to get your popcorn ready.",
        "Stay tuned! Jeff's got the latest show news.",
        "Jeff says: 'World premieres incoming!'"
    ]), 200

def run_flask():
    app.run(host="0.0.0.0", port=8080)

# Start Flask in a separate daemon thread
threading.Thread(target=run_flask, daemon=True).start()

# --- Discord Bot Setup ---
SHOW_FEEDS = [
    'https://www.gematsu.com/feed',
    'https://www.ign.com/feed',
    'https://blog.playstation.com/feed/',
    'https://www.nintendo.com/whatsnew/feed/',
    'https://news.xbox.com/en-us/feed/'
]

TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

posted_links = set()
reminder_schedule = {}

# Jeff personality quotes (full list, no cuts)
jeff_quotes = [
    "Jeff says: 'Get ready for world premieres, surprises, and maybe some gamer tears. 🎤'",
    "Jeff’s hype level: Maximum!",
    "Breaking news from Jeff: the hype train never stops!",
    "Jeff’s countdown started — grab snacks and hydrate!",
    "World premieres loading… Jeff is hyped!",
    "Jeff says: ‘Stay tuned for surprises and exclusive reveals!’",
    "The gaming gods have spoken, and Jeff relays the message.",
    "Jeff’s microphone is hot — the show is coming!",
    "Grab your controllers, Jeff’s got the scoop!",
    "Jeff’s got the deets and he’s not keeping quiet!",
    "Showtime’s almost here — Jeff’s got your back!",
    "Jeff is the hype man your showcase deserves!",
    "If excitement was a currency, Jeff’s rich!",
    "Jeff’s got the insider info you need.",
    "The countdown is on — Jeff’s got the timer!",
    "Jeff says: 'Don’t blink or you’ll miss it!'",
    "Ready for surprises? Jeff already is.",
    "Jeff’s hype-o-meter is off the charts!",
    "The stage is set, Jeff’s voice is loud.",
    "Jeff says: 'This is gonna be legendary!'",
    "Get ready, get set, Jeff’s ready to shout it out!",
    "Jeff’s got more excitement than your favorite game.",
    "Hype alert: Jeff is in the building!",
    "Jeff says: 'This stream will change your life!'",
    "Countdown started — Jeff’s cheering loud.",
    "Jeff’s here to make sure you don’t miss a thing.",
    "Nothing but good vibes and hype from Jeff!",
    "Jeff’s got the best seats in the house for you.",
    "Showcasing the best, with Jeff as your guide.",
    "Jeff’s voice is your ultimate hype soundtrack.",
    "It’s happening! Jeff can barely contain himself.",
    "Jeff’s mic is ready for the big reveal!",
    "Brace yourself, Jeff’s got announcements coming.",
    "Jeff says: 'Let the games begin!'",
    "Countdown’s ticking — Jeff’s counting with you.",
    "Jeff’s hype game is stronger than ever!",
    "The spotlight’s on, and Jeff’s shining bright.",
    "Jeff’s got exclusive intel you can trust.",
    "Get hype, Jeff’s delivering the news.",
    "Jeff’s countdown reminders got you covered!",
    "Jeff says: 'Don’t miss the action, folks!'",
    "Let Jeff be your hype man all year round!",
    "Jeff’s hype train never stops rolling!"
]

jeff_statuses = [
    "hype-man duties in progress",
    "counting down to the next big reveal",
    "scouting world premieres",
    "making hype happen",
    "feeding on gamer excitement",
    "announcing surprises and delights",
    "boosting hype levels worldwide",
    "ready to drop exclusive news",
    "gathering showcase intel",
    "spreading the hype vibes",
    "warming up the mic",
    "prepping the spotlight",
    "waiting for the big moment",
    "hype meter maxed out",
    "watching streams and keeping score",
    "ready to hype your next event",
    "counting minutes till showtime",
    "Jeff’s got the inside scoop",
    "never missing a premiere",
    "keeping hype fresh daily"
]

# Event dates for sales and showcases
EVENTS = {
    "Steam Summer Sale": datetime.datetime(datetime.datetime.now().year, 6, 27, 17, 0, 0),  # June 27 5PM UTC
    "Steam Winter Sale": datetime.datetime(datetime.datetime.now().year, 12, 22, 17, 0, 0),  # Dec 22 5PM UTC
    "Nintendo Direct": None,  # Could add actual dates if desired
    "State of Play": None,
    "Game Awards": datetime.datetime(datetime.datetime.now().year, 12, 7, 1, 0, 0),
    "Summer Game Fest": None,
    "Xbox Showcase": None
}

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
        print(f"Channel ID {CHANNEL_ID} not found.")
        return

    embed = discord.Embed(
        title=f"🎮 {entry.title}",
        url=entry.link,
        description=random.choice(jeff_quotes),
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
        print(f"Channel ID {CHANNEL_ID} not found.")
        return
    if minutes_left == 0:
        msg = f"🚨 **It's LIVE!**\n▶️ [Watch here]({link})\nJeff says: 'LET'S GO. World Premieres are loading... 🎬'"
    else:
        msg = f"⏱️ **Reminder: Showcase starts in {minutes_left} minutes!**\n🔗 [Stream Link]({link})\nJeff says: 'Grab your snacks and hydrate. It’s almost showtime.'"
    await channel.send(msg)

def estimate_event_time(entry):
    # If the feed has published_parsed, we can get a datetime from it
    if hasattr(entry, 'published_parsed'):
        return datetime.datetime(*entry.published_parsed[:6])
    # fallback to 2 days from now
    return datetime.datetime.utcnow() + datetime.timedelta(days=2)

# --- Additional commands ---

@bot.command(name="countdown")
async def countdown(ctx, *, event_name=None):
    now = datetime.datetime.utcnow()
    if event_name is None:
        await ctx.send("Please specify an event name. Use `!events` to see upcoming events.")
        return
    event = EVENTS.get(event_name)
    if event is None:
        await ctx.send(f"Sorry, I don't have info on '{event_name}'. Use `!events` for known events.")
        return
    delta = event - now
    if delta.total_seconds() < 0:
        await ctx.send(f"The event '{event_name}' already happened or is happening now!")
        return
    days, seconds = delta.days, delta.seconds
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    await ctx.send(f"⏳ Countdown for **{event_name}**: {days}d {hours}h {minutes}m remaining.")

@bot.command(name="events")
async def events(ctx):
    now = datetime.datetime.utcnow()
    embed = discord.Embed(title="📅 Upcoming Jeff-Notified Events & Sales", color=0xff4500)
    for name, date in EVENTS.items():
        if date is None:
            value = "Date not set"
        else:
            if date < now:
                value = "Already happened"
            else:
                value = f"<t:{int(date.timestamp())}:F>"
        embed.add_field(name=name, value=value, inline=False)
    await ctx.send(embed=embed)

@bot.command(name="jeffinfo")
async def jeffinfo(ctx):
    embed = discord.Embed(title="🎤 JeffBot Info", color=0xff4500)
    embed.add_field(name="Bot Name", value=bot.user.name)
    embed.add_field(name="Server Count", value=len(bot.guilds))
    embed.add_field(name="Latency", value=f"{round(bot.latency * 1000)}ms")
    embed.add_field(name="Total Show Announcements", value=len(posted_links))
    await ctx.send(embed=embed)

# Override default help to avoid conflicts
@bot.command(name="helpme")
async def helpme(ctx):
    help_text = """
**JeffBot Commands:**
!countdown [event] - Get countdown to an event
!events - List upcoming events & sales
!jeffinfo - Info about JeffBot
!helpme - Show this help message
"""
    await ctx.send(help_text)

bot.run(TOKEN)
