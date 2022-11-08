import discord
from discord import app_commands
from os import environ
from dotenv import load_dotenv
import pymongo
import anilist
from discord.ext import tasks, commands
from pymongo import errors
import utility
import datetime
import zoneinfo

load_dotenv()
TOKEN = environ['TOKEN']
PASSWORD = environ['PASSWORD']

db_client = pymongo.MongoClient(f"mongodb+srv://CSA:{PASSWORD}@anibot.o2nqcvj.mongodb.net/?retryWrites=true&w=majority")

db = db_client['release_tracking']
collection = db['792309472784547850']


@tasks.loop(minutes=4, seconds=30)
async def keep_online():
    channel = client.get_channel(1039045162749411338)
    time = datetime.datetime.now(tz=zoneinfo.ZoneInfo('Pacific/Auckland'))
    await channel.send(time.strftime("%I:%M:%S %p, %A %d %B %Y %Z"))


@tasks.loop(minutes=1.0)
async def update_times():
    embed = discord.Embed()
    channel = client.get_channel(1016581439002783784)
    tracking = collection.find()
    for anime in tracking:
        query = anilist.get_next_airing_episode(anime['_id'])
        embed.description = f"[{query['name_romaji']} AniList Page](https://anilist.co/anime/{query['id']}/)"
        if query['next_airing_episode'] is None:
            if query['name_romaji'] == query['name_english'] or query['name_english'] is None:
                embed.title = f"Episode {query['episode'] - 1} of {query['name_romaji']} just aired!"
            else:
                embed.title = f"Episode {query['episode'] - 1} of {query['name_romaji']} ({query['name_english']}) just aired!"
            await channel.send(embed=embed)
            collection.delete_one({'_id': anime['id']})

        elif query['time_until_airing'] >= anime['time_until_airing']:
            if query['name_romaji'] == query['name_english'] or query['name_english'] is None:
                embed.title = f"Episode {query['episode'] - 1} of {query['name_romaji']} just aired!"
            else:
                embed.title = f"Episode {query['episode'] - 1} of {query['name_romaji']} ({query['name_english']}) just aired!"
            await channel.send(embed=embed)
            collection.update_one({'_id': query['id']}, {'$set': {'time_until_airing': query['time_until_airing'], 'episode': query['episode'], 'airing_at': query['airing_at']}})
        else:
            collection.update_one({'_id': query['id']}, {'$set': {'time_until_airing': query['time_until_airing'], 'episode': query['episode']}})


class Bot(commands.Bot):
    def __init__(self):
        super().__init__(intents=discord.Intents.all(), application_id=1026407754899931189, command_prefix='-', heartbeat_timeout=300)

    async def setup_hook(self) -> None:
        await self.load_extension(f"cogs.character")
        await self.load_extension(f"cogs.anime")
        for command in c:
            client.tree.add_command(command)

    async def on_ready(self):
        update_times.start()
        keep_online.start()

        print(f"Logged in as {self.user}")


client = Bot()


@client.command()
async def sync(ctx):
    synced = await ctx.bot.tree.sync()
    for c in synced:
        print(c)
    await ctx.send(f"Synced {len(synced)} commands.")


@client.command()
async def commands(ctx):
    await ctx.send('\n'.join(ctx.bot.tree.get_commands()))


@app_commands.command(description="Displays client latency. ")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f'{round(client.latency * 1000)}ms')


@app_commands.command(description="Adds an anime to track when new episodes are released. ")
async def track(interaction: discord.Interaction, name: str = None, anime_id: int = None):
    await interaction.response.defer()
    if name is None and anime_id is None:
        await interaction.followup.send('You must provide at least one of `name` or `animeID`.')
        return
    query = anilist.get_multiple(name=name, anime_id=anime_id, status='RELEASING')

    if type(query) == dict:
        try:
            collection.insert_one({'_id': query['id'], 'time_until_airing': query['time_until_airing'], 'name_english': query['name_english'], 'name_romaji': query['name_romaji'],
                                   'airing_at': query['airing_at'], 'episode': query['episode']})
            if query['name_romaji'] == query['name_english'] or query['name_english'] is None:
                await interaction.followup.send(f"Successfully tracking ***{query['name_romaji']}***. Episode {query['episode']} is releasing on <t:{query['airing_at']}> "
                                                f"(<t:{query['airing_at']}:R>)")
            else:
                await interaction.followup.send(f"Successfully tracking ***{query['name_romaji']} ({query['name_english']})***. Episode {query['episode']} is releasing on <t:{query['airing_at']}> "
                                                f"(<t:{query['airing_at']}:R>)")
        except KeyError:
            await interaction.response.send_message(view=utility.View(data=query, name=name, remove=False))
        except pymongo.errors.DuplicateKeyError:
            await interaction.followup.send("Already tracking this Anime. ")
    else:
        embed = discord.Embed(colour=discord.Color.from_rgb(255, 0, 0), timestamp=interaction.created_at)
        for error in query:
            embed.add_field(name=error['message'], value=f"Status code: {error['status']}")
        await interaction.followup.send(content="If the error is `404 Not Found`, please enter a currently releasing anime. ", embed=embed)


