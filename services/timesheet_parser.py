"""
Parser for timesheet Markdown files.
Converts between Markdown format and Python data structures.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
import re

class TimesheetEntry:
    """Represents a single timesheet entry."""
    def __init__(self, date: str, jj_mois: str, client: str, affaire: str, h_sup: float, remarques: str):
        self.date = date  # YYYY-MM-DD
        self.jj_mois = jj_mois  # DD/MM
        self.client = client
        self.affaire = affaire
        self.h_sup = float(h_sup) if h_sup else 0
        self.remarques = remarques
        self.h_normales = self._calculate_h_normales()

    def _calculate_h_normales(self) -> float:
        """Calculate normal hours based on day of week."""
        try:
            date_obj = datetime.strptime(self.date, "%Y-%m-%d")
            weekday = date_obj.weekday()  # 0=Mon, 4=Fri

            # If client is "—" and affaire is an absence type, return 0
            if self.client == "—":
                return 0.0

            # Mon-Thu = 8h, Fri = 7h
            return 8.0 if weekday < 4 else 7.0
        except:
            return 0.0

    def to_markdown_row(self) -> str:
        """Convert entry to Markdown table row."""
        return f"| {self.date} | {self.jj_mois} | {self.client} | {self.affaire} | {self.h_normales} | {self.h_sup} | {self.remarques} |"

    def __repr__(self):
        return f"TimesheetEntry({self.date}, {self.client}, {self.affaire}, {self.h_normales}h, {self.h_sup}h sup)"


def parse_timesheet_entries(markdown_content: str) -> List[TimesheetEntry]:
    """
    Parse timesheet entries from Markdown format.
    Format: YYYY-MM-DD | JJ-mois | Client | Affaire/Dossier | H.Sup | Remarques
    """
    entries = []
    lines = markdown_content.strip().split('\n')

    for line in lines:
        # Skip header lines and empty lines
        if not line.strip() or '---' in line or 'Format:' in line or 'Absence:' in line:
            continue

        # Parse pipe-separated format
        parts = [p.strip() for p in line.split('|')]
        if len(parts) < 6:
            continue

        try:
            date = parts[0]
            jj_mois = parts[1]
            client = parts[2]
            affaire = parts[3]
            h_sup = parts[4]
            remarques = parts[5] if len(parts) > 5 else ""

            # Validate date format
            if not re.match(r'\d{4}-\d{2}-\d{2}', date):
                continue

            entry = TimesheetEntry(date, jj_mois, client, affaire, h_sup, remarques)
            entries.append(entry)
        except Exception as e:
            print(f"Error parsing line: {line} - {e}")
            continue

    return entries


def create_timesheet_markdown(entries: List[TimesheetEntry], year: int, month: int) -> str:
    """
    Create a Markdown timesheet file from entries.
    """
    month_name = datetime(year, month, 1).strftime("%B")

    header = f"""# Timesheet {month_name} {year} — Cadindus

| Date | JJ-mois | Client | Affaires/Dossier | H. Normales | H. Sup | Remarques |
|------|---------|--------|-----------------|-------------|--------|-----------|
"""

    rows = [entry.to_markdown_row() for entry in entries]
    body = "\n".join(rows)

    footer = "\n\n---\n*Lun-Jeu = 8h / Ven = 7h / Week-end = 0*"

    return header + body + footer


def merge_entries_into_timesheet(existing_timesheet: str, new_entries: List[TimesheetEntry]) -> str:
    """
    Merge new entries into an existing timesheet, avoiding duplicates.
    """
    # Parse existing timesheet
    existing_entries = parse_timesheet_entries(existing_timesheet)

    # Create a set of existing dates for quick lookup
    existing_dates = {e.date for e in existing_entries}

    # Add only new entries (not already present)
    for entry in new_entries:
        if entry.date not in existing_dates:
            existing_entries.append(entry)

    # Sort by date
    existing_entries.sort(key=lambda e: e.date)

    # Reconstruct timesheet
    month = existing_entries[0].date.split('-')[1] if existing_entries else "01"
    year = existing_entries[0].date.split('-')[0] if existing_entries else "2026"

    return create_timesheet_markdown(existing_entries, int(year), int(month))


def archive_entries(archive_content: str, entries: List[TimesheetEntry]) -> str:
    """
    Archive processed entries.
    """
    lines = archive_content.strip().split('\n')

    # Keep header and existing entries
    header_lines = [l for l in lines if not re.match(r'\d{4}-\d{2}-\d{2}', l)]

    # Add new entries as rows
    new_rows = []
    for entry in entries:
        row = f"{entry.date} | {entry.jj_mois} | {entry.client} | {entry.affaire} | {entry.h_sup} | {entry.remarques}"
        new_rows.append(row)

    return "\n".join(header_lines) + "\n" + "\n".join(new_rows)
