"""/modifier — re-prompt timesheet entry for a given date (clears then re-asks)."""

import discord
from datetime import date
import re
import state


def _parse_date_str(s: str) -> tuple:
    s = s.strip().lower()
    if s in ("hier", "yesterday"):
        from datetime import timedelta
        d = date.today() - timedelta(days=1)
        return d.day, d.month
    m = re.match(r'^(\d{1,2})[/.\- ](\d{1,2})$', s)
    if m:
        return int(m.group(1)), int(m.group(2))
    raise ValueError(f"Format invalide: {s!r}")


async def modifier_command(interaction: discord.Interaction, date_str: str = None):
    await interaction.response.defer()
    if date_str:
        try:
            day, month = _parse_date_str(date_str)
            target = date(date.today().year, month, day)
        except Exception:
            await interaction.followup.send("❌ Format date invalide. Utilise `DD/MM` ou `hier`", ephemeral=True)
            return
    else:
        target = date.today()

    state.awaiting_timesheet = True
    state.pending_date = target

    day_names = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
    day_label = f"{day_names[target.weekday()]} {target.day:02d}/{target.month:02d}"
    await interaction.followup.send(
        f"✏️ **Modifier {day_label}** — Nouveau contenu ? (l'ancien sera écrasé)\n"
        "Format: `Client, Affaire` ou `Client, Affaire, H.Sup` ou `Congé` / `Maladie` / `RTT`"
    )
