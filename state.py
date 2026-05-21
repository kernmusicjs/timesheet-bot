"""Shared mutable state for the bot."""

awaiting_timesheet = False
pending_date = None
pending_dates = None  # list[date] for multi-day /fh ranges

# Invoice confirmation state
awaiting_invoice_confirm = False
pending_invoice = None  # dict: {vendor, total, date}