class ConfirmButton(discord.ui.View):
    def __init__(self):
        super().__init__()

    @discord.ui.button(style=discord.ButtonStyle.red, label='CONFIRM')
    async def on_click(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != 595802642106548240:
            await interaction.response.send_message("You are not powerful enough...")
            return
        count = collection.delete_many({}).deleted_count
        button.style = discord.ButtonStyle.green
        button.disabled = True
        await interaction.response.edit_message(content=f"Successfully deleted **{count}** post/s from collection `{collection.name}`. ", view=self)


@app_commands.command(description="Displays all the anime whose releases are currently being tracked")
async def tracking(interaction: discord.Interaction):
    currently_tracking = collection.find()
    message = []
    for anime in currently_tracking:
        if anime['name_romaji'] == anime['name_english'] or anime['name_english'] is None:
            message.append(f"**{anime['name_romaji']}** - Episode {anime['episode']}: <t:{anime['airing_at']}:F> (<t:{anime['airing_at']}:R>)")
        else:
            message.append(f"**{anime['name_romaji']} ({anime['name_english']})** - Episode {anime['episode']}: <t:{anime['airing_at']}:F> (<t:{anime['airing_at']}:R>)")
    await interaction.response.send_message("***Currently Tracking:***\n" + '\n'.join(message))


@app_commands.command(description='Untracks an anime whose releases are currently being tracked. ')
async def untrack(interaction: discord.Interaction, name: str = None, anime_id: int = None):
    await interaction.response.defer()

    if name is None and anime_id is None:
        await interaction.followup.send("You must provide at least one of `name` or `animeID`. ")
        return

    query = anilist.get_multiple(name=name, anime_id=anime_id, status='RELEASING')

    if type(query) == dict:
        try:
            collection.delete_one({'_id': query['id']})
            if query['name_romaji'] == query['name_english'] or query['name_english'] is None:
                await interaction.followup.send(f"Successfully untracked **{query['name_romaji']}**.")
            else:
                await interaction.followup.send(f"Successfully untracked **{query['name_romaji']} ({query['name_english']})**.")
        except KeyError:
            await interaction.response.send_message(view=utility.View(data=query, name=name, remove=True))
    else:
        embed = discord.Embed(colour=discord.Color.from_rgb(255, 0, 0),
                              timestamp=interaction.created_at)
        for error in query:
            embed.add_field(name=error['message'], value=f"Status code: {error['status']}")
        await interaction.followup.send(content="If the error is `404 Not Found`, please enter a currently releasing anime. ", embed=embed)


@app_commands.command(description="You are not powerful enough... (unless your name is Richie Moon)")
async def deleteall(interaction: discord.Interaction):
    if interaction.user.id != 595802642106548240:
        await interaction.response.send_message("You are not powerful enough...")
        return
    button = ConfirmButton()
    await interaction.response.send_message(content=f"Are you sure you want to remove all posts from `Database: {db.name}`, `Collection: {collection.name}`?", view=button)


@app_commands.command(description='Imagine needing help.')
async def help(interaction: discord.Interaction):
    fields = {"`/anime <anime name>`": "Get anime info from Anilist.", "`/ping`": "Displays latency.", '`/todo`': "Shows the things that Richie is too lazy to implement. "}
    embed = discord.Embed(colour=discord.Color.from_rgb(255, 255, 255), timestamp=interaction.created_at, title="Help")
    count = 1
    for key, value in fields.items():
        embed.add_field(name=f"{count}. {key}", value=value, inline=False)
        count += 1

    await interaction.response.send_message(embed=embed)


@app_commands.command()
async def test(interaction: discord.Interaction):
    pass


@app_commands.command(description="Displays Richie's to-do list.")
async def todo(interaction: discord.Interaction):
    todo_list = ['sex', 'characters', 'user']
    await interaction.response.send_message('\n'.join(todo_list))


# TODO REMEMBER TO ADD TO COMMANDS!!!
c = [ping, help, todo, test, track, deleteall, tracking, untrack]

client.run(TOKEN)
