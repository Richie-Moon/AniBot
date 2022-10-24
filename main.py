import discord
from discord import app_commands
from os import environ
from dotenv import load_dotenv
import pymongo
import anilist
from discord.ext import tasks
from pymongo import errors

load_dotenv()
TOKEN = environ['TOKEN']
PASSWORD = environ['PASSWORD']

db_client = pymongo.MongoClient(f"mongodb+srv://CSA:{PASSWORD}@anibot.o2nqcvj.mongodb.net/?retryWrites=true&w=majority")

db = db_client['release_tracking']
collection = db['792309472784547850']


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


class aclient(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.all())
        self.synced = False

    async def on_ready(self):
        await self.wait_until_ready()

        tree.clear_commands(guild=None)
        for command in commands:
            tree.add_command(command)

        if not self.synced:
            await tree.sync()
            self.synced = True

        update_times.start()

        print(f"Logged in as {self.user}")


client = aclient()
tree = app_commands.CommandTree(client)


@app_commands.command(description="Displays client latency. ")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f'{round(client.latency * 1000)}ms')


def value_check(query: dict) -> dict:
    MAXLEN = 1024
    for key, value in query.items():
        if value is None or (isinstance(value, str) and len(value) == 0) or (isinstance(value, list) and len(value) == 0):
            query[key] = 'Not Available'
        elif value == 'None/None/None':
            query[key] = 'Not Available'
        elif isinstance(value, str):
            value = value.replace('<br>', '').replace('<i>', '*').replace('</i>', '*')
            value = value.replace('None/', '')
            query[key] = value
            if len(value) >= MAXLEN:
                index = len(value) - MAXLEN + 9
                query[key] = value[: -index] + '...'
    return query


def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    rgb = tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    return rgb[0], rgb[1], rgb[2]


def format_embed(embed, data) -> discord.Embed:
    if data['banner_image'] != 'Not Available':
        embed.set_image(url=data['banner_image'])
    embed.set_thumbnail(url=data['cover_image'])

    if data['is_adult'] is True:
        desc = ":warning:||" + data['desc'] + "||:warning:"
        embed.add_field(name='Description', value=desc, inline=False)
    else:
        embed.add_field(name='Description', value=data['desc'], inline=False)
    embed.add_field(name='Start Date:', value=data['start_date'])
    if data['end_date'] == 'Not Available':
        embed.add_field(name='End Date:', value=data['end_date'])
    else:
        embed.add_field(name='End Date:', value=data['end_date'])
    embed.add_field(name='Season:', value=data['season'])
    if data['airing_episodes'] != 'Not Available':
        embed.add_field(name='Airing Format:', value=f":flag_{data['origin_country']}: {data['airing_format']} ({data['airing_episodes']} Episodes, {data['episode_duration']} minutes)")
    else:
        embed.add_field(name='Airing Format:', value=f":flag_{data['origin_country']}: {data['airing_format']}")
    embed.add_field(name='Airing Status:', value=data['airing_status'])
    if data['genres'] == 'Not Available':
        embed.add_field(name='Genres:', value=data['genres'])
    else:
        embed.add_field(name='Genres', value=', '.join(data['genres']))

    if data['next_airing_episode'] == 'Not Available':
        embed.add_field(name="Next Episode:", value='This anime has finished Airing!')
    elif data['next_airing_episode'] == 'Not Yet Release':
        embed.add_field(name="Next Episode:", value=data['next_airing_episode'])
    else:
        embed.add_field(name="Next Episode:", value=f"Episode {data['next_airing_episode']['episode']} (<t:{data['next_airing_episode']['airingAt']}>, "
                                                    f"<t:{data['next_airing_episode']['airingAt']}:R>)",
                        inline=False)

    embed.add_field(name='Average Score:', value=f"**{data['average_score']}**/100")

    return embed


