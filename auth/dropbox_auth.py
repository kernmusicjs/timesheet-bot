#!/usr/bin/env python3
"""
One-time Dropbox OAuth2 Authorization Script
Obtient un refresh token pour l'API Dropbox
"""

import dropbox
from dropbox import DropboxOAuth2FlowNoRedirect

def main():
    print("=" * 60)
    print("Dropbox OAuth2 Authorization")
    print("=" * 60)

    # Demander les credentials
    app_key = input("\nApp key (from dropbox.com/developers/apps): ").strip()
    app_secret = input("App secret (from dropbox.com/developers/apps): ").strip()

    if not app_key or not app_secret:
        print("❌ Error: App key and App secret are required")
        return

    try:
        # Créer un flux OAuth2 sans redirect
        auth_flow = DropboxOAuth2FlowNoRedirect(app_key, app_secret, token_access_type='offline')

        # Générer l'URL d'autorisation
        auth_url = auth_flow.start()

        print("\n" + "=" * 60)
        print("1. Ouvrir ce lien dans ton browser:")
        print("=" * 60)
        print(auth_url)
        print("=" * 60)
        print("\n2. Clique sur 'Allow' pour donner accès au bot")
        print("3. Tu vas être redirigé vers une page avec un CODE")
        print("\n")

        # Demander le code d'autorisation
        auth_code = input("Colle le code (après 'code=' dans l'URL): ").strip()

        if not auth_code:
            print("❌ Error: Authorization code is required")
            return

        # Échanger le code pour un refresh token
        oauth_result = auth_flow.finish(auth_code)

        # Afficher le résultat
        print("\n" + "=" * 60)
        print("✓ SUCCESS!")
        print("=" * 60)
        print(f"\nDROPBOX_REFRESH_TOKEN=\"{oauth_result.refresh_token}\"")
        print("\n" + "=" * 60)
        print("Copie ce token dans ton fichier .env")
        print("=" * 60 + "\n")

    except Exception as e:
        print(f"❌ Error: {e}")
        return

if __name__ == "__main__":
    main()
