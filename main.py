"""
Main Discord bot entry point.
Initializes the bot, registers commands, and starts the scheduler.
"""

import discord
from discord.ext import commands, tasks
from datetime import datetime
import asyncio
from config import DISCORD_BOT_TOKEN, DISCORD_GUILD_ID, DISCORD_CHANNEL_ID, DROPBOX_APP_KEY, DROPBOX_APP_SECRET, DROPBOX_REFRESH_TOKEN, DROPBOX_VAULT_PATH, EXCEL_TIMESHEET_BASE_PATH
from commands import sync, rapport, factures, status, fh
from scheduler import start_monthly_scheduler
from services.dropbox_client import DropboxClient
import state

FRENCH_MONTHS = {
    1: "janvier", 2: "février", 3: "mars", 4: "avril", 5: "mai", 6: "juin",
    7: "juillet", 8: "août", 9: "septembre", 10: "octobre", 11: "novembre", 12: "décembre"
}

FRENCH_MONTHS_CAP = {k: v.capitalize() for k, v in FRENCH_MONTHS.items()}


def _safe_name(s: str) -> str:
    """Sanitize a string for use in a filename."""
    import re as _re
    return _re.sub(r'[^\w\-\.€ ,]', '_', s).strip() or "X"


def invoice_filename(vendor: str, total: str, invoice_date) -> str:
    """Generate consistent invoice filename: 'Amazon 7,98€ 20-05.pdf'."""
    total_fr = (total or "?").replace(".", ",")
    return f"{_safe_name(vendor)} {_safe_name(total_fr)}€ {invoice_date.strftime('%d-%m')}.pdf"


def _upload_invoice_pdf(content: bytes, original_filename: str, vendor: str, total: str, invoice_date) -> None:
    """Upload PDF to Dropbox in 'Factures {Month} {Year}/' folder next to the Excel."""
    month_name = FRENCH_MONTHS_CAP[invoice_date.month]
    folder = f"{DROPBOX_VAULT_PATH}/Factures {month_name} {invoice_date.year}"
    fname = invoice_filename(vendor, total, invoice_date)
    dbx = DropboxClient(DROPBOX_APP_KEY, DROPBOX_APP_SECRET, DROPBOX_REFRESH_TOKEN)
    dbx.create_folder(folder)
    dbx.upload_bytes(content, f"{folder}/{fname}")

# Initialize bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)


@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: Exception):
    print(f"✗ Slash command error: {type(error).__name__}: {error}", flush=True)
    import traceback
    traceback.print_exc()
    try:
        await interaction.response.send_message(f"❌ Erreur: {error}", ephemeral=True)
    except Exception:
        pass


@bot.event
async def on_ready():
    """Called when bot is ready."""
    import sys
    print(f"✓ Bot logged in as {bot.user}", flush=True)
    try:
        if DISCORD_GUILD_ID:
            guild = discord.Object(id=DISCORD_GUILD_ID)
            bot.tree.copy_global_to(guild=guild)
            synced = await bot.tree.sync(guild=guild)
        else:
            synced = await bot.tree.sync()
        print(f"✓ Commands synced: {[c.name for c in synced]}", flush=True)
    except Exception as e:
        print(f"✗ Command sync failed: {type(e).__name__}: {e}", flush=True)

    try:
        scheduler_task.start()
        print("✓ Scheduler started", flush=True)
    except Exception as e:
        print(f"✗ Scheduler error: {e}", flush=True)


@tasks.loop(minutes=1)
async def scheduler_task():
    """Check scheduled tasks every minute."""
    now = datetime.now()
    # Monthly report: 1st of month at 07:00
    if now.day == 1 and now.hour == 7 and now.minute == 0:
        await run_monthly_report()
    # Daily timesheet prompt: 16:00, workdays only (Mon–Fri)
    if now.weekday() < 5 and now.hour == 16 and now.minute == 0:
        channel = bot.get_channel(DISCORD_CHANNEL_ID)
        if channel:
            day_names = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"]
            day_label = f"{day_names[now.weekday()]} {now.day:02d}/{now.month:02d}"
            await channel.send(
                f"⏰ **Feuille d'heures — {day_label}** — Que as-tu fait aujourd'hui?\n"
                "Format: `Client, Affaire` ou `Client, Affaire, H.Sup` ou `Congé` / `Maladie` / `RTT`\n"
                "_(virgule, slash ou pipe acceptés — H. Normales auto: 8h lun–jeu, 7h ven)_"
            )
            state.awaiting_timesheet = True
            state.pending_date = None