@app_commands.command(description="Returns with anime information. Will send a dropdown menu if multiple anime are found. ")
async def anime(interaction: discord.Interaction, name: str = None, anime_id: int = None):
    if name is None and anime_id is None:
        await interaction.response.send_message("Please provide at least one of `name` or `animeID`")
        return
    try:
        query = anilist.get_multiple(name=name, anime_id=anime_id, page=1)
        if type(query) == dict:
            try:
                if query['cover_color'] is not None:
                    r, g, b = hex_to_rgb(query['cover_color'])
                else:
                    r, g, b = 255, 255, 255
                query = value_check(query)

                embed = discord.Embed(colour=discord.Color.from_rgb(r, g, b), timestamp=interaction.created_at, title=query['name_romaji'], description=query['name_english'])
                embed.set_author(name=interaction.user.name, icon_url=interaction.user.avatar)
                embed = format_embed(embed, query)
                link_buttons = LinkButton()
                if query['trailer_url'] != 'Not Available':
                    if len(f"{query['name_romaji']} Anilist Page") > 80:
                        link_buttons.add_item(discord.ui.Button(style=discord.ButtonStyle.link, label=f"AniList Page", url=query['site_url']))
                        link_buttons.add_item(discord.ui.Button(style=discord.ButtonStyle.link, label=f"Trailer", url=query['trailer_url']))

                    elif 40 < len(f"{query['name_romaji']} Anilist Page") <= 80:
                        link_buttons.add_item(discord.ui.Button(style=discord.ButtonStyle.link, label=f"{query['name_romaji']} AniList Page", url=query['site_url'], row=1))
                        link_buttons.add_item(discord.ui.Button(style=discord.ButtonStyle.link, label=f"{query['name_romaji']} trailer", url=query['trailer_url'], row=2))

                    else:
                        link_buttons.add_item(discord.ui.Button(style=discord.ButtonStyle.link, label=f"{query['name_romaji']} AniList Page", url=query['site_url']))
                        link_buttons.add_item(discord.ui.Button(style=discord.ButtonStyle.link, label=f"{query['name_romaji']} trailer", url=query['trailer_url']))

                else:
                    if len(f"{query['name_romaji']} Trailer") > 80:
                        link_buttons.add_item(discord.ui.Button(style=discord.ButtonStyle.link, label=f"AniList Page", url=query['site_url']))
                    else:
                        link_buttons.add_item(discord.ui.Button(style=discord.ButtonStyle.link, label=f"{query['name_romaji']} AniList Page", url=query['site_url']))
                await interaction.response.send_message(embed=embed, view=link_buttons)

            except KeyError:
                await interaction.response.send_message(content='The `lastPage` number may be wrong due to API restrictions. ', view=View(query, name, send_embed=True))

        elif type(query) == list:
            embed = discord.Embed(colour=discord.Color.from_rgb(255, 0, 0), timestamp=interaction.created_at)
            for error in query:
                embed.add_field(name=error['message'], value=f"Status code: {error['status']}")
            await interaction.response.send_message(embed=embed)

    except Exception as e:
        embed = discord.Embed(colour=discord.Color.from_rgb(255, 0, 0), timestamp=interaction.created_at)
        embed.add_field(name='Error', value=e)

        await interaction.response.send_message(embed=embed)


class LinkButton(discord.ui.View):
    def __init__(self):
        super().__init__()


class Options(discord.ui.Select):
    def __init__(self, data, send_embed: bool = True, remove: bool = False):
        self.remove = remove
        self.send_embed = send_embed
        selection = []

        media = data['media']
        page_info = data['pageInfo']

        for item in media:
            title = item['title']
            if title['romaji'] == title['english']:
                selection.append(discord.SelectOption(label=title['romaji'], value=item['id']))
            else:
                selection.append(discord.SelectOption(label=title['romaji'], description=title['english'], value=item['id']))

        super().__init__(placeholder=f"Page {page_info['currentPage']} of {page_info['lastPage']}", options=selection, row=0)

    async def callback(self, interaction: discord.Interaction):
        if self.send_embed is True:
            query = anilist.get_anime(int(self.values[0]))

            if query['cover_color'] is not None:
                r, g, b = hex_to_rgb(query['cover_color'])
            else:
                r, g, b = 255, 255, 255
            query = value_check(query)

            embed = discord.Embed(colour=discord.Color.from_rgb(r, g, b), timestamp=interaction.created_at, title=query['name_romaji'], description=query['name_english'])
            embed.set_author(name=interaction.user.name, icon_url=interaction.user.avatar)
            embed = format_embed(embed, query)

            link_buttons = LinkButton()

            if query['trailer_url'] != 'Not Available':
                if len(f"{query['name_romaji']} Anilist Page") > 80:
                    link_buttons.add_item(discord.ui.Button(style=discord.ButtonStyle.link, label=f"AniList Page", url=query['site_url']))
                    link_buttons.add_item(discord.ui.Button(style=discord.ButtonStyle.link, label=f"Trailer", url=query['trailer_url']))
                elif 40 < len(f"{query['name_romaji']} Anilist Page") <= 80:
                    link_buttons.add_item(discord.ui.Button(style=discord.ButtonStyle.link, label=f"{query['name_romaji']} AniList Page", url=query['site_url'], row=1))
                    link_buttons.add_item(discord.ui.Button(style=discord.ButtonStyle.link, label=f"{query['name_romaji']} trailer", url=query['trailer_url'], row=2))
                else:
                    link_buttons.add_item(discord.ui.Button(style=discord.ButtonStyle.link, label=f"{query['name_romaji']} AniList Page", url=query['site_url']))
                    link_buttons.add_item(discord.ui.Button(style=discord.ButtonStyle.link, label=f"{query['name_romaji']} trailer", url=query['trailer_url']))

            else:
                if len(f"{query['name_romaji']} Trailer") > 80:
                    link_buttons.add_item(discord.ui.Button(style=discord.ButtonStyle.link, label=f"AniList Page", url=query['site_url']))
                else:
                    link_buttons.add_item(discord.ui.Button(style=discord.ButtonStyle.link, label=f"{query['name_romaji']} AniList Page", url=query['site_url']))

            await interaction.response.send_message(embed=embed, view=link_buttons)

        else:
            if self.remove is True:
                query = anilist.get_anime(int(self.values[0]))
                collection.delete_one({'_id': int(self.values[0])})
                if query['name_romaji'] == query['name_english'] or query['name_english'] is True:
                    await interaction.response.send_message(f"Successfully untracked **{query['name_romaji']}**")
                else:
                    await interaction.response.send_message(f"Successfully untracked **{query['name_romaji']} ({query['name_english']})**")
            else:
                try:
                    query = anilist.get_next_airing_episode(int(self.values[0]))
                    collection.insert_one({'_id': query['id'], 'time_until_airing': query['time_until_airing'], 'name_english': query['name_english'], 'name_romaji': query['name_romaji'],
                                           'airing_at': query['airing_at'], 'episode': query['episode']})
                    await interaction.response.send_mesage(f"Successfully tracking {query['name_romaji']}. "
                                                           f"Episode {query['episode']} is releasing at <t:{query['airing_at']}> (<t:{query['airing_at']}:R>)")
                except pymongo.errors.DuplicateKeyError:
                    await interaction.response.send_message('This anime is already being tracked. ')


