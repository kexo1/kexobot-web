import asyncio
import os
import time
import re
import unidecode
from urllib.parse import urlparse
from fake_useragent import UserAgent

import discord
import html
import asyncpraw
import asyncprawcore
from asyncprawcore import exceptions
import requests
from bs4 import BeautifulSoup

from datetime import datetime, timedelta
from bson.objectid import ObjectId
from discord.ext import tasks, commands
from pymongo import MongoClient
from deep_translator import GoogleTranslator

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
ua = UserAgent()


class Bot(commands.Bot):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(
            intents=intents,
        )
        self.database = None

    async def on_ready(self):
        print(f'Logged in {self.user}')


bot = Bot(intents=intents)


class Scraping:
    def __init__(self):
        self.session = requests.Session()
        self.session.verify = True
        self.session.headers = {
            'User-Agent': ua.random
        }

        self.database = MongoClient(
            f"mongodb+srv://{os.getenv('MONGO_URL')}@cluster0.exygx.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")[
            "KexoBOTDatabase"]["KexoBOTCollection"]

        self.reddit = asyncpraw.Reddit(
            client_id="4JQ0g3ez1zP5zjhWvE-gNg",
            client_secret=os.getenv('REDDIT_SECRET'),
            user_agent="KexoXD",
            username="Kexotv",
            password=os.getenv('REDDIT'),
        )

        self.parts = (
            'Download ', ' + OnLine', '-P2P', ' Build', ' + Update Only', ' + Update', ' + Online',
            ' + 5 DLCs-FitGirl Repack',
            ' Hotfix 1', ')-FitGirl Repack', ' + Bonus Content DLC',
            ' Hotfix 2' ' Hotfix', ' rc', '\u200b', '-GOG', '-Repack', ' VR', '/Denuvoless', ' (Build',
            '-FitGirl Repack', '[Frankenpack]', ')')

        self.exception = (
            'Barotrauma', 'Green Hell', 'Ready or Not', 'Generation Zero', 'Evil West',
            'Devour', 'Minecraft Legends', 'The Long Drive', 'Stronghold Definitive Edition', 'Valheim', 'No Mans Sky',
            'Warhammer 40,000: Space Marine 2')

        self.split_parts = (' *', '* ', '*', '---')

    async def onlinefix(self):

        games = self.database.find_one({'_id': ObjectId('6178211ec5f5c08c699b8fd3')},
                                       {'onlinefix_cache': 1, 'games': 1})
        onlinefix_cache = games['onlinefix_cache']
        games = games['games']

        source = self.session.get('https://online-fix.me/chat.php').text

        # Remove russian text
        source = source.replace(' по сети', '')

        game_info = []
        for _ in range(10):

            pattern = re.compile(r'@0xdeadc0de</b> обновил:.*?">(.*?)<', re.DOTALL)
            match = pattern.search(source)

            if not match:
                break

            if match.group(1) in games:
                title = html.unescape(match.group(1))
                pattern = re.compile(r'@0xdeadc0de</b> обновил:.*?href="(.*?)"', re.DOTALL)
                match = pattern.search(source)
                link = match.group(1)
                game_info.append({'title': title, 'link': link})

            source = source[match.end():]

        if not game_info:
            return

        to_upload = []
        for game in game_info:
            to_upload.append(game['title'])

            if game['title'] in onlinefix_cache:
                continue
            # Online-fix game page
            source = self.session.get(game['link']).text

            # Thumbnail
            pattern = re.compile(r'<meta property="og:image" content="(.*?)"')
            match = pattern.search(source)
            image_link = match.group(1)

            # Getting description and translating text
            pattern = re.compile(r'Причина: (.*?)\n')
            match = pattern.search(source)
            description = GoogleTranslator(source='ru').translate(text=match.group(1))

            pattern = re.compile(r'version\s*(\d+(\.\d+)*)')
            version = pattern.findall(description)
            version = f' v{version[0][0]}' if version else ''

            embed = discord.Embed(title=game['title'] + version,
                                  url=game['link'],
                                  description=description, color=discord.Color.blue())
            # embed.timestamp = datetime.now(datetime.UTC)
            embed.timestamp = datetime.utcnow()

            embed.set_footer(text='https://online-fix.me',
                             icon_url='https://media.discordapp.net/attachments/796453724713123870/1035951759505506364/favicon-1.png')
            embed.set_thumbnail(url=image_link)
            game_updates = bot.get_channel(882185054174994462)
            await game_updates.send(embed=embed)

        self.database.update_one({'_id': ObjectId('6178211ec5f5c08c699b8fd3')},
                                 {'$set': {'onlinefix_cache': to_upload}})

    async def game3rb_check(self):

        games = self.database.find_one({'_id': ObjectId('6178211ec5f5c08c699b8fd3')}, {'game3rb_cache': 1, 'games': 1})
        game3rb_cache = games['game3rb_cache']
        games = '\n'.join(games['games'])

        source = self.session.get('https://www.game3rb.com/')
        game_info = []
        to_upload = []

        # If game3rb is unreachable
        if 'Bad gateway' in source.text:
            return

        soup = BeautifulSoup(source.content, 'html.parser')
        article = soup.find('article')

        if not article:
            return
        # Remove pinned games
        for sticky in article.select('article.sticky.hentry'):
            sticky.decompose()

        for _ in range(16):

            line = article.find('a', {'title': True})
            game_title = line.get('title')
            full_title = game_title

            # Check if game is online
            has_online = 'online' in game_title.lower()

            # Remove unecessary strings
            for part in self.parts:
                game_title = game_title.replace(part, '')

            game_title = game_title.split()

            # Get game version
            version = ''
            regex = re.compile(r'v\d+(\.\d+)+')
            if regex.match(game_title[-1]):
                version = f' got updated to {game_title[-1]}'
                game_title.pop()
            # If not version, get build instead
            else:
                pattern = r"Build [\d.]+"
                match = re.search(pattern, full_title)

                if not match:
                    version = 'unknown'
                else:
                    version = f' got updated to {match.group().lower()}'
                    to_remove = version.split()[-1]

                    try:
                        game_title.pop(game_title.index(to_remove))
                    except ValueError:
                        if full_title not in game3rb_cache:
                            user = await bot.fetch_user(402221830930432000)
                            await user.send(f'Incorrect version format - {full_title}')
                            to_upload.append(full_title)
                        continue

            game_title = ' '.join(game_title)

            carts = []
            for cart in article.find_all(id='cart'):
                if cart:
                    carts.append(cart.text)
                else:
                    break

            # If Game3rb stripped title in game list
            if game_title.lower() in games.lower():
                if any(game in game_title for game in self.exception):
                    # Skip loop if not online tag for required games with online tag
                    if has_online is False:
                        article = article.find_next('article')
                        continue
            else:
                article = article.find_next('article')
                continue

            game_info.append(
                {'title': game_title, 'full_title': full_title, 'version': version, 'link': line.get('href'),
                 'image': article.find('img', {'class': 'entry-image'})['src'],
                 'timestamp': article.find('time')['datetime'], 'carts': carts})
            article = article.find_next('article')

        if not game_info:
            return

        for game in game_info:
            to_upload.append(game['full_title'])
            if game['full_title'] not in game3rb_cache:

                # Game info page
                description = []
                source = self.session.get(game['link'])
                soup = BeautifulSoup(source.content, 'html.parser')

                # Torrent link
                torrent_link = soup.find('a', {'class': 'torrent'})
                if torrent_link:
                    torrent = f'[Torrent link]({torrent_link["href"]})'
                    description.append(torrent)

                # Direct link
                direct_link = soup.find('a', {'class': 'direct'})
                if direct_link:
                    direct = f'[Direct link]({direct_link["href"]})'
                    description.append(direct)

                # Game crack link
                if 'Fix already included' in str(soup) or 'Crack online already added' in str(soup):
                    description.append('_Fix already included_')
                else:
                    online_link = soup.find('a', {'class': 'online'})
                    if online_link:
                        crack = f'[Crack link]({online_link["href"]})'
                        description.append(crack)
                    else:
                        crack_link = soup.find('a', {'class': 'crack'})
                        if crack_link:
                            crack = f'[Crack link]({crack_link["href"]})'
                            description.append(crack)

                # Get update links
                game_update_link, game_update_name = [], []
                update_pattern = r'>Update (.*?)</strong>.*?<a\s+id="download-link"\s+class="update"\s+href="(.*?)"'

                for match in re.finditer(update_pattern, source.text, re.DOTALL):
                    update_name = match.group(1)
                    update_link = match.group(2)

                    # Remove any HTML tags from the update name
                    update_name = re.sub(r'<.*?>', '', update_name)
                    update_name = update_name.strip()

                    game_update_name.append(unidecode.unidecode(update_name.strip()))
                    game_update_link.append(unidecode.unidecode(update_link.strip()))

                embed = discord.Embed(title=game['title'] + game['version'], url=game['link'])
                embed.timestamp = datetime.fromisoformat(game['timestamp'])
                embed.add_field(name='Download links:',
                                value='\n'.join(description))

                if game_update_name:
                    game_update = '\n'.join(
                        f'{i + 1}. [{game_update_name[i]}]({game_update_link[i]})' for i in
                        range(len(game_update_link)))
                    embed.add_field(name='Update links:', value=game_update, inline=False)

                embed.set_footer(text=', '.join(carts),
                                 icon_url='https://media.discordapp.net/attachments/796453724713123870/1162443171209433088/d95X3.png?ex=653bf491&is=65297f91&hm=c36058433d50580eeec7cd89ddfe60965ec297d6fc8054994fee5ae976bedfd3&=')
                embed.set_image(url=game['image'])
                game_updates = bot.get_channel(882185054174994462)
                await game_updates.send(embed=embed)

        if to_upload:
            self.database.update_one({'_id': ObjectId('6178211ec5f5c08c699b8fd3')},
                                     {'$set': {'game3rb_cache': to_upload}})

    async def reddit_check(self):

        reddit_cache = self.database.find_one({'_id': ObjectId('617958fae4043ee4a3f073f2')})
        reddit_link_cache = reddit_cache['free_game_link']
        reddit_cache = reddit_link_cache

        ignore_list = self.database.find_one({'_id': ObjectId('6178211ec5f5c08c699b8fd3')})
        ignore_list = ignore_list['freegame_exceptions']

        pending_link_list = []
        subreddit = await self.reddit.subreddit("FreeGameFindings")

        try:
            async for submission in subreddit.new(limit=3):

                if submission.url not in reddit_cache:
                    if '(game)' in submission.title.lower() and 'https' in submission.url and 'virtual' not in submission.title.lower() and 'trivia' not in submission.title.lower():

                        number = [k for k in ignore_list if k in submission.url]

                        # Check if is not in blacklisted sites and database
                        if not number:
                            reddit_link_cache = [reddit_link_cache[-1]] + reddit_link_cache[:-1]
                            reddit_link_cache[0] = submission.url
                            pending_link_list.append(submission.url)

        except (
                asyncprawcore.exceptions.AsyncPrawcoreException, asyncprawcore.exceptions.RequestException,
                asyncprawcore.exceptions.ResponseException, AssertionError):
            pass

        if pending_link_list:
            tasks = []
            self.database.update_one({'_id': ObjectId('617958fae4043ee4a3f073f2')},
                                     {'$set': {
                                         'free_game_link': reddit_link_cache}})

            task_funcs = {
                'key-hub': key_hub,
                'gleam.io': gleam,
                'steelseries': steelseries,
                'alienwarearena': alienwarearena,
                'fanatical': fanatical,
            }

            for url in pending_link_list:
                for key, func in task_funcs.items():
                    if key in url:
                        tasks.append(func(url, self.session))
                        break
                else:
                    tasks.append(send_embed(('Free game - unknown site',
                                             'Keys from this site __disappear really fast__ so you should go and get it fast!',
                                             url, None, None)))

            await asyncio.gather(*tasks)

    async def crack_news(self):

        crack_cache = self.database.find_one({'_id': ObjectId('617958fae4043ee4a3f073f2')})
        crack_cache_link = crack_cache['crack_game_link']
        crack_cache = crack_cache_link

        ignore_list = self.database.find_one({'_id': ObjectId('6178211ec5f5c08c699b8fd3')})
        ignore_list = ignore_list['crackwatch_exceptions']

        subreddit = await self.reddit.subreddit('CrackWatch')

        try:
            async for submission in subreddit.new(limit=3):
                # If already checked
                if submission.permalink in crack_cache:
                    continue

                number = [k for k in ignore_list if k.lower() in submission.title.lower()]
                # If in exceptions
                if number:
                    continue

                try:
                    image_url = None
                    # If an image is in post description
                    if submission.url.endswith(('.jpg', '.jpeg', '.png')):
                        image_url = submission.url

                    description = []
                    post_description = submission.selftext

                    if post_description:

                        for part in self.split_parts:
                            post_description = post_description.replace(part, '')
                        post_description = post_description.split('\n')

                        for string in post_description:
                            string = string.strip()
                            string_low = string.lower()

                            if not string:
                                continue

                            if '.png' in string_low or '.jpeg' in string_low or '.jpg' in string_low:
                                pattern = r"\((.*?)\)"
                                match = re.findall(pattern, string)

                                if not match:
                                    continue

                                if len(match) > 1:
                                    image_url = match[1]
                                else:
                                    image_url = match[0]
                            else:
                                description.append(f'• {string}\n')

                    crack_cache_link = [crack_cache_link[-1]] + crack_cache_link[:-1]
                    crack_cache_link[0] = submission.permalink

                    embed = discord.Embed(title=submission.title[:256],
                                          url=f'https://www.reddit.com{submission.permalink}',
                                          description=''.join(description)[:4096])

                    if 'denuvo removed' in submission.title.lower() or 'denuvo removed' in ''.join(description).lower():
                        embed.color = discord.Color.gold()
                    else:
                        embed.color = discord.Color.dark_magenta()

                    if image_url:
                        embed.set_image(url=image_url)

                    embed.set_footer(text='I took it from - r/CrackWatch',
                                     icon_url='https://b.thumbs.redditmedia.com/zmVhOJSaEBYGMsE__QEZuBPSNM25gerc2hak9bQyePI.png')
                    embed.timestamp = datetime.fromtimestamp(submission.created_utc)

                    game_updates = bot.get_channel(882185054174994462)
                    await game_updates.send(embed=embed)

                except Exception as e:
                    user = await bot.fetch_user(402221830930432000)
                    await user.send(f"Incorrect embed: `{submission.permalink}`"
                                    f"\n```css\n[{e}]```"
                                    f"\nImage url: {image_url}"
                                    f"\nDescription: {post_description}")

            if crack_cache != crack_cache_link:
                self.database.update_one({'_id': ObjectId('617958fae4043ee4a3f073f2')},
                                         {'$set': {
                                             'crack_game_link': crack_cache_link}})
        # If redit is unreachable
        except (
                asyncprawcore.exceptions.AsyncPrawcoreException, asyncprawcore.exceptions.RequestException,
                asyncprawcore.exceptions.ResponseException, AssertionError):
            pass

    async def elektrina_vypadky_check(self):

        to_upload = []
        post_link = self.database.find_one({'_id': ObjectId('618945c8221f18d804636965')})
        post_link = post_link['hlinik_post_link_cache']

        source = self.session.get("https://www.hliniknadhronom.sk/mid/492460/ma0/all/.html")
        soup = BeautifulSoup(source.content, 'html.parser')
        article = soup.find(class_='oznamy-new-columns-all-list-default oznamy-new-columns-all-list')

        if not article:
            return

        # Get first 3 articles
        for i in range(3):
            article = article.find_next('div', {'class': 'short-text-envelope-default short-text-envelope'})

            if 'elektriny' not in article.find('div').text and 'elektriny' not in article.find('a')['aria-label']:
                continue

            link = f"https://www.hliniknadhronom.sk{article.find('a')['href']}"

            if link in post_link:
                continue

            to_upload.append(link)
            title = article.find('a')['aria-label']
            source = self.session.get(link)
            soup = BeautifulSoup(source.content, 'html.parser')
            post = soup.find(class_='ci-full').text

            if len(post) > 2048:
                embed = discord.Embed(title=title, url=link,
                                      description='Under embed (amount of text in embed is restricted')
                above_limit = True
            else:
                embed = discord.Embed(title=title, url=link, description=post)
                above_limit = False

            embed.timestamp = datetime.utcnow()
            embed.set_footer(text='',
                             icon_url='https://www.hliniknadhronom.sk/portals_pictures/i_006868/i_6868718.png')
            user = await bot.fetch_user(402221830930432000)
            await user.send(embed=embed)
            if above_limit is True:
                await user.send(post)

            self.database.update_one({'_id': ObjectId('618945c8221f18d804636965')},
                                     {'$set': {
                                         'hlinik_post_link_cache': to_upload}})

    async def esutaze_check(self):

        title_exceptions = self.database.find_one({'_id': ObjectId('6178211ec5f5c08c699b8fd3')})
        title_exceptions = title_exceptions['esutaze_exceptions']

        post_title = self.database.find_one({'_id': ObjectId('618945c8221f18d804636965')})
        post_title = post_title['esutaze_link_cache']

        try:
            source = self.session.get("https://www.esutaze.sk/feed/")
        except:
            return

        soup = BeautifulSoup(source.content, 'xml')
        article = soup.find('channel')

        if not article:
            print("No article in esutaze")
            return

        for i in range(3):

            article = article.find_next('item')
            title = article.find('title').text

            if title in post_title:
                return

            category = article.find('category').text

            if not (category == 'Internetové súťaže' or 'TOP SÚŤAŽ' in category):
                continue

            number = [k for k in title_exceptions if k.lower() in title]

            if number:
                continue

            post_title = [post_title[-1]] + post_title[:-1]
            post_title[0] = title

            esutaze_link = article.find('link').text
            description = html.unescape(article.find('description').text)

            pattern = re.compile(r'<p>(.*?)</p>', re.DOTALL)
            match = pattern.search(description)
            description = match.group(1)

            description = description.replace('\xa0', '\n').replace('ilustračné foto:', '')
            pos = description.find('Koniec súťaže')
            description = description[:pos] + '\n**' + description[pos:] + '**'

            source = html.unescape(article.text)

            pattern = re.compile(r'src="(.*?)"', re.DOTALL)
            match = pattern.search(source)
            image_link = match.group(1)

            pattern = re.compile(r'</h4>\n<a href="(.*?)"', re.DOTALL)
            match = pattern.search(source)
            giveaway_link = match.group(1)

            embed = discord.Embed(title=title, url=giveaway_link, description=description,
                                  colour=discord.Colour.brand_red())
            embed.set_image(url=image_link)
            embed.timestamp = datetime.utcnow()
            embed.set_footer(text=esutaze_link,
                             icon_url='https://www.startpage.com/av/proxy-image?piurl=https%3A%2F%2Fwww.esutaze.sk%2Fwp-content%2Fuploads%2F2016%2F11%2Flogo-esutaze.png&sp=1700075018T81dcbed0be165129a6c3452c1165a337a93663c6c749eacb888d407c52b0ad3f')
            user = await bot.fetch_user(402221830930432000)
            await user.send(embed=embed)

            self.database.update_one({'_id': ObjectId('618945c8221f18d804636965')},
                                     {'$set': {
                                         'esutaze_link_cache': post_title}})


