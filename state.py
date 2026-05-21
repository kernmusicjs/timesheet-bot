"""Shared mutable state for the bot."""

awaiting_timesheet = False
pending_date = None

# Invoice confirmation state
awaiting_invoice_confirm = False
pending_invoice = None  # dict: {vendor, total, date}
