import os

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
DISCORD_PRESENCES = ('Giveaways', 'r/FreeGameFindings', 'Game3rb', 'Online-fix', 'r/CrackwatchNews')

MONGO_DB_URL = (f"mongodb+srv://{os.getenv('MONGO_KEY')}@cluster0.exygx.mongodb.net/myFirstDatabase?retryWrites=true&w"
                f"=majority")

REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
REDDIT_SECRET = os.getenv('REDDIT_SECRET')
REDDIT_USER_AGENT = os.getenv('REDDIT_USER_AGENT')
REDDIT_USERNAME = os.getenv('REDDIT_USERNAME')
REDDIT_PASSWORD = os.getenv('REDDIT_PASSWORD')
REDDIT_STRIP = (' *', '* ', '*', '---')

GAME3RB_STRIP = (
            'Download ', ' + OnLine', '-P2P', ' Build', ' + Update Only', ' + Update', ' + Online',
            ' + 5 DLCs-FitGirl Repack',
            ' Hotfix 1', ')-FitGirl Repack', ' + Bonus Content DLC',
            ' Hotfix 2' ' Hotfix', ' rc', '\u200b', '-GOG', '-Repack', ' VR', '/Denuvoless', ' (Build',
            '-FitGirl Repack', '[Frankenpack]', ')')
GAME3RB_MUST_BE_ONLINE = (
            'barotrauma', 'green hell', 'ready or not', 'generation zero', 'evil west',
            'devour', 'minecraft legends', 'the long drive', 'stronghold definitive edition', 'valheim', 'no mans sky',
            'warhammer 40,000: space marine 2', 'abiotic factor', 'core keeper')
ONLINEFIX_MAX_GAMES = 10

REDDIT_FREEGAME_EMBEDS = {
            'gleam': (
                'Gleam',
                '**Gleam** - keys from this site __disappear really fast__ so you should go and get it fast!',
                'https://media.discordapp.net/attachments/796453724713123870/1038118297914318878/favicon.png'),
            'alienwarearena': (
                'Alienwarearena',
                '**Alienwarearena** - keys from this site __disappear really fast__ so you should go and get it fast!',
                'https://media.discordapp.net/attachments/796453724713123870/1009896932929441874/unknown.png')}

ELEKTRINA_MAX_ARTICLES = 3
ESUTAZE_MAX_ARTICLES = 3
