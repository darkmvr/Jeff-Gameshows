import discord
from discord.ext import tasks, commands
import feedparser
import asyncio
import datetime
import random
import os
from flask import Flask
import threading

# --- Flask keep-alive server ---
app = Flask("")

@app.route("/")
def home():
    return random.choice([
        "JeffBot is awake and summoning showcases! 🎮",
        "Jeff is tracking game events and sales! 🔥",
        "Ready to hype your next game reveal! 🎤",
        "JeffBot online — let’s get hyped! 🎉",
        "Stay tuned, Jeff’s got your game news! 🚀"
    ]), 200

def run_flask():
    app.run(host="0.0.0.0", port=8080)

threading.Thread(target=run_flask, daemon=True).start()

# --- Environment variables ---
TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))

# --- Jeff personality quotes (full large list) ---
jeff_quotes = [
    "Jeff says: 'Get ready for world premieres, surprises, and maybe some gamer tears. 🎤'",
    "Jeff says: 'This is gonna be good. Like, really good.'",
    "Jeff says: 'Brace yourself for hype overload!'",
    "Jeff says: 'Grab your snacks and hydrate. It’s almost showtime.'",
    "Jeff says: 'Who else is excited? Jeff is beyond hype!'",
    "Jeff says: 'Countdowns are my cardio.'",
    "Jeff says: 'Don’t blink or you’ll miss the magic.'",
    "Jeff says: 'The future of gaming is about to be revealed.'",
    "Jeff says: 'This is not a drill, folks!'",
    "Jeff says: 'Keep your eyes peeled and your ears open.'",
    "Jeff says: 'The hype is real, and I’m here for it!'",
    "Jeff says: 'World premieres incoming — better have your snacks ready!'",
    "Jeff says: 'Time to gather the hype squad! 🚀'",
    "Jeff says: 'Major announcements? You know Jeff’s on it.'",
    "Jeff says: 'Stay calm and watch the stream.'",
    "Jeff says: 'Hype levels critical, activate all notifications!'",
    "Jeff says: 'I live for these moments, don’t you?'",
    "Jeff says: 'Nothing beats the feeling of a new reveal.'",
    "Jeff says: 'Watch parties are mandatory.'",
    "Jeff says: 'It’s gonna be legendary, trust me.'",
    "Jeff says: 'Can’t wait to see your reactions!'",
    "Jeff says: 'It’s almost time... Let’s do this!'",
    "Jeff says: 'Your hype manager is on the job.'",
    "Jeff says: 'Making the impossible look possible — that’s Jeff’s motto.'",
    "Jeff says: 'Got the popcorn ready? Because it’s showtime!'",
    "Jeff says: 'The countdown starts now — hype incoming!'",
    "Jeff says: 'You don’t want to miss this, trust me.'",
    "Jeff says: 'JeffBot: your official hype coach.'",
    "Jeff says: 'Stream, hype, repeat.'",
    "Jeff says: 'Every announcement feels like Christmas morning.'",
    "Jeff says: 'Prepare your hype muscles.'",
    "Jeff says: 'We’re live in T-minus... NOW!'",
    "Jeff says: 'Buckle up for an epic ride.'",
    "Jeff says: 'From teasers to trailers, Jeff’s got it covered.'",
    "Jeff says: 'The countdown to awesome continues.'",
    "Jeff says: 'This is the hype you deserve.'",
    "Jeff says: 'Epic reveals ahead — keep your eyes glued!'",
]

# --- Jeff statuses (large list) ---
jeff_statuses = [
    "summoning game showcases 🎮",
    "tracking world premieres 🔥",
    "counting down to epic reveals ⏳",
    "hype mode: ON 🚀",
    "bringing you the freshest news 🎤",
    "waiting for the next big announcement",
    "chasing exclusive leaks 👀",
    "assembling hype squads worldwide",
    "refreshing feeds like a pro",
    "prepping for the next Game Awards",
    "gearing up for Nintendo Direct",
    "brewing coffee and counting hype minutes",
    "fine-tuning hype levels",
    "loading exclusive leaks",
    "on standby for Xbox showcase",
    "checking Steam sale rumors",
    "hyping the community daily",
    "updating countdown timers",
]

