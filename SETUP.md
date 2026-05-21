# Setup Guide — Timesheet Bot

## Phase 1: Local Setup

### 1.1 Cloner et installer

```bash
cd ~/timesheet-bot
chmod +x setup.sh
./setup.sh
source venv/bin/activate
```

### 1.2 Créer les credentials (6 services)

#### A) Microsoft Graph API (Outlook)

Aller sur [portal.azure.com](https://portal.azure.com):

1. Login avec ton compte Microsoft
2. Azure Active Directory → App registrations → New registration
3. Name: `Timesheet Bot`
4. Supported account types: `Accounts in any organizational directory and personal Microsoft accounts`
5. Register
6. Copy **Application (client) ID** → mets de côté
7. API permissions → Add a permission → Microsoft Graph → Delegated permissions
8. Search: `Mail.Read`
9. Tick `Mail.Read` → Add permissions
10. Grant admin consent (si tu peux)

**Résultat:**
- `AZURE_CLIENT_ID` = l'Application (client) ID

Maintenant, obtenir le refresh token:

```bash
python auth/ms_auth.py
```

Tu vas être redirigé vers une page pour te connecter à Microsoft. C'est normal. Copie le code affiché et rentre-le sur ta phone/autre appareil. Après, le script affichera le `MICROSOFT_REFRESH_TOKEN`.

#### B) Dropbox

Aller sur [dropbox.com/developers/apps](https://dropbox.com/developers/apps):

1. Create app
2. Scoped app → Full Dropbox
3. Name: `timesheet-bot`
4. Create app
5. Permissions tab:
   - Check `files.content.read`
   - Check `files.content.write`
6. Settings tab:
   - Copy **App key** → `DROPBOX_APP_KEY`
   - Copy **App secret** → `DROPBOX_APP_SECRET`
7. OAuth 2 / Refresh tokens section → Generate → copy `DROPBOX_REFRESH_TOKEN`

#### C) Discord Bot

Aller sur [discord.com/developers/applications](https://discord.com/developers/applications):

1. New Application → Name: `Timesheet Bot` → Create
2. Bot section → Add Bot
3. Copy **TOKEN** → `DISCORD_BOT_TOKEN`
4. OAuth2 → URL Generator
5. Scopes: check `bot`
6. Permissions:
   - General → Server Members
   - Text Permissions → Send Messages, Read Message History
   - Integration → Use Slash Commands
7. Copy the generated URL → ouvrir dans le navigateur → authorize bot sur ton serveur

**Pour les IDs:**
- Server: Right-click ton serveur → Copy Server ID → `DISCORD_GUILD_ID`
- Channel: Right-click le channel où le bot va envoyer les messages → Copy Channel ID → `DISCORD_CHANNEL_ID`

### 1.3 Remplir `.env`

```bash
# Copy template
cp .env.example .env

# Edit
nano .env  # ou ton éditeur préféré
```

Remplir les 10 variables:

```
AZURE_CLIENT_ID=<from step A>
AZURE_TENANT_ID=consumers
MICROSOFT_REFRESH_TOKEN=<from step A>
DROPBOX_APP_KEY=<from step B>
DROPBOX_APP_SECRET=<from step B>
DROPBOX_REFRESH_TOKEN=<from step B>
DISCORD_BOT_TOKEN=<from step C>
DISCORD_GUILD_ID=<from step C>
DISCORD_CHANNEL_ID=<from step C>
```

### 1.4 Test local

```bash
source venv/bin/activate
python main.py
```

Expected output:
```
✓ Bot logged in as Timesheet Bot#XXXX
✓ Commands synced
✓ Scheduler started
```

Sur Discord, essayer:
```
/status
```

Le bot devrait répondre avec l'état du système.

### 1.5 Test chaque commande

**Test `/sync`:**
1. Ajouter une entrée test dans `~/Library/Mobile Documents/com~apple~CloudDocs/timesheet_entries.md`
2. Lancer `/sync` sur Discord
3. Vérifier que `timesheet_mai_2026.md` est mis à jour dans Dropbox

**Test `/factures`:**
1. Envoyer un email à toi-même avec "facture" dans le sujet + un PDF joint
2. Lancer `/factures` sur Discord
3. Vérifier que l'email est détecté

**Test `/rapport`:**
1. Lancer `/rapport` sur Discord
2. Vérifier que le fichier Excel est uploadé dans Dropbox
3. Télécharger et ouvrir le fichier pour vérifier le format

---

## Phase 2: Railway Deployment

### 2.1 Installer Railway CLI

```bash
npm install -g @railway/cli
railway login
```

### 2.2 Initialiser Railway

```bash
cd ~/timesheet-bot
railway init
```

Suivre les prompts:
- Project name: `timesheet-bot`
- Template: skip (we have code)
- Create environment: `production`

### 2.3 Git setup

```bash
git init
git add .
git commit -m "Initial commit: timesheet bot with Discord + Outlook + Dropbox"
git remote add origin https://github.com/yourusername/timesheet-bot.git
git push -u origin main
```

### 2.4 Link to Railway

```bash
railway link
```

Sélectionner le projet `timesheet-bot`.

### 2.5 Ajouter variables d'environnement

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

Ou via l'UI: [railway.app](https://railway.app) → Project → Variables → Add

### 2.6 Deploy

```bash
railway deploy
```

Vérifier le déploiement:
```bash
railway logs
```

Expected:
```
✓ Bot logged in as Timesheet Bot#XXXX
✓ Commands synced
✓ Scheduler started
```

Le bot devrait être online dans Discord (avec le statut "Online").

### 2.7 Test en production

Sur Discord (pour confirmer que c'est la version cloud):
```
/status
```

Le bot devrait répondre.

---

## Troubleshooting

### Erreur: `module not found: msal`
```bash
pip install msal
```

### Erreur: `DISCORD_BOT_TOKEN not found`
Vérifier que `.env` est rempli et que le bot a les bonnes permissions sur Discord.

### Erreur: Microsoft Graph API 401
Le refresh token a expiré ou est invalide. Relancer `python auth/ms_auth.py` pour obtenir un nouveau token.

### Erreur: Dropbox `ApiError`
Vérifier que le refresh token est valide. Relancer l'auth Dropbox si nécessaire.

### Bot n'est pas online sur Discord
- Vérifier les logs: `railway logs`
- Vérifier les variables d'environnement: `railway variables`
- Relancer: `railway redeploy`

---

## Notes Importantes

1. **iCloud + Dropbox** — Le fichier `timesheet_entries.md` est dans iCloud, mais Remotely Save le synchronise dans Dropbox. Le bot lit le fichier local sur ta machine pour les tests; en production, tu devras configurer Remotely Save.

2. **Token expiration** — Les refresh tokens Microsoft expirent après 90 jours d'inactivité. Si ça arrive, relancer `python auth/ms_auth.py`.

3. **Scheduled tasks** — Le cron s'exécute le 1er du mois à 07:00 (heure serveur, UTC sur Railway).

4. **Coûts** — Railway gratuit pour les premiers $5/mois. Pour ce bot, compte ~$2-3/mois.

5. **Sauvegardes** — Garde les credentials dans un endroit sûr (1Password, Bitwarden, etc.). Ne pas les committer sur GitHub.

---

## Prochaines étapes

1. ✅ Setup local
2. ✅ Test chaque commande
3. ✅ Deploy sur Railway
4. → Tester le cron mensuel (attendre le 1er du mois ou simuler)
5. → Ajouter plus de détails au rapport Excel si besoin
6. → Intégrer avec ton workflow actuel (Cadindus, etc.)

---

**Questions?** Ouvre une issue sur GitHub ou contacte Jerome.
