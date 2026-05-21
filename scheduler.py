"""
Scheduler for monthly automated tasks.
Uses APScheduler for reliable cron-like behavior.
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import asyncio

scheduler = None


async def generate_monthly_report(bot):
    """Generate and send monthly report."""
    try:
        from services.graph_api import GraphAPIClient
        from services.dropbox_client import DropboxClient
        from services.excel_builder import ExcelReportBuilder
        from services.timesheet_parser import parse_timesheet_entries
        from config import (
            DROPBOX_VAULT_PATH, DROPBOX_APP_KEY, DROPBOX_APP_SECRET, DROPBOX_REFRESH_TOKEN,
            MICROSOFT_REFRESH_TOKEN, TIMESHEET_ENTRIES_PATH, DISCORD_CHANNEL_ID
        )
        import tempfile
        import os

        # Get previous month
        now = datetime.now()
        if now.month == 1:
            month = 12
            year = now.year - 1
        else:
            month = now.month - 1
            year = now.year

        print(f"Generating report for {month}/{year}...")

        graph = GraphAPIClient(MICROSOFT_REFRESH_TOKEN)
        dbx = DropboxClient(DROPBOX_APP_KEY, DROPBOX_APP_SECRET, DROPBOX_REFRESH_TOKEN)

        # Get timesheet entries
        try:
            with open(TIMESHEET_ENTRIES_PATH, 'r') as f:
                pending_content = f.read()
            entries = parse_timesheet_entries(pending_content)
        except:
            entries = []

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

        # Get invoices
        invoices = graph.find_invoices(year, month)

        # Build Excel
        builder = ExcelReportBuilder(month, year)
        summary = builder.create_report(entries_data, invoices)

        month_name = datetime(year, month, 1).strftime("%B").capitalize()
        temp_filename = f"Rapport_{month_name}_{year}.xlsx"
        temp_path = os.path.join(tempfile.gettempdir(), temp_filename)

        if builder.save(temp_path):
            dropbox_path = f"{DROPBOX_VAULT_PATH}/{temp_filename}"
            if dbx.upload_binary_file(temp_path, dropbox_path):
                link = dbx.get_file_link(dropbox_path)

                # Send notification to Discord
                channel = bot.get_channel(DISCORD_CHANNEL_ID)
                if channel:
                    msg = f"""✓ Rapport mensuel généré!

{summary}

📄 [Lien Dropbox]({link})
                    """
                    await channel.send(msg)
                    print("✓ Report generated and sent to Discord")

            try:
                os.remove(temp_path)
            except:
                pass

    except Exception as e:
        print(f"✗ Error generating monthly report: {e}")
        import traceback
        traceback.print_exc()


async def archive_previous_month_excel(bot):
    """On the 1st: copy previous month's Excel into 'Factures {Month} {Year}/Feuille d'heures.xlsx'."""
    try:
        from services.dropbox_client import DropboxClient
        from config import DROPBOX_VAULT_PATH, DROPBOX_APP_KEY, DROPBOX_APP_SECRET, DROPBOX_REFRESH_TOKEN, DISCORD_CHANNEL_ID

        now = datetime.now()
        if now.month == 1:
            month, year = 12, now.year - 1
        else:
            month, year = now.month - 1, now.year

        months_cap = {1: "Janvier", 2: "Février", 3: "Mars", 4: "Avril", 5: "Mai", 6: "Juin",
                      7: "Juillet", 8: "Août", 9: "Septembre", 10: "Octobre", 11: "Novembre", 12: "Décembre"}
        month_name = months_cap[month]

        src = f"{DROPBOX_VAULT_PATH}/{month_name} {year}.xlsx"
        dst = f"{DROPBOX_VAULT_PATH}/Feuille d'heures {month_name} {year}/Feuille d'heures.xlsx"

        dbx = DropboxClient(DROPBOX_APP_KEY, DROPBOX_APP_SECRET, DROPBOX_REFRESH_TOKEN)
        try:
            dbx.dbx.files_create_folder_v2(f"{DROPBOX_VAULT_PATH}/Feuille d'heures {month_name} {year}")
        except Exception:
            pass
        try:
            dbx.dbx.files_copy_v2(src, dst, autorename=False)
        except Exception:
            # Already exists → overwrite via delete+copy
            try:
                dbx.dbx.files_delete_v2(dst)
                dbx.dbx.files_copy_v2(src, dst, autorename=False)
            except Exception as e:
                print(f"[archive] copy failed: {e}", flush=True)
                return

        channel = bot.get_channel(DISCORD_CHANNEL_ID)
        if channel:
            await channel.send(f"📦 Mois clôturé : `Feuille d'heures {month_name} {year}/` contient maintenant `Feuille d'heures.xlsx` + les factures. Prêt à envoyer à l'employeur.")
        print(f"✓ Archived {month_name} {year}", flush=True)
    except Exception as e:
        print(f"✗ archive_previous_month_excel: {e}", flush=True)
        import traceback; traceback.print_exc()


def start_monthly_scheduler(bot):
    """Start the scheduler."""
    global scheduler
    if scheduler is not None:
        return

    scheduler = AsyncIOScheduler()

    # Schedule monthly report generation: 1st of each month at 07:00
    scheduler.add_job(
        generate_monthly_report,
        CronTrigger(day=1, hour=7, minute=0),
        args=[bot],
        id="monthly_report",
        name="Generate monthly report",
        replace_existing=True
    )

    # Archive previous month's Excel into Factures folder: 1st of each month at 07:05
    scheduler.add_job(
        archive_previous_month_excel,
        CronTrigger(day=1, hour=7, minute=5),
        args=[bot],
        id="archive_month_excel",
        name="Archive previous month Excel",
        replace_existing=True
    )

    scheduler.start()
    print("✓ Scheduler started")


def stop_scheduler():
    """Stop the scheduler."""
    global scheduler
    if scheduler is not None:
        scheduler.shutdown()
        print("✓ Scheduler stopped")