class_scraping = Scraping()


@tasks.loop(hours=6)
async def daily_loop():
    now = datetime.now()
    await class_scraping.elektrina_vypadky_check()


@tasks.loop(minutes=5)
async def main_loop():
    # now = datetime.now()

    if main_loop.counter == 0:
        main_loop.counter = 1
        await class_scraping.reddit_check()

    elif main_loop.counter == 1:
        main_loop.counter = 2
        await class_scraping.game3rb_check()

    elif main_loop.counter == 2:
        main_loop.counter = 3
        await class_scraping.onlinefix()

    elif main_loop.counter == 3:
        main_loop.counter = 4
        await class_scraping.crack_news()

    elif main_loop.counter == 4:
        main_loop.counter = 0
        await class_scraping.esutaze_check()

    await change_presences(main_loop.counter)


main_loop.counter = 0


@main_loop.before_loop
async def before_my_task():
    await bot.wait_until_ready()


main_loop.start()


@daily_loop.before_loop
async def before_my_task():
    await bot.wait_until_ready()


daily_loop.start()

presences = ('Giveaways', 'r/Free Game Findings', 'Game3rb', 'Online-fix', 'r/Crack News')


async def change_presences(number):
    await bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.watching, name=presences[number]))


async def key_hub(url, session):
    source = session.get(url).text
    if 'nsfw' in source.lower():
        return

    pattern = re.compile(r'og:title" content="(.*?)-', re.DOTALL)
    match = pattern.search(source)
    if match:
        title = match.group(1)
    else:
        title = 'Free game'
        print(url)

    pattern = re.compile(r'og:image" content="(.*?)"', re.DOTALL)
    match = pattern.search(source)

    if not match:
        print(url)
        return

    await send_embed((title,
                      '**KeyHub** - keys from this site __disappear really fast__ so you should go and get it fast!',
                      url,
                      'https://cdn.discordapp.com/attachments/823205909353857085/890997523173494794/favicon-32x32.png',
                      match.group(1)))


