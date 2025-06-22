import discord
import feedparser
import asyncio
import datetime
import os
from discord.ext import tasks, commands
import random

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

# Jeff’s personality quotes (100+)
jeff_quotes = [
    "Jeff says: 'Get ready for world premieres, surprises, and maybe some gamer tears. 🎤'",
    "LET'S GO! The hype train never stops here!",
    "Snack time? Nope, it's showtime!",
    "Press F to pay respects to your sleep schedule.",
    "World premieres incoming — grab your popcorn!",
    "Jeff's got the info, you bring the hype!",
    "Counting down till epicness overload!",
    "Ready your snacks and hype levels.",
    "Don't blink or you might miss the big reveal!",
    "Streaming greatness detected. Engage!",
    "Eyes glued, heart pounding — Jeff’s got you covered.",
    "This is not a drill. Showcase incoming!",
    "Get those hype muscles warmed up!",
    "Streaming soon: stay hydrated and hype ready!",
    "Alerts set. Let the games begin!",
    "Hype mode: ACTIVATED.",
    "The countdown has begun. Jeff is on it.",
    "Here comes the big one! Don’t miss out.",
    "Streaming surprises loading in 3... 2... 1...",
    "Your source for all things hype, Jeff out.",
    "Spilling tea on all upcoming showcases.",
    "Epic news incoming — Jeff’s got the scoop!",
    "Streaming alert: time to get loud!",
    "Jeff’s hype radar is 100% accurate.",
    "Stay tuned and stay hyped!",
    "Ready, set, stream!",
    "The hype is real, people!",
    "Get ready to be amazed.",
    "Jeff’s streaming senses are tingling.",
    "Epic reveals incoming — hold onto your controllers!",
    "Countdowns are Jeff’s cardio.",
    "Keep calm and hype on.",
    "Watch party starting soon — bring friends!",
    "Big announcements? Jeff’s got ’em.",
    "Prepare for hype overload!",
    "Alert! New streams ahead.",
    "The hype bus is arriving — get on!",
    "Streaming and dreaming of game gold.",
    "Jeff’s got the hottest showcase deets.",
    "Stay hyped, stay awesome.",
    "Your hype buddy has entered the chat.",
    "Announcements incoming, grab your snacks!",
    "World premieres? You know Jeff’s on it.",
    "Keep those hype meters maxed out.",
    "Live from the hype zone!",
    "Streaming updates like a pro.",
    "You bring the hype, Jeff brings the news.",
    "The countdown hype train is unstoppable.",
    "Streaming countdowns and coffee — Jeff’s fuel.",
    "Alert: hype levels rising sharply!",
    "Big reveals, big hype, Jeff approved.",
    "Stay ready, stay hype, stay Jeff.",
    "Game premieres are Jeff’s jam.",
    "Streaming vibes: 100% hype certified.",
    "Keep your hype game strong!",
    "Jeff’s on the lookout for new reveals.",
    "Time to hype like there’s no tomorrow!",
    "Ready for the hype explosion?",
    "Streaming excitement incoming.",
    "Jeff’s got the pulse on the gaming world.",
    "Get those hype fingers twitching!",
    "Countdown mode: ON.",
    "Streaming updates, all day every day.",
    "Jeff’s hype quotes: unlimited supply.",
    "Stay hyped, stay tuned.",
    "The hype never sleeps.",
    "Streaming alerts coming your way.",
    "Countdowns and hype — Jeff’s daily grind.",
    "Epic news — Jeff’s specialty.",
    "Get hyped or get left behind.",
    "Countdown to hype: Jeff style.",
    "Streaming, hype, repeat.",
    "Jeff’s got you covered for every premiere.",
    "The hype station is now boarding.",
    "Stream alerts like you’ve never seen.",
    "Big reveals ahead — Jeff says buckle up!",
    "The hype is strong with this one.",
    "Jeff delivers hype on demand.",
    "Countdown started — hype steady rising.",
    "Stay plugged in for the latest hype.",
    "Jeff’s got the inside scoop on streaming.",
    "Get hyped, gamers!",
    "Streaming news delivered with style.",
    "Countdowns, hype, and good vibes.",
    "Jeff’s hype vault is overflowing.",
    "Get ready for a hype party!",
    "Streaming alerts, no cap.",
    "The hype parade marches on.",
    "Count on Jeff for hype updates.",
    "Streaming excitement is Jeff’s playground.",
    "Hype levels at max capacity.",
    "Ready, set, hype!",
    "Countdowns fuel Jeff’s streaming soul.",
    "The hype is alive and well.",
    "Jeff’s streaming news will blow your mind.",
    "Streaming countdowns, Jeff’s way.",
    "Big news, big hype, big fun.",
    "Streaming surprises coming soon!",
    "Jeff’s hype engine is roaring.",
    "Stay tuned, stay hype, stay Jeff.",
    "Countdowns never felt so good.",
    "Streaming alerts to brighten your day."
]

# Jeff’s status messages (25+)
jeff_statuses = [
    "hunting for world premieres 🎮",
    "counting down to epic streams ⏳",
    "spilling gaming news secrets 🔥",
    "getting hype ready! 🚀",
    "scouting for surprises 🎉",
    "stream alert standby 🚨",
    "ready to hype you up 💥",
    "watching the hype meter rise 📈",
    "snacking and streaming 🍿",
    "checking those feeds 📡",
    "stream countdown mode ON ⏰",
    "curating hype content 🔍",
    "your hype guide for today 🌟",
    "breaking down stream news 📰",
    "feeling the hype vibes ⚡",
    "bringing you the hype scoop 🎤",
    "live from the hype zone 🎙️",
    "loading hype levels… 🔄",
    "gaming news on deck 🎲",
    "stream alerts incoming! 🎬",
    "ready for the big reveal! 🎭",
    "the hype never stops here! 🔥",
    "refreshing those feeds 🔄",
    "gathering hype intel 📊",
    "bringing hype and games together 🎮"
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
    if not channel:
        print(f"Channel ID {CHANNEL_ID} not found!")
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
    if not channel:
        print(f"Channel ID {CHANNEL_ID} not found!")
        return
    if minutes_left == 0:
        msg = f"🚨 **It's LIVE!**\n▶️ [Watch here]({link})\nJeff says: 'LET'S GO. World Premieres are loading... 🎬'"
    else:
        msg = f"⏱️ **Reminder: Showcase starts in {minutes_left} minutes!**\n🔗 [Stream Link]({link})\nJeff says: 'Grab your snacks and hydrate. It’s almost showtime.'"
    await channel.send(msg)

def estimate_event_time(entry):
    # This is a placeholder. You can add logic to parse dates from entry if available.
    return datetime.datetime.utcnow() + datetime.timedelta(days=2)

@bot.command()
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.send(f"🏓 Pong! Jeff's hype ping is {latency}ms.")

@bot.command()
async def uptime(ctx):
    if not hasattr(bot, 'start_time'):
        bot.start_time = datetime.datetime.utcnow()
    uptime_duration = datetime.datetime.utcnow() - bot.start_time
    await ctx.send(f"⏰ Jeff has been hyping for {str(uptime_duration).split('.')[0]}")

@bot.command()
async def status(ctx):
    await ctx.send("✅ Jeff is online and ready to hype up your streams!")

@bot.command()
async def help(ctx):
    help_text = """
**JeffBot Commands:**
`!ping` - Check Jeff's response time
`!uptime` - See how long Jeff has been hyping
`!status` - Check if Jeff is online
`!help` - Show this message
"""
    await ctx.send(help_text)

bot.run(TOKEN)
