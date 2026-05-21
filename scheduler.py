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

    scheduler.start()
    print("✓ Scheduler started")


def stop_scheduler():
    """Stop the scheduler."""
    global scheduler
    if scheduler is not None:
        scheduler.shutdown()
        print("✓ Scheduler stopped")