# noinspection PyUnusedLocal
async def gleam(url, session=None):
    await send_embed(('Gleam',
                      'Gleam - keys from this site __disappear really fast__ so you should go and get it fast!',
                      url,
                      'https://media.discordapp.net/attachments/796453724713123870/1038118297914318878/favicon.png',
                      None))


# noinspection PyUnusedLocal
async def steelseries(url, session=None):
    await send_embed(('SteelSeries: Game On!',
                      'Steelseries - you will need to __install steelseries app__ so you could claim key',
                      url,
                      'https://media.discordapp.net/attachments/796453724713123870/996443673690652682/output-onlinepngtools.png',
                      None))


async def alienwarearena(url, session):
    source = session.get(url).text
    # Not working due to IP blocking
    pattern = re.compile(r'<title>(.*?)<', re.DOTALL)
    match = pattern.search(source)

    if match:
        title = html.unescape(match.group(1))
        pattern = re.compile(r'class="embed-responsive-item" src="(.*?)"', re.DOTALL)
        match = pattern.search(source)
    else:
        title = 'Free game'
        user = await bot.fetch_user(402221830930432000)
        await user.send(f"Couldn' get data: \n{source}")

    await send_embed((title,
                      '**Alienware** - keys from this site __disappear really fast__ so you should go and get it fast!',
                      url,
                      'https://media.discordapp.net/attachments/796453724713123870/1009896932929441874/unknown.png',
                      None))
    await asyncio.sleep(1)


