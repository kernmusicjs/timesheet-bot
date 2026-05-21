"""
Dropbox client for reading and uploading files.
"""

import dropbox
from dropbox.files import WriteMode
from typing import Optional
import os
from config import DROPBOX_APP_KEY, DROPBOX_APP_SECRET, DROPBOX_REFRESH_TOKEN

class DropboxClient:
    def __init__(self, app_key: str, app_secret: str, refresh_token: str):
        self.app_key = app_key
        self.app_secret = app_secret
        self.refresh_token = refresh_token
        self.dbx = None
        self.connect()

    def connect(self):
        """Establish connection to Dropbox using OAuth2 refresh token."""
        try:
            self.dbx = dropbox.Dropbox(
                oauth2_refresh_token=self.refresh_token,
                app_key=self.app_key,
                app_secret=self.app_secret
            )
            # Test connection
            self.dbx.users_get_current_account()
            print("✓ Dropbox connected")
        except Exception as e:
            print(f"✗ Dropbox connection failed: {e}")
            raise

    def read_file(self, path: str) -> str:
        """
        Read a text file from Dropbox.
        """
        try:
            metadata, response = self.dbx.files_download(path)
            return response.content.decode('utf-8')
        except dropbox.exceptions.ApiError as e:
            if e.error.is_path() and e.error.get_path().is_not_found():
                print(f"File not found: {path}")
                return None
            raise

    def write_file(self, path: str, content: str, overwrite: bool = True) -> bool:
        """
        Write a text file to Dropbox.
        """
        try:
            mode = WriteMode.overwrite if overwrite else WriteMode.add
            self.dbx.files_upload(
                content.encode('utf-8'),
                path,
                mode=mode
            )
            return True
        except dropbox.exceptions.ApiError as e:
            print(f"Error writing file {path}: {e}")
            return False

    def upload_binary_file(self, local_path: str, dropbox_path: str, overwrite: bool = True) -> bool:
        """
        Upload a binary file (e.g., Excel) to Dropbox.
        """
        try:
            with open(local_path, 'rb') as f:
                content = f.read()

            mode = WriteMode.overwrite if overwrite else WriteMode.add
            self.dbx.files_upload(
                content,
                dropbox_path,
                mode=mode
            )
            return True
        except Exception as e:
            print(f"Error uploading file {dropbox_path}: {e}")
            return False

    def get_file_link(self, path: str) -> Optional[str]:
        """
        Get a shareable link for a file.
        """
        try:
            shared_link_metadata = self.dbx.sharing_create_shared_link_with_settings(
                path,
                dropbox.sharing.SharedLinkSettings(
                    requested_visibility=dropbox.sharing.RequestedVisibility.public
                )
            )
            return shared_link_metadata.url
        except dropbox.exceptions.ApiError as e:
            # Link might already exist
            if e.error.is_shared_link_already_exists():
                try:
                    links = self.dbx.sharing_list_shared_links(path=path)
                    if links.links:
                        return links.links[0].url
                except:
                    pass
            print(f"Error getting link for {path}: {e}")
            return None

    def create_folder(self, path: str) -> bool:
        """
        Create a folder in Dropbox if it doesn't exist.
        """
        try:
            self.dbx.files_create_folder_v2(path)
            return True
        except dropbox.exceptions.ApiError as e:
            if e.error.is_path() and e.error.get_path().is_conflict():
                # Folder already exists
                return True
            print(f"Error creating folder {path}: {e}")
            return False

    def download_binary(self, dropbox_path: str, local_path: str) -> bool:
        """Download a binary file from Dropbox to a local path."""
        try:
            metadata, response = self.dbx.files_download(dropbox_path)
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            with open(local_path, 'wb') as f:
                f.write(response.content)
            return True
        except Exception as e:
            print(f"Error downloading {dropbox_path}: {e}")
            return False

    def upload_bytes(self, content: bytes, dropbox_path: str) -> bool:
        """Upload binary content directly from memory."""
        try:
            self.dbx.files_upload(content, dropbox_path, mode=WriteMode.overwrite)
            return True
        except Exception as e:
            print(f"Error uploading bytes to {dropbox_path}: {e}")
            return False

    def list_folder(self, path: str) -> list:
        """List files in a Dropbox folder. Returns list of dicts with name and path."""
        try:
            result = self.dbx.files_list_folder(path)
            files = []
            for entry in result.entries:
                if isinstance(entry, dropbox.files.FileMetadata):
                    files.append({"name": entry.name, "path": entry.path_lower})
            return files
        except Exception as e:
            print(f"Error listing folder {path}: {e}")
            return []