# --- Upcoming shows & sales ---
def next_date(month, day, hour=19, minute=0):
    now = datetime.datetime.utcnow()
    year = now.year
    dt = datetime.datetime(year, month, day, hour, minute)
    if dt < now:
        dt = datetime.datetime(year + 1, month, day, hour, minute)
    return dt

UPCOMING_SHOWS = [
    ("Nintendo Direct", next_date(7, 24, 15, 0)),
    ("Summer Game Fest", next_date(6, 28, 18, 0)),
    ("Gamescom", next_date(8, 21, 16, 0)),
    ("PlayStation State of Play", next_date(9, 5, 17, 0)),
    ("The Game Awards", next_date(12, 5, 1, 0)),
    ("Steam Summer Sale", next_date(6, 20, 19, 0)),
    ("Steam Halloween Sale", next_date(10, 28, 19, 0)),
    ("Steam Autumn Sale", next_date(11, 22, 19, 0)),
    ("Steam Winter Sale", next_date(12, 20, 19, 0)),
    ("Epic Mega Sale", next_date(6, 15, 19, 0)),
    ("Epic Halloween Sale", next_date(10, 25, 19, 0)),
]

# --- Show feeds to watch for ---
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

# --- Background Tasks ---

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
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
        print(f"Channel {CHANNEL_ID} not found.")
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
        return
    if minutes_left == 0:
        msg = f"🚨 **It's LIVE!**\n▶️ [Watch here]({link})\nJeff says: 'LET'S GO. World Premieres are loading... 🎬'"
    else:
        msg = f"⏱️ **Reminder: Showcase starts in {minutes_left} minutes!**\n🔗 [Stream Link]({link})\nJeff says: 'Grab your snacks and hydrate. It’s almost showtime.'"
    await channel.send(msg)

def estimate_event_time(entry):
    # Placeholder: guess 2 days from now if no date in feed
    return datetime.datetime.utcnow() + datetime.timedelta(days=2)

# --- Commands ---

@bot.command(name="upcoming")
async def upcoming(ctx):
    now = datetime.datetime.utcnow()
    upcoming_events = [(name, dt) for (name, dt) in UPCOMING_SHOWS if dt > now]
    if not upcoming_events:
        await ctx.send("Jeff says: No upcoming shows or sales found! Stay tuned.")
        return
    upcoming_events.sort(key=lambda x: x[1])
    embed = discord.Embed(
        title="🎉 Upcoming Game Showcases & Sales",
        color=0xff4500,
        timestamp=now
    )
    for name, dt in upcoming_events:
        delta = dt - now
        days = delta.days
        hours = delta.seconds // 3600
        embed.add_field(name=name, value=f"Starts in {days}d {hours}h — <t:{int(dt.timestamp())}:F>", inline=False)
    embed.set_footer(text="JeffBot countdowns powered by hype and caffeine.")
    await ctx.send(embed=embed)

@bot.command(name="jeff")
async def jeff_info(ctx):
    embed = discord.Embed(title="🎤 JeffBot Info & Personality", color=0xff0000)
    embed.add_field(name="Status", value=random.choice(jeff_statuses), inline=False)
    embed.add_field(name="Quotes Sample", value=random.choice(jeff_quotes), inline=False)
    embed.set_footer(text="Powered by Jeff's endless hype.")
    await ctx.send(embed=embed)

@bot.command(name="ping")
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.send(f"🏓 Pong! JeffBot's brain ping is {latency}ms.")

@bot.command(name="help")
async def help_command(ctx):
    commands_info = {
        "!upcoming": "Show upcoming showcases & sales countdown",
        "!jeff": "Learn about JeffBot's personality",
        "!ping": "Check bot latency",
        "!help": "Show this help message"
    }
    embed = discord.Embed(title="📋 JeffBot Commands", color=discord.Color.gold())
    for cmd, desc in commands_info.items():
        embed.add_field(name=cmd, value=desc, inline=False)
    embed.set_footer(text="Stay hyped, stay gaming! 🎮")
    await ctx.send(embed=embed)

# --- Run the bot ---
if not TOKEN:
    print("ERROR: DISCORD_TOKEN environment variable missing!")
else:
    bot.run(TOKEN)
