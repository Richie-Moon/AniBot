import discord
from discord import app_commands
from discord.ext import commands
from os import environ
import anilist
from dotenv import load_dotenv
import pymongo
import utility

load_dotenv()
PASSWORD = environ['PASSWORD']

db_client = pymongo.MongoClient(f"mongodb+srv://CSA:{PASSWORD}@anibot.o2nqcvj.mongodb.net/?retryWrites=true&w=majority")

db = db_client['release_tracking']
collection = db['792309472784547850']


class Anime(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(description="Returns with anime information. Will send a dropdown menu if multiple anime are found. ", name='anime')
    async def anime(self, interaction: discord.Interaction, name: str = None, anime_id: int = None):
        if name is None and anime_id is None:
            await interaction.response.send_message("Please provide at least one of `name` or `animeID`")
            return
        try:
            query = anilist.get_multiple(name=name, anime_id=anime_id, page=1)
            if type(query) == dict:
                try:
                    if query['cover_color'] is not None:
                        r, g, b = utility.hex_to_rgb(query['cover_color'])
                    else:
                        r, g, b = 255, 255, 255
                    query = utility.value_check(query)

                    embed = discord.Embed(colour=discord.Color.from_rgb(r, g, b), timestamp=interaction.created_at, title=query['name_romaji'], description=query['name_english'])
                    embed.set_author(name=interaction.user.name, icon_url=interaction.user.avatar)
                    embed = utility.format_embed(embed, query)
                    link_buttons = utility.LinkButton()
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
                    await interaction.response.send_message(content='The `lastPage` number may be wrong due to API restrictions. ', view=utility.View(query, name, remove=False))

            elif type(query) == list:
                embed = discord.Embed(colour=discord.Color.from_rgb(255, 0, 0), timestamp=interaction.created_at)
                for error in query:
                    embed.add_field(name=error['message'], value=f"Status code: {error['status']}")
                await interaction.response.send_message(embed=embed)

        except Exception as e:
            embed = discord.Embed(colour=discord.Color.from_rgb(255, 0, 0), timestamp=interaction.created_at)
            embed.add_field(name='Error', value=e)

            await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Anime(bot))
