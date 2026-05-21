"""/resume — show summary of current month timesheet + invoices."""

import discord
from datetime import date


async def resume_command(interaction: discord.Interaction):
    await interaction.response.defer()
    from services.excel_updater import summarize_month
    from config import EXCEL_TIMESHEET_BASE_PATH
    msg = summarize_month(EXCEL_TIMESHEET_BASE_PATH, date.today())
    await interaction.followup.send(msg)
