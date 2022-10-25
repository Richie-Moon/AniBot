import discord
from discord import app_commands
from discord.ext import commands
from os import environ
import anilist
from dotenv import load_dotenv
import pymongo

load_dotenv()
PASSWORD = environ['PASSWORD']

db_client = pymongo.MongoClient(f"mongodb+srv://CSA:{PASSWORD}@anibot.o2nqcvj.mongodb.net/?retryWrites=true&w=majority")

db = db_client['release_tracking']
collection = db['792309472784547850']


class Options(discord.ui.Select):
    def __init__(self, data, remove: bool = False):
        self.remove = remove
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


class LinkButton(discord.ui.View):
    def __init__(self):
        super().__init__()


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


class View(discord.ui.View):
    def __init__(self, data, name):
        self.name = name
        self.data = data
        self.page = self.data['pageInfo']['currentPage']
        super().__init__()
        self.select_class = Options(data=data)
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


class Anime(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(description="Returns with anime information. Will send a dropdown menu if multiple anime are found. ")
    async def anime(self, interaction: discord.Interaction, name: str = None, anime_id: int = None):
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


async def setup(bot: commands.Bot):
    await bot.add_cog(Anime(bot))
