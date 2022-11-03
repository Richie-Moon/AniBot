import discord
from discord import app_commands
from discord.ext import commands
import utility
import anilist


class Character(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(description="Returns with character information. Will send a dropdown menu if multiple characters are found.")
    async def character(self, interaction: discord.Interaction, name: str = None, character_id: int = None):
        if name is None and character_id is None:
            await interaction.response.send_message("Please provide at least one of `name` or `characterID`.")
            return

        try:
            await interaction.response.defer()
            query = anilist.get_characters(name=name, char_id=character_id)
            if type(query) == dict:
                if query['multiple'] is True:
                    view = utility.View(data=query, name=name, remove=False, char=True)
                    await interaction.followup.send(content='The `lastPage` number may be wrong due to API restrictions.', view=view)
                else:
                    query = utility.char_value_check(query)

                    embed = discord.Embed(colour=discord.Color.blurple(), timestamp=interaction.created_at, title=query['name'], description=', '.join(query['alt_names']))
                    embed.set_author(name=interaction.user.name, icon_url=interaction.user.avatar)
                    embed = utility.char_format_embed(embed, query)

                    link_buttons = utility.LinkButton()
                    link_buttons.add_item(discord.ui.Button(style=discord.ButtonStyle.link, label=f"{query['name']} AniList Page", url=query['site_url']))

                    await interaction.followup.send(embed=embed, view=link_buttons)
            elif type(query) == list:
                embed = discord.Embed(colour=discord.Color.from_rgb(255, 0, 0), timestamp=interaction.created_at)
                for error in query:
                    embed.add_field(name=error['message'], value=f"Status code: {error['status']}")
                await interaction.response.send_message(embed=embed)

        except Exception as e:
            embed = discord.Embed(colour=discord.Color.from_rgb(255, 0, 0), timestamp=interaction.created_at)
            embed.add_field(name='Error', value=e)

            await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Character(bot))