@scheduler_task.before_loop
async def before_scheduler():
    """Wait for bot to be ready before starting scheduler."""
    await bot.wait_until_ready()


async def run_monthly_report():
    """Run the monthly report generation and send to Discord."""
    try:
        from services.graph_api import GraphAPIClient
        from services.dropbox_client import DropboxClient
        from services.excel_builder import ExcelReportBuilder
        from services.timesheet_parser import parse_timesheet_entries
        from config import (
            DROPBOX_VAULT_PATH, DROPBOX_APP_KEY, DROPBOX_APP_SECRET, DROPBOX_REFRESH_TOKEN,
            MICROSOFT_REFRESH_TOKEN, TIMESHEET_ENTRIES_PATH
        )
        import tempfile
        import os

        now = datetime.now()
        month = now.month - 1 if now.month > 1 else 12
        year = now.year if now.month > 1 else now.year - 1

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

        month_name_fr = FRENCH_MONTHS[month].capitalize()
        temp_filename = f"Rapport_{month_name_fr}_{year}.xlsx"
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

            try:
                os.remove(temp_path)
            except:
                pass

    except Exception as e:
        print(f"Error running monthly report: {e}")


@bot.event
async def on_message(message: discord.Message):
    """Handle PDF uploads and daily timesheet responses."""
    if message.author.bot:
        await bot.process_commands(message)
        return

    print(f"[on_message] ch={message.channel.id} expected={DISCORD_CHANNEL_ID} awaiting={state.awaiting_timesheet} content={message.content[:40]!r}", flush=True)

    if message.channel.id != DISCORD_CHANNEL_ID:
        await bot.process_commands(message)
        return

    # Skip slash commands
    if message.content.startswith("/"):
        await bot.process_commands(message)
        return

    # Handle invoice confirmation reply
    if state.awaiting_invoice_confirm and not message.attachments:
        content_lower = message.content.strip().lower()
        if content_lower in ("oui", "o", "ok", "yes", "✅", "confirmer", "confirm"):
            state.awaiting_invoice_confirm = False
            inv = state.pending_invoice
            state.pending_invoice = None
            if inv and inv.get("vendor") and inv.get("total") and inv.get("date"):
                try:
                    from services.excel_updater import update_observation
                    result = update_observation(EXCEL_TIMESHEET_BASE_PATH, inv["vendor"], inv["total"], inv["date"])
                    if inv.get("pdf_bytes"):
                        try:
                            _upload_invoice_pdf(inv["pdf_bytes"], inv["pdf_filename"], inv["vendor"], inv["total"], inv["date"])
                            result += " 📎"
                        except Exception as e:
                            print(f"[invoice] PDF upload failed: {e}", flush=True)
                except Exception as e:
                    result = f"❌ Erreur: {e}"
                await message.reply(result)
            else:
                await message.reply("❌ Données incomplètes. Réponds avec: `Vendeur, total, DD/MM`")
        elif content_lower in ("non", "n", "no", "annuler", "cancel"):
            state.awaiting_invoice_confirm = False
            state.pending_invoice = None
            await message.reply("❌ Facture annulée.")
        else:
            # Manual correction: "Amazon, 42.50, 15/05"
            state.awaiting_invoice_confirm = False
            try:
                from services.invoice_parser import parse_manual_correction, save_correction
                from services.excel_updater import update_observation
                corrected = parse_manual_correction(message.content)
                pending = state.pending_invoice or {}
                raw_text = pending.get("raw_text", "")
                state.pending_invoice = None
                if corrected.get("vendor") and corrected.get("total") and corrected.get("date"):
                    result = update_observation(EXCEL_TIMESHEET_BASE_PATH, corrected["vendor"], corrected["total"], corrected["date"])
                    if pending.get("pdf_bytes"):
                        try:
                            _upload_invoice_pdf(pending["pdf_bytes"], pending["pdf_filename"], corrected["vendor"], corrected["total"], corrected["date"])
                            result += " 📎"
                        except Exception as e:
                            print(f"[invoice] PDF upload failed: {e}", flush=True)
                    if raw_text:
                        try:
                            save_correction(raw_text, corrected["vendor"], corrected["total"], corrected["date"])
                            result += " 📚"
                        except Exception as e:
                            print(f"[invoice] save_correction failed: {e}", flush=True)
                else:
                    result = "❌ Format invalide. Utilise: `Vendeur, total, DD/MM`"
            except Exception as e:
                result = f"❌ Erreur: {e}"
            await message.reply(result)
        await bot.process_commands(message)
        return

    # Handle daily timesheet response
    if state.awaiting_timesheet and not message.attachments:
        state.awaiting_timesheet = False
        try:
            from services.excel_updater import parse_response, update_excel_entry
            from datetime import date
            target = state.pending_date if state.pending_date is not None else date.today()
            state.pending_date = None
            print(f"[timesheet] target={target} base={EXCEL_TIMESHEET_BASE_PATH}", flush=True)
            entry = parse_response(message.content, target)
            print(f"[timesheet] entry={entry}", flush=True)
            result = update_excel_entry(EXCEL_TIMESHEET_BASE_PATH, entry, target)
            print(f"[timesheet] result={result}", flush=True)
        except Exception as e:
            import traceback
            traceback.print_exc()
            result = f"❌ Erreur: {e}"
        await message.reply(result)
        await bot.process_commands(message)
        return

    # Handle invoice/image attachments
    invoice_extensions = ('.pdf', '.jpg', '.jpeg', '.png', '.heic', '.webp')
    invoice_attachments = [a for a in message.attachments if a.filename.lower().endswith(invoice_extensions)]
    if not invoice_attachments:
        await bot.process_commands(message)
        return

    try:
        from services.invoice_parser import extract_text, parse_invoice

        for attachment in invoice_attachments:
            content = await attachment.read()

            # Parse invoice (upload to Dropbox deferred until confirmation)
            text = extract_text(content, attachment.filename)
            inv = parse_invoice(text)

            vendor = inv.get("vendor") or "?"
            total = inv.get("total") or "?"
            inv_date = inv.get("date")
            date_str = inv_date.strftime("%d/%m/%Y") if inv_date else "?"
            warnings = []
            if inv.get("vendor_confidence") != "signature":
                warnings.append("⚠️ vérifie le vendeur")
            if inv.get("date_confidence") not in ("order", "oldest"):
                warnings.append("⚠️ vérifie la date")
            warn_line = ("\n" + " · ".join(warnings)) if warnings else ""

            # Ask for confirmation
            state.awaiting_invoice_confirm = True
            state.pending_invoice = {
                "vendor": inv.get("vendor"),
                "total": inv.get("total"),
                "date": inv_date,
                "raw_text": text,
                "pdf_bytes": content,
                "pdf_filename": attachment.filename,
            }

            await message.reply(
                f"📄 **Facture détectée :**\n"
                f"Vendeur : **{vendor}**\n"
                f"Total TTC : **{total}€**\n"
                f"Date : **{date_str}**{warn_line}\n\n"
                f"Réponds `oui` pour confirmer, `non` pour annuler, "
                f"ou corrige avec : `Vendeur, total, DD/MM`"
            )
            break  # One attachment at a time for confirmation flow

    except Exception as e:
        await message.reply(f"❌ Erreur: {str(e)}")

    await bot.process_commands(message)


