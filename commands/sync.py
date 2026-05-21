"""
/sync command: Read timesheet entries from iCloud, update the monthly timesheet, archive entries.
"""

import discord
from discord import app_commands
from datetime import datetime
from pathlib import Path
from services.timesheet_parser import parse_timesheet_entries, merge_entries_into_timesheet, archive_entries
from services.dropbox_client import DropboxClient
from config import TIMESHEET_ENTRIES_PATH, TIMESHEET_ENTRIES_DONE_PATH, DROPBOX_VAULT_PATH, DROPBOX_APP_KEY, DROPBOX_APP_SECRET, DROPBOX_REFRESH_TOKEN

FRENCH_MONTHS = {
    1: "janvier", 2: "février", 3: "mars", 4: "avril", 5: "mai", 6: "juin",
    7: "juillet", 8: "août", 9: "septembre", 10: "octobre", 11: "novembre", 12: "décembre"
}

class SyncCommands(app_commands.Group):
    def __init__(self, bot):
        super().__init__(name="sync", description="Timesheet sync commands")
        self.bot = bot
        self.dbx = None

    async def sync_command(self, interaction: discord.Interaction):
        """Sync timesheet entries from iCloud to Dropbox."""
        await interaction.response.defer()

        try:
            # Connect to Dropbox
            if not self.dbx:
                self.dbx = DropboxClient(DROPBOX_APP_KEY, DROPBOX_APP_SECRET, DROPBOX_REFRESH_TOKEN)

            # Read pending entries from iCloud
            if not Path(TIMESHEET_ENTRIES_PATH).exists():
                await interaction.followup.send(f"❌ Timesheet entries file not found at {TIMESHEET_ENTRIES_PATH}")
                return

            with open(TIMESHEET_ENTRIES_PATH, 'r') as f:
                pending_content = f.read()

            entries = parse_timesheet_entries(pending_content)
            if not entries:
                await interaction.followup.send("ℹ️ No new entries to sync.")
                return

            # Determine current month
            now = datetime.now()
            month_file = f"{DROPBOX_VAULT_PATH}/timesheet_{now.strftime('%B').lower()}_{now.year}.md"

            # Read existing timesheet
            existing_timesheet = self.dbx.read_file(month_file)
            if not existing_timesheet:
                # Create new timesheet if doesn't exist
                from services.timesheet_parser import create_timesheet_markdown
                existing_timesheet = create_timesheet_markdown([], now.year, now.month)

            # Merge entries
            updated_timesheet = merge_entries_into_timesheet(existing_timesheet, entries)

            # Write updated timesheet back
            if self.dbx.write_file(month_file, updated_timesheet):
                # Archive entries
                with open(TIMESHEET_ENTRIES_DONE_PATH, 'r') as f:
                    archive_content = f.read()

                updated_archive = archive_entries(archive_content, entries)

                # Write archive
                with open(TIMESHEET_ENTRIES_DONE_PATH, 'w') as f:
                    f.write(updated_archive)

                # Clear pending entries
                with open(TIMESHEET_ENTRIES_PATH, 'w') as f:
                    f.write("# Entrées heures en attente\n\nFormat: `YYYY-MM-DD | JJ-mois | Client | Affaire/Dossier | H.Sup | Remarques`\n\nAbsence: `YYYY-MM-DD | JJ-mois | — | Type (Maladie/Congés/RTT/Jour férié) | 0 |`\n")

                summary = f"""✓ Sync completed!
- Entries synced: {len(entries)}
- File updated: `{month_file}`
- Entries archived and cleared
                """
                await interaction.followup.send(summary)
            else:
                await interaction.followup.send("❌ Failed to update timesheet.")

        except Exception as e:
            await interaction.followup.send(f"❌ Error during sync: {str(e)}")


async def setup(bot):
    """Setup sync commands."""
    bot.tree.add_command(app_commands.command(name="sync")(sync_command))


async def sync_command(interaction: discord.Interaction):
    """Sync timesheet entries from iCloud to Dropbox."""
    await interaction.response.defer()

    try:
        dbx = DropboxClient(DROPBOX_APP_KEY, DROPBOX_APP_SECRET, DROPBOX_REFRESH_TOKEN)

        # Read pending entries from iCloud
        if not Path(TIMESHEET_ENTRIES_PATH).exists():
            await interaction.followup.send(f"❌ Timesheet entries file not found at {TIMESHEET_ENTRIES_PATH}")
            return

        with open(TIMESHEET_ENTRIES_PATH, 'r') as f:
            pending_content = f.read()

        entries = parse_timesheet_entries(pending_content)
        if not entries:
            await interaction.followup.send("ℹ️ No new entries to sync.")
            return

        # Determine current month
        now = datetime.now()
        month_name = FRENCH_MONTHS[now.month]
        month_file = f"{DROPBOX_VAULT_PATH}/timesheet_{month_name}_{now.year}.md"

        # Read existing timesheet
        existing_timesheet = dbx.read_file(month_file)
        if not existing_timesheet:
            # Create new timesheet if doesn't exist
            from services.timesheet_parser import create_timesheet_markdown
            existing_timesheet = create_timesheet_markdown([], now.year, now.month)

        # Merge entries
        updated_timesheet = merge_entries_into_timesheet(existing_timesheet, entries)

        # Write updated timesheet back
        if dbx.write_file(month_file, updated_timesheet):
            # Archive entries
            try:
                with open(TIMESHEET_ENTRIES_DONE_PATH, 'r') as f:
                    archive_content = f.read()
            except:
                archive_content = "# Archived Entries\n"

            updated_archive = archive_entries(archive_content, entries)

            # Write archive
            try:
                with open(TIMESHEET_ENTRIES_DONE_PATH, 'w') as f:
                    f.write(updated_archive)
            except Exception as e:
                print(f"Warning: Could not write archive: {e}")

            # Clear pending entries
            try:
                with open(TIMESHEET_ENTRIES_PATH, 'w') as f:
                    f.write("# Entrées heures en attente\n\nFormat: `YYYY-MM-DD | JJ-mois | Client | Affaire/Dossier | H.Sup | Remarques`\n\nAbsence: `YYYY-MM-DD | JJ-mois | — | Type (Maladie/Congés/RTT/Jour férié) | 0 |`\n")
            except Exception as e:
                print(f"Warning: Could not clear pending entries: {e}")

            summary = f"""✓ Sync completed!
- Entries synced: {len(entries)}
- File updated: `{month_file}`
- Entries archived and cleared
            """
            await interaction.followup.send(summary)
        else:
            await interaction.followup.send("❌ Failed to update timesheet.")

    except Exception as e:
        await interaction.followup.send(f"❌ Error during sync: {str(e)}")
