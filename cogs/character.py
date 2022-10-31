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
            query = anilist.get_characters(name=name, char_id=character_id)
            if type(query) == dict:
                pass
            elif type(query) == list:
                pass

        except Exception as e:
            embed = discord.Embed(colour=discord.Color.from_rgb(255, 0, 0), timestamp=interaction.created_at)
            embed.add_field(name='Error', value=e)

            await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Character(bot))
