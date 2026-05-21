# Obtenir les 9 Credentials — Guide Simple Copy-Paste

Tu dois obtenir **9 credentials** pour que le bot fonctionne. Aucun n'est difficile — c'est juste des clics et du copier-coller. Total: ~25 minutes.

## Avant de Commencer

- Ouvre une fenêtre de browser
- Prépare un éditeur texte (Notes, TextEdit, Bloc-notes, n'importe quoi)
- Copie tes credentials **dans ce fichier** à mesure que tu les obtiens (ne les perds pas!)

---

## Étape 1: Azure & Microsoft (10 min)

### 1.1 Obtenir AZURE_CLIENT_ID

1. Va sur: https://portal.azure.com
2. **Se connecter** avec ton compte Outlook/Microsoft (kernmusic.js@gmail.com ou autre)
3. Dans la barre de recherche en haut, tape: **"App registrations"** → appuie sur Enter
4. Clique sur le bouton bleu **"+ New registration"**
5. Remplis le formulaire:
   - **Name:** `timesheet-bot`
   - **Supported account types:** Clique sur **"Personal Microsoft accounts only"**
   - **Redirect URI:** Laisse vide
6. Clique sur le bouton **"Register"** (bleu)
7. Tu arrives sur la page de l'app. En haut tu vois **"Application (client) ID"**. C'est une longue chaîne genre `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`
8. **Copie-la** et sauvegarde-la: `AZURE_CLIENT_ID = ...`

### 1.2 Activer les "Public Client Flows"

1. Reste sur la même page (tu es sur l'app `timesheet-bot`)
2. Dans le menu de gauche, clique sur **"Authentication"**
3. Scroll down vers le bas jusqu'à **"Advanced settings"**
4. Trouve l'option **"Allow public client flows"** et passe-la à **"Yes"** (bascule bleue)
5. Clique sur le bouton **"Save"** en bas

### 1.3 Obtenir MICROSOFT_REFRESH_TOKEN

1. Ouvre Terminal sur ton Mac
2. Copie-colle ces commandes (une par une):

```bash
cd ~/timesheet-bot
source venv/bin/activate
python auth/ms_auth.py
```

3. Le script te demande: **"Enter your Azure Client ID:"**
   - Colle le `AZURE_CLIENT_ID` que tu viens de copier + appuie sur Enter

4. Le script affiche une URL et un **code** (8 caractères). Par exemple:
   ```
   Visit: https://microsoft.com/devicelogin
   Code: A1B2C3D4
   ```

5. **Dans un nouvel onglet du browser:**
   - Va sur: https://microsoft.com/devicelogin
   - Colle le code `A1B2C3D4` (exemple)
   - Clique **"Next"**
   - **Se connecte** avec ton compte Outlook (kernmusic.js@gmail.com)
   - Quand ça demande "Trying to sign in to Microsoft Azure CLI", clique **"Continue"**
   - Une page s'affiche: "You have signed in to the Microsoft Azure CLI application on your device"

6. **Retour dans Terminal:** Le script affiche:
   ```
   SUCCESS! Your refresh token is:
   0.AXXX...
   ```

7. **Copie ce token** (la longue chaîne qui commence par `0.A`): `MICROSOFT_REFRESH_TOKEN = 0.AXXX...`

---

## Étape 2: Dropbox (10 min)

### 2.1 Créer l'app Dropbox

1. Va sur: https://www.dropbox.com/developers/apps
2. **Se connecter** avec ton compte Dropbox (même compte que JEROME BRAIN)
3. Clique sur le bouton bleu **"Create app"**
4. Remplis le formulaire:
   - **API:** Clique sur **"Scoped access"**
   - **Type:** Clique sur **"Full Dropbox"**
   - **Name:** `jerome-timesheet-bot`
   - Clique **"Create app"**

### 2.2 Copier App Key & App Secret

1. Tu es sur la page des settings de ton app
2. Scroll un peu: tu vois **"App key"** et **"App secret"**
3. **Copie "App key"** (clique le bouton à côté): `DROPBOX_APP_KEY = ...`
4. **Copie "App secret"** (clique le bouton à côté): `DROPBOX_APP_SECRET = ...`

### 2.3 Configurer les permissions

1. Reste sur la même page
2. Clique sur l'onglet **"Permissions"** (en haut)
3. Scroll dans la liste et cherche ces permissions. Chaque permission a une checkbox. **Coche-les:**
   - `files.metadata.read`
   - `files.content.read`
   - `files.content.write`
   - `sharing.write`
4. En bas, clique sur le bouton **"Submit"** (bleu)

### 2.4 Obtenir DROPBOX_REFRESH_TOKEN

1. Ouvre Terminal sur ton Mac
2. Copie-colle cette commande:

```bash
cd ~/timesheet-bot && python auth/dropbox_auth.py
```

3. Le script demande: **"App key:"**
   - Colle le `DROPBOX_APP_KEY` que tu viens de copier + Enter

4. Le script demande: **"App secret:"**
   - Colle le `DROPBOX_APP_SECRET` que tu viens de copier + Enter

5. Le script affiche une URL. **Dans un nouvel onglet du browser:**
   - Copie-colle l'URL complète
   - Clique **"Allow"** (le bouton bleu)

6. Tu arrives sur une page qui dit "You've linked your app to Dropbox" ou similaire
7. **Dans l'URL en haut du browser**, il y a un code long genre `xxx`. Copie tout ce qui est après `code=`
   - Exemple: l'URL est `https://localhost/?code=A1B2C3D4...` → copie `A1B2C3D4...`

8. **Retour dans Terminal:** Le script demande: **"Paste the code here:"**
   - Colle le code → Enter

9. Le script affiche:
   ```
   DROPBOX_REFRESH_TOKEN=sl.Bxxxxxxxx...
   ```

10. **Copie ce token** (la longue chaîne qui commence par `sl.B`): `DROPBOX_REFRESH_TOKEN = sl.Bxxxxxxxx...`

---

## Étape 3: Discord (5 min)

### 3.1 Créer l'application Discord

1. Va sur: https://discord.com/developers/applications
2. **Se connecter** avec ton compte Discord
3. Clique sur le bouton bleu **"New Application"** (en haut à droite)
4. Rentre le nom: `Timesheet Bot` → clique **"Create"**

### 3.2 Obtenir DISCORD_BOT_TOKEN

1. Tu es sur la page de ton app
2. Dans le menu de gauche, clique sur **"Bot"**
3. Sous la section **"TOKEN"**, clique sur le bouton **"Reset Token"**
4. Une popup demande: "Are you sure?" → clique **"Yes, do it!"**
5. Une longue chaîne s'affiche (commence par `MTI...`)
6. Clique le bouton **"Copy"** pour la copier: `DISCORD_BOT_TOKEN = MTI...`

### 3.3 Activer les permissions importantes

1. Reste sur la page **"Bot"**
2. Scroll jusqu'à **"Privileged Gateway Intents"**
3. Active (bascule bleu) l'option: **"Message Content Intent"** (elle est importante pour lire les messages)
4. Clique **"Save Changes"** (en bas si nécessaire)

### 3.4 Inviter le bot sur ton serveur Discord

1. Dans le menu de gauche, clique sur **"OAuth2"** → puis **"URL Generator"**
2. Sous **"SCOPES"**, coche ces deux:
   - `bot`
   - `applications.commands`
3. Sous **"PERMISSIONS"**, coche:
   - `Send Messages`
   - `Read Message History`
   - `Use Slash Commands`
4. En bas tu vois une URL générée. **Copie-la complètement**
5. **Ouvre cette URL dans un nouvel onglet du browser**
6. Discord demande: "Select a server" → choisis ton serveur Discord personnel
7. Clique **"Continue"** puis **"Authorize"**
8. Voilà! Le bot `Timesheet Bot` est maintenant sur ton serveur

### 3.5 Obtenir DISCORD_GUILD_ID et DISCORD_CHANNEL_ID

Pour cette étape, tu as besoin d'activer le **"Développeur Mode"** dans Discord.

#### Activer le Développeur Mode:
1. Dans Discord (app ou web), en haut à gauche, clique sur la roue **"Paramètres utilisateur"** (ou User Settings)
2. Dans le menu de gauche, scroll jusqu'à **"Avancé"** (Advanced)
3. Active (bascule bleu): **"Mode développeur"**
4. Ferme les paramètres

#### Obtenir GUILD_ID:
1. Dans Discord, sur ton serveur, **fais un clic droit** sur le nom du serveur (en haut à gauche)
2. Tu vois un menu. Clique sur: **"Copier l'identifiant du serveur"** (ou "Copy Server ID")
3. C'est une chaîne de 18 chiffres. **Copie-la**: `DISCORD_GUILD_ID = 123456789012345678`

#### Obtenir CHANNEL_ID:
1. Dans Discord, sur ton serveur, **fais un clic droit** sur le nom du **channel** où tu veux que le bot envoie les messages (par exemple `#general`)
2. Clique sur: **"Copier l'identifiant du canal"** (ou "Copy Channel ID")
3. **Copie-la**: `DISCORD_CHANNEL_ID = 123456789012345678`

---

## Résumé: Tu as maintenant 9 credentials!

```
AZURE_CLIENT_ID = xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
AZURE_TENANT_ID = consumers
MICROSOFT_REFRESH_TOKEN = 0.AXXX...
DROPBOX_APP_KEY = xxxxxxxxxxxxxxx
DROPBOX_APP_SECRET = xxxxxxxxxxxxxxx
DROPBOX_REFRESH_TOKEN = sl.Bxxxxxxxx...
DISCORD_BOT_TOKEN = MTIxMj...
DISCORD_GUILD_ID = 123456789012345678
DISCORD_CHANNEL_ID = 123456789012345678
```

---

## Étape 4: Créer le fichier .env

1. Ouvre un éditeur de texte (TextEdit, VSCode, n'importe quoi)
2. Copie-colle ce template:

```
AZURE_CLIENT_ID="..."
AZURE_TENANT_ID="consumers"
MICROSOFT_REFRESH_TOKEN="..."
DROPBOX_APP_KEY="..."
DROPBOX_APP_SECRET="..."
DROPBOX_REFRESH_TOKEN="..."
DISCORD_BOT_TOKEN="..."
DISCORD_GUILD_ID="..."
DISCORD_CHANNEL_ID="..."
```

3. **Remplace chaque `...` par la vraie valeur** que tu as copiée
4. **Sauvegarde le fichier** comme: `~/.env`
   - Sur Mac: `~/.env` = `/Users/schneiderjerome/.env`
   - (Remplace `schneiderjerome` par ton username)

---

## Sécurité: NE JAMAIS

- Ne partage pas ton `.env` par email, Slack, ou documents
- Ne commite pas `.env` dans Git
- Ne dis pas tes credentials à quiconque
- Si tu penses avoir leaké une credential, va la révoquer sur le service (Azure, Dropbox, Discord) immédiatement

---

## Prochaine Étape

Une fois que tu as le `.env`, tu peux tester le bot localement:

```bash
cd ~/timesheet-bot
source venv/bin/activate
python main.py
```

Si tout marche, tu devrais voir:
```
✓ Bot logged in as Timesheet Bot#XXXX
✓ Commands synced
```

Puis tu peux tester les commandes Discord dans ton serveur:
- `/status` — doit afficher le nombre d'entrées en attente
- `/sync` — synchronise les entrées avec Dropbox
- `/rapport` — génère un fichier Excel
- `/factures` — cherche les factures dans Outlook

Bonne chance! 🚀
