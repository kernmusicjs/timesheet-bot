# Prochaines Étapes — Setup Local du Bot Timesheet

## ✓ Complété (Étape 0)

- [x] Fichier de référence credentials créé: `JEROME BRAIN/WORK/wiki/operations/api-credentials.md`
- [x] Guide complet créé: `OBTENIR_CREDENTIALS.md` dans ce dossier
- [x] Script Dropbox OAuth créé: `auth/dropbox_auth.py`

---

## 📋 À Faire Maintenant (Étape 1: Obtenir les 9 Credentials)

**Durée estimée:** 25-30 minutes

### Étapes:

1. **Lis le guide:** `~/timesheet-bot/OBTENIR_CREDENTIALS.md`
   - Suis chaque étape dans l'ordre (Azure → Dropbox → Discord)
   - Copie-colle les credentials au fur et à mesure

2. **Exécute les scripts en Terminal:**
   ```bash
   cd ~/timesheet-bot
   source venv/bin/activate
   
   # Microsoft OAuth
   python auth/ms_auth.py
   
   # Dropbox OAuth
   python auth/dropbox_auth.py
   ```

3. **Crée le fichier `~/.env`:**
   - Copie le template du guide
   - Remplis les 9 credentials
   - Sauvegarde en: `~/.env` (dans ton home directory)

---

## 🤖 Ensuite: Test Local (Étape 2)

Une fois que tu as le `~/.env`:

```bash
cd ~/timesheet-bot
source venv/bin/activate
python main.py
```

Tu devrais voir:
```
✓ Bot logged in as Timesheet Bot#XXXX
✓ Commands synced
```

Dans Discord, teste:
- `/status` — affiche le nombre d'entrées en attente
- `/sync` — synchronise les entrées avec Dropbox
- `/rapport` — génère un Excel
- `/factures` — cherche les factures dans Outlook

---

## 🎯 Après le Test Local

Si tout marche localement:
- On adapte le code pour Hetzner
- On crée un compte Hetzner
- On déploie le bot sur le VPS

**IMPORTANT:** Pas de dépense Hetzner avant que le test local soit ✓ validé!

---

## 📝 Notes

- Tu as besoin d'un **compte Discord personnel** (création rapide si tu n'en as pas)
- Tu as besoin d'un **compte Dropbox** avec JEROME BRAIN vault
- Tu as besoin d'un **compte Outlook** (kernmusic.js@gmail.com)
- Tous les scripts demandent juste du copier-coller — rien de compliqué

---

**Prêt?** Ouvre `OBTENIR_CREDENTIALS.md` et commence! 🚀
