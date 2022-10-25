import discord
from discord import app_commands
from discord.ext import commands


class Character(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(description="Returns with character information. Will send a dropdown menu if multiple characters are found.")
    async def character(self, interaction: discord.Interaction, name: str = None, character_id: int = None):
        

async def setup(bot: commands.Bot):
    await bot.add_cog(Character(bot))