class View(discord.ui.View):
    def __init__(self, data, name, send_embed: bool = False):
        self.name = name
        self.data = data
        self.page = self.data['pageInfo']['currentPage']
        super().__init__()
        self.select_class = Options(data=data, send_embed=send_embed)
        self.add_item(self.select_class)

        if self.page == 1:
            self.left.disabled = True
        else:
            self.left.disabled = False

        has_next_page = self.data['pageInfo']['hasNextPage']
        if has_next_page is True:
            self.right.disabled = False
        else:
            self.right.disabled = True

    def reset_buttons(self):
        self.right.disabled = False
        self.left.disabled = False

    @discord.ui.button(style=discord.ButtonStyle.primary, row=1, emoji='\U000025c0')
    async def left(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.remove_item(self.select_class)
        query = anilist.get_multiple(name=self.name, anime_id=None, page=self.page - 1)
        self.select_class = Options(query)

        self.add_item(self.select_class)

        self.reset_buttons()

        if query['pageInfo']['currentPage'] == 1:
            button.disabled = True
        else:
            button.disabled = False

        await interaction.response.edit_message(view=self)

    @discord.ui.button(style=discord.ButtonStyle.primary, row=1, emoji='\U000025b6')
    async def right(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.remove_item(self.select_class)
        query = anilist.get_multiple(name=self.name, anime_id=None, page=self.page + 1)

        self.select_class = Options(query)
        self.add_item(self.select_class)

        self.reset_buttons()

        if query['pageInfo']['hasNextPage'] is True:
            button.disabled = False
        else:
            button.disabled = True

        await interaction.response.edit_message(view=self)


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
            await interaction.response.send_message(view=View(data=query, send_embed=False, name=name))
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
            message.append(f"**{anime['name_romaji']}** Episode {anime['episode']}: <t:{anime['airing_at']}:F> (<t:{anime['airing_at']}:R>)")
        else:
            message.append(f"**{anime['name_romaji']} ({anime['name_english']})**: Episode {anime['episode']}: <t:{anime['airing_at']}:F> (<t:{anime['airing_at']}:R>)")
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
            await interaction.response.send_message(view=View(data=query, send_embed=False, name=name))
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
async def test(interaction: discord.Interaction, number: int):
    await interaction.response.send_message(number)


@app_commands.command(description="Displays Richie's to-do list.")
async def todo(interaction: discord.Interaction):
    todo_list = ["send message when new episode is released. ", 'sex', 'characters', 'user']
    await interaction.response.send_message('\n'.join(todo_list))


# TODO REMEMBER TO ADD TO COMMANDS!!!
commands = [ping, anime, help, todo, test, track, deleteall, tracking, untrack]

client.run(TOKEN)
