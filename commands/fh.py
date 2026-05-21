"""
/fh command — manual timesheet entry for today, a past date, or a date range.
Usage: /fh             → prompt for today
       /fh 19/05       → prompt for May 19th
       /fh 18-20/05    → prompt for May 18-20 (3 days same content)
"""

import discord
from discord import app_commands
from datetime import date, timedelta
import re
import state


def _parse_date_or_range(s: str) -> list:
    """Return list of date(s). Supports 'DD/MM', 'DDDD', 'DD-DD/MM'."""
    s = s.strip()
    today = date.today()
    # Range: DD-DD/MM
    m = re.match(r'^(\d{1,2})\s*-\s*(\d{1,2})[/.\- ](\d{1,2})$', s)
    if m:
        d1, d2, mo = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if d1 > d2:
            d1, d2 = d2, d1
        return [date(today.year, mo, d) for d in range(d1, d2 + 1)]
    # Single: DD/MM
    m = re.match(r'^(\d{1,2})[/.\- ](\d{1,2})$', s)
    if m:
        return [date(today.year, int(m.group(2)), int(m.group(1)))]
    # Compact: DDDD
    m = re.match(r'^(\d{2})(\d{2})$', s)
    if m:
        return [date(today.year, int(m.group(2)), int(m.group(1)))]
    raise ValueError(f"Format invalide: {s!r}")


async def fh_command(interaction: discord.Interaction, date_str: str = None):
    await interaction.response.defer()

    if date_str:
        try:
            targets = _parse_date_or_range(date_str)
        except Exception:
            await interaction.followup.send(
                "❌ Format date invalide. Utilise `DD/MM`, `2005` ou plage `18-20/05`",
                ephemeral=True,
            )
            return
    else:
        targets = [date.today()]

    state.awaiting_timesheet = True
    state.pending_date = targets[0] if len(targets) == 1 else None
    state.pending_dates = targets if len(targets) > 1 else None

    day_names = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
    if len(targets) == 1:
        t = targets[0]
        day_label = f"{day_names[t.weekday()]} {t.day:02d}/{t.month:02d}"
    else:
        first, last = targets[0], targets[-1]
        day_label = f"{first.strftime('%d/%m')} → {last.strftime('%d/%m')} ({len(targets)} jours)"

    await interaction.followup.send(
        f"⏰ **Feuille d'heures — {day_label}** — Que as-tu fait ?\n"
        "Format: `Client, Affaire` ou `Client, Affaire, H.Sup` ou `Congé` / `Maladie` / `RTT`\n"
        "_(virgule, slash ou pipe acceptés — H. Normales auto: 8h lun–jeu, 7h ven)_"
    )
