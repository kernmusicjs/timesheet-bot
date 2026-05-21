"""
/factures command: Scan Outlook for invoices in the current month.
"""

import discord
from discord import app_commands

async def factures_command(interaction: discord.Interaction):
    """Find and list invoices from Outlook."""
    await interaction.response.send_message(
        "⚠️ Accès Outlook non disponible — connexion admin requise pour @cadindus.fr.\n"
        "Les factures doivent être ajoutées manuellement au rapport."
    )


async def setup(bot):
    """Setup factures command."""
    bot.tree.add_command(app_commands.command(name="factures")(factures_command))
