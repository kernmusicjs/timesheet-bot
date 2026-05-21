"""
/fh command — manual timesheet entry for today or a past date.
Usage: /fh          → prompt for today
       /fh 19/05    → prompt for May 19th
"""

import discord
from discord import app_commands
from datetime import date
import re
import state


def _parse_date_str(s: str) -> tuple:
    s = s.strip()
    m = re.match(r'^(\d{1,2})[/.\- ](\d{1,2})$', s)
    if m:
        return int(m.group(1)), int(m.group(2))
    m = re.match(r'^(\d{2})(\d{2})$', s)
    if m:
        return int(m.group(1)), int(m.group(2))
    raise ValueError(f"Format invalide: {s!r}")


async def fh_command(interaction: discord.Interaction, date_str: str = None):
    await interaction.response.defer()

    if date_str:
        try:
            day, month = _parse_date_str(date_str)
            target = date(date.today().year, month, day)
        except Exception:
            await interaction.followup.send("❌ Format date invalide. Utilise `DD/MM`, `2005` ou `20 05`", ephemeral=True)
            return
    else:
        target = date.today()

    state.awaiting_timesheet = True
    state.pending_date = target

    day_names = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
    day_label = f"{day_names[target.weekday()]} {target.day:02d}/{target.month:02d}"

    await interaction.followup.send(
        f"⏰ **Feuille d'heures — {day_label}** — Que as-tu fait ?\n"
        "Format: `Client, Affaire` ou `Client, Affaire, H.Sup` ou `Congé` / `Maladie` / `RTT`\n"
        "_(virgule, slash ou pipe acceptés — H. Normales auto: 8h lun–jeu, 7h ven)_"
    )
