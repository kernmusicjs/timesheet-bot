"""
Microsoft Graph API client for reading Outlook emails and downloading PDF attachments.
"""

import requests
import msal
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
from config import AZURE_CLIENT_ID, AZURE_TENANT_ID, MICROSOFT_REFRESH_TOKEN

class GraphAPIClient:
    def __init__(self, refresh_token: str):
        self.client_id = AZURE_CLIENT_ID
        self.tenant_id = AZURE_TENANT_ID
        self.refresh_token = refresh_token
        self.access_token = None
        self.refresh_access_token()

    def refresh_access_token(self):
        """Refresh the access token using the refresh token."""
        app = msal.PublicClientApplication(
            self.client_id,
            authority=f"https://login.microsoftonline.com/{self.tenant_id}"
        )

        result = app.acquire_token_by_refresh_token(
            self.refresh_token,
            scopes=["Mail.Read"]
        )

        if "access_token" in result:
            self.access_token = result["access_token"]
            # Update refresh token for next time (can be reissued)
            if "refresh_token" in result:
                self.refresh_token = result["refresh_token"]
        else:
            raise Exception(f"Failed to refresh token: {result.get('error_description')}")

    def get_emails_by_date_and_keyword(self, year: int, month: int, keywords: List[str]) -> List[Dict]:
        """
        Get emails from a specific month containing any of the keywords in subject.
        Returns list of emails with: id, subject, from, receivedDateTime, attachments.
        """
        # Build date filter: all emails in the given month
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)

        filter_query = f"receivedDateTime ge {start_date.isoformat()}Z and receivedDateTime lt {end_date.isoformat()}Z"

        headers = {"Authorization": f"Bearer {self.access_token}"}
        url = "https://graph.microsoft.com/v1.0/me/mailFolders/inbox/messages"
        params = {
            "$filter": filter_query,
            "$select": "id,subject,from,receivedDateTime,hasAttachments",
            "$top": 999  # Get up to 999 emails
        }

        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            print(f"Error fetching emails: {response.status_code} - {response.text}")
            return []

        emails = response.json().get("value", [])

        # Filter by keywords in subject (case-insensitive)
        keywords_lower = [k.lower() for k in keywords]
        filtered_emails = []
        for email in emails:
            subject_lower = email.get("subject", "").lower()
            if any(kw in subject_lower for kw in keywords_lower):
                filtered_emails.append(email)

        return filtered_emails

    def get_attachments(self, message_id: str) -> List[Dict]:
        """
        Get all attachments from a specific message.
        Returns list of attachments with: id, name, contentType.
        """
        headers = {"Authorization": f"Bearer {self.access_token}"}
        url = f"https://graph.microsoft.com/v1.0/me/messages/{message_id}/attachments"
        params = {"$select": "id,name,contentType,size"}

        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            print(f"Error fetching attachments: {response.status_code} - {response.text}")
            return []

        return response.json().get("value", [])

    def download_attachment(self, message_id: str, attachment_id: str) -> Tuple[bytes, str]:
        """
        Download a specific attachment from a message.
        Returns (content, filename).
        """
        headers = {"Authorization": f"Bearer {self.access_token}"}
        url = f"https://graph.microsoft.com/v1.0/me/messages/{message_id}/attachments/{attachment_id}"

        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Error downloading attachment: {response.status_code} - {response.text}")
            return None, None

        attachment = response.json()
        content = attachment.get("contentBytes", "").encode() if isinstance(attachment.get("contentBytes"), str) else attachment.get("contentBytes")

        # For file attachments, content is base64-encoded
        if attachment.get("@odata.type") == "#microsoft.graph.fileAttachment":
            import base64
            try:
                content = base64.b64decode(attachment.get("contentBytes", ""))
            except Exception as e:
                print(f"Error decoding attachment: {e}")
                return None, None

        return content, attachment.get("name")

    def find_invoices(self, year: int, month: int) -> List[Dict]:
        """
        Find all invoices in a given month.
        Returns list of invoices with: email metadata + PDFs list.
        """
        keywords = ["facture", "invoice", "reçu"]
        emails = self.get_emails_by_date_and_keyword(year, month, keywords)

        invoices = []
        for email in emails:
            message_id = email.get("id")
            attachments = self.get_attachments(message_id)

            # Filter for PDF attachments
            pdf_attachments = [
                att for att in attachments
                if att.get("contentType") == "application/pdf" or att.get("name", "").endswith(".pdf")
            ]

            if pdf_attachments:
                invoices.append({
                    "message_id": message_id,
                    "subject": email.get("subject"),
                    "from": email.get("from", {}).get("emailAddress", {}).get("address"),
                    "received_date": email.get("receivedDateTime"),
                    "pdf_attachments": pdf_attachments
                })

        return invoices