async def setup_commands():
    """Register all commands."""
    # Load sync command
    @bot.tree.command(name="sync", description="Sync timesheet entries from iCloud to Dropbox")
    async def sync_cmd(interaction: discord.Interaction):
        await sync.sync_command(interaction)

    # Load rapport command
    @bot.tree.command(name="rapport", description="Generate monthly Excel report")
    async def rapport_cmd(interaction: discord.Interaction):
        await rapport.rapport_command(interaction)

    # Load factures command
    @bot.tree.command(name="factures", description="Find invoices in Outlook")
    async def factures_cmd(interaction: discord.Interaction):
        await factures.factures_command(interaction)

    # Load status command
    @bot.tree.command(name="status", description="Show system status")
    async def status_cmd(interaction: discord.Interaction):
        await status.status_command(interaction)

    # Load fh command
    @bot.tree.command(name="fh", description="Remplir la feuille d'heures (aujourd'hui ou une date passée)")
    @discord.app_commands.describe(date="Date optionnelle au format DD/MM (ex: 19/05)")
    async def fh_cmd(interaction: discord.Interaction, date: str = None):
        await fh.fh_command(interaction, date)


async def main():
    """Start the bot."""
    await setup_commands()
    async with bot:
        await bot.start(DISCORD_BOT_TOKEN)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot stopped")
