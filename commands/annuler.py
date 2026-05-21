"""/annuler — clear a timesheet row for a given date (default today)."""

import discord
from datetime import date
import re


def _parse_date_str(s: str) -> tuple:
    s = s.strip().lower()
    if s in ("hier", "yesterday"):
        from datetime import timedelta
        d = date.today() - timedelta(days=1)
        return d.day, d.month
    m = re.match(r'^(\d{1,2})[/.\- ](\d{1,2})$', s)
    if m:
        return int(m.group(1)), int(m.group(2))
    m = re.match(r'^(\d{2})(\d{2})$', s)
    if m:
        return int(m.group(1)), int(m.group(2))
    raise ValueError(f"Format invalide: {s!r}")


async def annuler_command(interaction: discord.Interaction, date_str: str = None):
    await interaction.response.defer()
    from services.excel_updater import clear_row
    from config import EXCEL_TIMESHEET_BASE_PATH

    if date_str:
        try:
            day, month = _parse_date_str(date_str)
            target = date(date.today().year, month, day)
        except Exception:
            await interaction.followup.send("❌ Format date invalide. Utilise `DD/MM`, `hier`, ou `21`", ephemeral=True)
            return
    else:
        target = date.today()

    result = clear_row(EXCEL_TIMESHEET_BASE_PATH, target)
    await interaction.followup.send(result)
