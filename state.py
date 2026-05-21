"""Shared mutable state for the bot."""

awaiting_timesheet = False
pending_date = None
pending_dates = None  # list[date] for multi-day /fh ranges

# Invoice confirmation state
awaiting_invoice_confirm = False
pending_invoice = None  # dict: {vendor, total, date}

# H.Sup yesterday follow-up (triggered after auto 16h prompt)
awaiting_hsup_yesterday = False
hsup_yesterday_date = None  # date object: the previous workday
auto_prompt = False  # True when prompt came from scheduler (not /fh)
