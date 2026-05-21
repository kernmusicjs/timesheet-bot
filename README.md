# Timesheet Bot — Automatisation Mensuelle

Système cloud pour synchroniser les entrées de feuille d'heures, extraire les factures depuis Outlook, générer des rapports Excel mensels, et piloter le tout via Discord.

## Architecture

- **Bot Discord** — slash commands (`/sync`, `/rapport`, `/factures`, `/status`)
- **Microsoft Graph API** — lecture des emails Outlook + PDFs
- **Dropbox API** — stockage des fichiers (timesheet, rapports)
- **APScheduler** — cron mensuel (1er du mois, 07:00)
- **Railway** — hébergement cloud (bot persistant)

## Setup local

### 1. Cloner et installer dépendances

```bash
cd ~/timesheet-bot
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Créer les credentials

#### Microsoft Graph (Outlook)

Aller sur [portal.azure.com](https://portal.azure.com):
1. App registrations → New registration
2. Name: `Timesheet Bot`
3. Supported account types: `Accounts in any organizational directory and personal Microsoft accounts`
4. Redirect URI: leave empty (public client)
5. API permissions: `Mail.Read` (delegated)
6. Copy `Application (client) ID` → `AZURE_CLIENT_ID`

Ensuite, lancer le script d'authentification:

```bash
python auth/ms_auth.py
```

Suivre les instructions pour obtenir le `MICROSOFT_REFRESH_TOKEN`.

#### Dropbox

[dropbox.com/developers/apps](https://dropbox.com/developers/apps):
1. Create app → Scoped app
2. Type: Full Dropbox
3. Permissions: `files.content.read`, `files.content.write`
4. Generate token
5. Copy `DROPBOX_APP_KEY`, `DROPBOX_APP_SECRET`, `DROPBOX_REFRESH_TOKEN`

#### Discord

[discord.com/developers/applications](https://discord.com/developers/applications):
1. New Application → name `Timesheet Bot`
2. Bot → Add Bot
3. Copy `TOKEN` → `DISCORD_BOT_TOKEN`
4. OAuth2 → URL Generator
5. Scopes: `bot`
6. Permissions: `Send Messages`, `Use Slash Commands`, `Read Message History`
7. Copy the generated URL, ouvrir dans le navigateur et autoriser sur ton serveur

Pour obtenir les IDs:
- `DISCORD_GUILD_ID` : Right-click on your server → Copy Server ID
- `DISCORD_CHANNEL_ID` : Right-click on the channel → Copy Channel ID

### 3. Créer `.env`

```bash
cp .env.example .env
# Remplir avec les credentials
```

### 4. Test local

```bash
source venv/bin/activate
python main.py
```

Le bot devrait être en ligne. Aller sur Discord et taper `/status` pour confirmer.

## Commandes Discord

| Commande | Action |
|----------|--------|
| `/sync` | Lire `timesheet_entries.md`, mettre à jour le timesheet du mois, archiver les entrées |
| `/rapport` | Générer Excel (timesheet + factures), upload Dropbox, envoyer le lien |
| `/factures` | Scanne Outlook, liste les factures du mois |
| `/status` | Affiche l'état du système |

## Déploiement Railway

### 1. Setup Railway

```bash
npm install -g @railway/cli
railway login
cd ~/timesheet-bot
railway init
```

### 2. Connecter à GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/yourusername/timesheet-bot.git
git push -u origin main

railway link
```

### 3. Ajouter variables d'environnement

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

### 4. Deploy

```bash
railway deploy
railway up
```

Vérifier : `railway logs`

## Troubleshooting

### Bot ne répond pas
- Vérifier que le bot est en ligne : `railway logs`
- Vérifier les permissions Discord (slash commands activés)
- Vérifier que les variables d'environnement sont présentes : `railway variables`

### Microsoft Graph API échoue
- Vérifier le refresh token (valide 90 jours)
- Relancer `python auth/ms_auth.py` pour obtenir un nouveau token
- Mettre à jour `MICROSOFT_REFRESH_TOKEN` dans Railway

### Dropbox échoue
- Vérifier que le app key/secret est correct
- Vérifier que le refresh token n'a pas expiré
- Vérifier que le chemin `/JEROME BRAIN/WORK/` existe dans Dropbox

## Structure des fichiers

```
timesheet-bot/
├── main.py              # Bot Discord entry point
├── scheduler.py         # Cron jobs
├── config.py            # Variables d'environnement
├── requirements.txt     # Dépendances Python
├── Procfile            # Config Railway
├── .env.example        # Template variables d'environnement
├── .gitignore          # Ignorer .env
├── auth/
│   └── ms_auth.py      # Script one-shot Microsoft OAuth
├── services/
│   ├── graph_api.py    # Microsoft Graph API client
│   ├── dropbox_client.py
│   ├── timesheet_parser.py
│   └── excel_builder.py
└── commands/
    ├── sync.py
    ├── rapport.py
    ├── factures.py
    └── status.py
```

## Notes

- **iCloud sans API** — `timesheet_entries.md` doit être synchronisé dans Dropbox via Remotely Save
- **Token refresh** — Le bot renouvelle automatiquement les access tokens à chaque run
- **Cron mensuel** — S'exécute le 1er du mois à 07:00 (heure serveur Railway/UTC)
- **Quota Outlook** — Microsoft Graph API gratuite (sans limite pour lecture)
- **Quota Dropbox** — Plan gratuit 2 GB (suffisant pour quelques rapports Excel par an)

## License

Internal tool — Copyright Jérôme Schneider / KERN Productions
