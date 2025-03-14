import os
import discord
import asyncpraw
import requests
import logging
import dns.resolver

from fake_useragent import UserAgent
from discord.ext import tasks, commands
from constants import DISCORD_TOKEN, DISCORD_PRESENCES, MONGO_DB_URL, REDDIT_PASSWORD, REDDIT_SECRET,  \
    REDDIT_USER_AGENT, REDDIT_USERNAME, REDDIT_CLIENT_ID

dns.resolver.default_resolver = dns.resolver.Resolver(configure=False)
dns.resolver.default_resolver.nameservers = ['8.8.8.8']
import pymongo
from pymongo import MongoClient

from onlinefix import OnlineFix
from game3rb import Game3rb
from reddit_freegamefindings import RedditFreegamefindings
from reddit_crackwatch import RedditCrackwatch
from elektrina_vypadky import ElektrinaVypadky
from esutaze import Esutaze

# Turn off unnecessary intents to save ram
intents = discord.Intents.default()
# noinspection PyUnresolvedReferences
intents.auto_moderation_configuration = False
intents.auto_moderation_execution = False
intents.message_content = True
intents.reactions = False
intents.bans = False
intents.dm_reactions = False
intents.emojis = False
intents.emojis_and_stickers = False
intents.invites = False
intents.scheduled_events = False
intents.webhooks = False
intents.voice_states = False

logging.basicConfig(level=logging.INFO)
logging.getLogger('discord').setLevel(logging.WARNING)
user_agent = UserAgent()


class Bot(commands.Bot):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(
            intents=intents,
        )
        self.database = None

    async def on_ready(self):
        logging.info(f'Logged in as {self.user}')


bot = Bot(intents=intents)


class KexoBOTWeb:
    def __init__(self):
        self.user_kexo = discord.User
        self.session = requests.Session()
        self.session.verify = True
        self.session.headers = {'User-Agent': user_agent.random}

        self.database = MongoClient(MONGO_DB_URL)["KexoBOTDatabase"]["KexoBOTCollection"]

        self.reddit = asyncpraw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_SECRET,
            user_agent=REDDIT_USER_AGENT,
            username=REDDIT_USERNAME,
            password=REDDIT_PASSWORD,
        )

    async def initialize_users(self):
        self.user_kexo = await bot.fetch_user(402221830930432000)


kexobot_web = KexoBOTWeb()

onlinefix = OnlineFix(kexobot_web.session, kexobot_web.database, bot)
game3rb = Game3rb(kexobot_web.session, kexobot_web.database, bot)
reddit_freegamefindings = RedditFreegamefindings(kexobot_web.session, kexobot_web.database, kexobot_web.reddit)
reddit_crackwatch = RedditCrackwatch(kexobot_web.session, kexobot_web.database, kexobot_web.reddit, bot)
elektrina_vypadky = ElektrinaVypadky(kexobot_web.session, kexobot_web.database, kexobot_web.user_kexo)
esutaze = Esutaze(kexobot_web.session, kexobot_web.database, bot)


@tasks.loop(hours=1)
async def daily_loop():
    # now = datetime.now()
    # Randomize user agent

    kexobot_web.session.headers = {'User-Agent': user_agent.random}
    await elektrina_vypadky.run()


@tasks.loop(minutes=5)
async def main_loop():
    # now = datetime.now()

    if main_loop.counter == 0:
        main_loop.counter = 1
        await reddit_freegamefindings.run()

    elif main_loop.counter == 1:
        main_loop.counter = 2
        await game3rb.run()

    elif main_loop.counter == 2:
        main_loop.counter = 3
        await onlinefix.run()

    elif main_loop.counter == 3:
        main_loop.counter = 4
        await reddit_crackwatch.run()

    elif main_loop.counter == 4:
        main_loop.counter = 0
        await esutaze.run()

    await change_presences(main_loop.counter)


main_loop.counter = 0


@main_loop.before_loop
async def before_my_task():
    await bot.wait_until_ready()


main_loop.start()


@daily_loop.before_loop
async def before_my_task():
    await bot.wait_until_ready()
    await kexobot_web.initialize_users()
    elektrina_vypadky.user_kexo = kexobot_web.user_kexo


daily_loop.start()


async def change_presences(number):
    await bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.watching, name=DISCORD_PRESENCES[number]))


bot.run(DISCORD_TOKEN)
