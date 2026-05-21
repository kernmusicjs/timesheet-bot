# Prochaines Étapes

## Phase 1: Setup Local (30 min)

```bash
cd ~/timesheet-bot
chmod +x setup.sh
./setup.sh
source venv/bin/activate
```

Ensuite: Remplir `.env` avec les 9 credentials (voir SETUP.md pour les détails).

---

## Phase 2: Authentification Microsoft (15 min)

One-time setup pour obtenir le Microsoft refresh token:

```bash
python auth/ms_auth.py
```

Suivre les instructions:
1. Go to `https://microsoft.com/devicelogin`
2. Enter the code affiché
3. Login avec ton compte Outlook
4. Copier le token affiché → ajouter à `.env`

---

## Phase 3: Test Local Bot (30 min)

```bash
python main.py
```

Expected output:
```
✓ Bot logged in as Timesheet Bot#XXXX
✓ Commands synced
✓ Scheduler started
```

Sur Discord, test chaque commande:

1. **`/status`** — devrait afficher l'état
2. **`/factures`** — envoyer un email "facture" d'abord
3. **`/sync`** — ajouter une entrée test dans `timesheet_entries.md`
4. **`/rapport`** — générer un rapport et vérifier Excel dans Dropbox

---

## Phase 4: Deploy sur Railway (30 min)

```bash
npm install -g @railway/cli
railway login
cd ~/timesheet-bot
railway init
# Follow prompts
```

Push vers GitHub:

```bash
git init
git add .
git commit -m "Initial: timesheet bot"
git remote add origin https://github.com/yourusername/timesheet-bot.git
git push -u origin main
railway link
```

Set environment variables:

```bash
railway variables set \
  AZURE_CLIENT_ID="..." \
  AZURE_TENANT_ID="consumers" \
  MICROSOFT_REFRESH_TOKEN="..." \
  DROPBOX_APP_KEY="..." \
  DROPBOX_APP_SECRET="..." \
  DROPBOX_REFRESH_TOKEN="..." \
  DISCORD_BOT_TOKEN="..." \
  DISCORD_GUILD_ID="..." \
  DISCORD_CHANNEL_ID="..."
```

Deploy:

```bash
railway deploy
railway logs  # Verify it's running
```

---

## Phase 5: Integration (Optional)

Once everything works locally:

1. **Move iCloud file to Dropbox** — Configure Remotely Save to sync `timesheet_entries.md`
2. **Add to calendar** — Get monthly summary notification automatically
3. **Extend Excel format** — Add project codes, cost tracking, etc.
4. **Webhook monitoring** — Alert on sync failures

---

## Credentials Checklist

Before starting, you'll need accounts + tokens for:

- [ ] Microsoft Azure account (free)
- [ ] Dropbox account (have one)
- [ ] Discord server + bot created
- [ ] GitHub account (for Railway integration)
- [ ] Railway account (sign up at railway.app)

See SETUP.md for step-by-step instructions on each.

---

## Estimated Timeline

- Phase 1 (Local setup): 30 min
- Phase 2 (Microsoft auth): 15 min
- Phase 3 (Bot testing): 30 min
- Phase 4 (Railway deploy): 30 min

**Total: ~2 hours** (first time)

Subsequent deploys: 5-10 min

---

## Quick Reference

| Command | What it does |
|---------|------------|
| `./setup.sh` | Setup Python venv + install deps |
| `python auth/ms_auth.py` | Get Microsoft refresh token (one-time) |
| `python main.py` | Run bot locally |
| `railway deploy` | Deploy to Railway |
| `railway logs` | Watch live logs |
| `railway variables` | View environment variables |

---

## Help

- **SETUP.md** — Detailed setup instructions
- **README.md** — Architecture + usage
- **Plan file** — Technical design
- Discord command help: Type `/status` then look at bot response

---

**Status:** Code complete. Ready to start Phase 1.
