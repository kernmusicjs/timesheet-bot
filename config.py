import os
from dotenv import load_dotenv

load_dotenv()

# Azure / Microsoft Graph
AZURE_CLIENT_ID = os.getenv("AZURE_CLIENT_ID")
AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID", "common")
MICROSOFT_REFRESH_TOKEN = os.getenv("MICROSOFT_REFRESH_TOKEN")

# Dropbox
DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")

# Discord
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DISCORD_GUILD_ID = int(os.getenv("DISCORD_GUILD_ID", "0"))
DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", "0"))

# File paths
TIMESHEET_ENTRIES_PATH = os.path.expanduser("~/Library/Mobile Documents/com~apple~CloudDocs/timesheet_entries.md")
TIMESHEET_ENTRIES_DONE_PATH = os.path.expanduser("~/Library/Mobile Documents/com~apple~CloudDocs/timesheet_entries_done.md")
DROPBOX_VAULT_PATH = os.getenv("DROPBOX_VAULT_PATH", "/JEROME BRAIN/WORK")

# Local Excel timesheet base path (Dropbox syncs automatically on Mac; override on VPS)
EXCEL_TIMESHEET_BASE_PATH = os.getenv(
    "EXCEL_TIMESHEET_BASE_PATH",
    os.path.expanduser("~/Library/CloudStorage/Dropbox/Applications/remotely-save/JEROME BRAIN/WORK")
)