async def fanatical(url, session):
    source = session.get(url).text

    pattern = re.compile(r'product-name">(.*?)<', re.DOTALL)
    match = pattern.search(source)
    if match:
        title = match.group(1)
    else:
        title = 'Free game'

    match = re.search(r"https://fanatical\.imgix\.net/[^\s\"]+", source)

    await send_embed((title,
                      f'**Fanatical** - sale ends <t:{str((datetime.now() + timedelta(days=5)).timestamp()).split(".")[0]}>',
                      url,
                      'https://media.discordapp.net/attachments/796453724713123870/1053672867591634965/output-onlinepngtools_1.png',
                      match.group()))


async def send_embed(info):
    # title, description, url, thumbnail: None, game_image: None
    embed = discord.Embed(title=info[0], description=info[1], color=discord.Color.dark_theme())

    url = urlparse(info[2])
    domain = url.netloc

    embed.add_field(
        name='\u200b',
        value='**[{}]({})**'.format(domain, info[2]))

    if info[3]: embed.set_thumbnail(url=info[3])

    if info[4]:
        if 'youtube' not in info[4]:
            embed.set_image(url=info[4])

    embed.set_footer(text='I took it from - r/FreeGameFindings',
                     icon_url='https://cdn.discordapp.com/attachments/796453724713123870/881868163137032212/communityIcon_xnoh6m7g9qh71.png')

    free_games = bot.get_channel(1081883673902714953)
    msg = await free_games.send(embed=embed)

    if info[4]:
        if 'youtube' in info[4]:
            link = info[4].replace('embed/', 'watch?v=')
            await msg.reply(link)


bot.run(os.getenv('DISCORD_TOKEN_2'))
