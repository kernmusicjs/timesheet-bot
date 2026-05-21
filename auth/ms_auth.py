"""
One-time Microsoft Graph authentication script.
Run this once to obtain and store the refresh token.
"""

import msal
import json
import sys
from pathlib import Path

# These values need to be created in Azure portal (portal.azure.com)
# Create an App Registration, type "Public Client", permissions: Mail.Read
AZURE_CLIENT_ID = input("Enter your AZURE_CLIENT_ID from Azure portal: ").strip()
AZURE_TENANT_ID = "common"  # For both personal and work/school accounts

def get_refresh_token(client_id):
    """Obtain a refresh token via Device Code flow."""
    app = msal.PublicClientApplication(client_id, authority=f"https://login.microsoftonline.com/{AZURE_TENANT_ID}")

    # Device code flow for ease of use
    flow = app.initiate_device_flow(scopes=["Mail.Read"])

    # Check for errors in the flow response
    if "error" in flow:
        print(f"❌ Authentication failed: {flow.get('error_description', flow['error'])}")
        sys.exit(1)

    print("\n" + "="*60)
    print("Device Code Flow Instructions:")
    print("="*60)
    print(f"\n1. Go to: {flow['verification_uri']}")
    print(f"2. Enter this code: {flow['user_code']}")
    print("\nWaiting for authentication...\n")

    result = app.acquire_token_by_device_flow(flow)

    if "refresh_token" in result:
        print("✓ Authentication successful!")
        return result["refresh_token"]
    else:
        print(f"✗ Authentication failed: {result.get('error_description', 'Unknown error')}")
        sys.exit(1)

if __name__ == "__main__":
    refresh_token = get_refresh_token(AZURE_CLIENT_ID)

    print(f"\nAZURE_CLIENT_ID: {AZURE_CLIENT_ID}")
    print(f"AZURE_TENANT_ID: {AZURE_TENANT_ID}")
    print(f"MICROSOFT_REFRESH_TOKEN: {refresh_token[:20]}...")

    print("\n" + "="*60)
    print("Add these to your .env file or Railway environment variables:")
    print("="*60)
    print(f"AZURE_CLIENT_ID={AZURE_CLIENT_ID}")
    print(f"AZURE_TENANT_ID={AZURE_TENANT_ID}")
    print(f"MICROSOFT_REFRESH_TOKEN={refresh_token}")
