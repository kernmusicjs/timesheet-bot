"""
/rapport command: Generate monthly Excel report (timesheet + invoices), upload to Dropbox.
"""

import discord
from discord import app_commands
from datetime import datetime
import tempfile
import os
from services.dropbox_client import DropboxClient
from services.excel_builder import ExcelReportBuilder
from services.timesheet_parser import parse_timesheet_entries
from config import (
    DROPBOX_VAULT_PATH, DROPBOX_APP_KEY, DROPBOX_APP_SECRET, DROPBOX_REFRESH_TOKEN
)

FRENCH_MONTHS = {
    1: "janvier", 2: "février", 3: "mars", 4: "avril", 5: "mai", 6: "juin",
    7: "juillet", 8: "août", 9: "septembre", 10: "octobre", 11: "novembre", 12: "décembre"
}

async def rapport_command(interaction: discord.Interaction):
    """Generate monthly Excel report with timesheet + invoices."""
    await interaction.response.defer()

    try:
        now = datetime.now()
        month = now.month
        year = now.year

        # Initialize Dropbox client
        dbx = DropboxClient(DROPBOX_APP_KEY, DROPBOX_APP_SECRET, DROPBOX_REFRESH_TOKEN)

        # Get timesheet entries from Dropbox
        dropbox_timesheet_path = f"{DROPBOX_VAULT_PATH}/timesheet_{FRENCH_MONTHS[month]}_{year}.md"
        try:
            content = dbx.read_file(dropbox_timesheet_path)
            entries = parse_timesheet_entries(content) if content else []
        except:
            entries = []

        # Convert entries to dict format for Excel
        entries_data = [
            {
                "date": e.date,
                "jj_mois": e.jj_mois,
                "client": e.client,
                "affaire": e.affaire,
                "h_normales": e.h_normales,
                "h_sup": e.h_sup,
                "remarques": e.remarques
            }
            for e in entries
        ]

        # Scan Discord-uploaded PDFs in Dropbox
        now_dt = datetime(year, month, 1)
        month_name = FRENCH_MONTHS[month]
        factures_folder = f"{DROPBOX_VAULT_PATH}/factures/{year}/{month_name}"
        factures_files = dbx.list_folder(factures_folder)
        invoices = [
            {
                "received_date": now_dt.strftime("%Y-%m-%d"),
                "from": "Discord",
                "subject": f["name"],
                "pdf_attachments": [{"name": f["name"]}],
                "dropbox_link": f["path"]
            }
            for f in factures_files if f["name"].lower().endswith(".pdf")
        ]

        # Build Excel report
        builder = ExcelReportBuilder(month, year)
        summary = builder.create_report(entries_data, invoices)

        # Save to temp file
        month_name_fr = FRENCH_MONTHS[month].capitalize()
        temp_filename = f"Rapport_{month_name_fr}_{year}.xlsx"
        temp_path = os.path.join(tempfile.gettempdir(), temp_filename)

        if not builder.save(temp_path):
            await interaction.followup.send("❌ Failed to generate Excel report.")
            return

        # Upload to Dropbox
        dropbox_path = f"{DROPBOX_VAULT_PATH}/{temp_filename}"
        if not dbx.upload_binary_file(temp_path, dropbox_path):
            await interaction.followup.send("❌ Failed to upload report to Dropbox.")
            return

        # Try to get shareable link (requires sharing.write scope)
        try:
            link = dbx.get_file_link(dropbox_path)
            link_text = f"\n📄 [Lien Dropbox]({link})"
        except Exception:
            link_text = f"\n📁 Fichier: `{dropbox_path}`"

        # Clean up temp file
        try:
            os.remove(temp_path)
        except:
            pass

        await interaction.followup.send(f"✓ Rapport généré!\n\n{summary}{link_text}")

    except Exception as e:
        await interaction.followup.send(f"❌ Error generating report: {str(e)}")


async def setup(bot):
    """Setup rapport command."""
    bot.tree.add_command(app_commands.command(name="rapport")(rapport_command))
