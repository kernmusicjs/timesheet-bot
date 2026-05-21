"""
/status command: Show system status (pending entries, last sync, last report).
"""

import discord
from discord import app_commands
from pathlib import Path
from services.timesheet_parser import parse_timesheet_entries
from config import TIMESHEET_ENTRIES_PATH

async def status_command(interaction: discord.Interaction):
    """Show current status."""
    await interaction.response.defer()

    try:
        status_msg = "📊 **Statut du système**\n\n"

        # Check pending entries
        if Path(TIMESHEET_ENTRIES_PATH).exists():
            with open(TIMESHEET_ENTRIES_PATH, 'r') as f:
                content = f.read()
            entries = parse_timesheet_entries(content)
            status_msg += f"⏳ Entrées en attente: {len(entries)}\n"
        else:
            status_msg += "⏳ Entrées en attente: 0 (fichier non trouvé)\n"

        status_msg += f"\n✓ Bot en ligne et actif"

        await interaction.followup.send(status_msg)

    except Exception as e:
        await interaction.followup.send(f"❌ Error getting status: {str(e)}")


async def setup(bot):
    """Setup status command."""
    bot.tree.add_command(app_commands.command(name="status")(status_command))
