"""
Download Health Connect export from Google Drive.

First-time setup:
1. Go to https://console.cloud.google.com/
2. Create a new project (or select existing one)
3. Enable the Google Drive API:
   - Go to "APIs & Services" > "Library"
   - Search for "Google Drive API" and enable it
4. Create OAuth credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - If prompted, configure the OAuth consent screen first (External, add your email as test user)
   - Application type: "Desktop app"
   - Download the JSON file and save it as "credentials.json" in this folder
5. Run this script — it will open a browser for you to log in the first time.
   After that, it saves a token.json and won't ask again.
"""

import os
import io
import zipfile
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_FILE = os.path.join(SCRIPT_DIR, "client_secret_961539101876-klnabcbjvlr24iecl8d0omhirsu1uomt.apps.googleusercontent.com.json")
TOKEN_FILE = os.path.join(SCRIPT_DIR, "token.json")

# Where to extract the .db file
DB_OUTPUT_PATH = os.path.join(SCRIPT_DIR, "health_connect_export.db")

# Search query — finds the most recent Health Connect zip in your Drive
# Adjust the filename pattern if your export has a different name
SEARCH_QUERY = "name contains 'health_connect' and mimeType='application/zip' and trashed=false"


def get_drive_service():
    """Authenticate and return a Google Drive API service."""
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

    creds = None

    # Load existing token
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    # If no valid credentials, do the OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                print(f"ERROR: {CREDENTIALS_FILE} not found!")
                print("Please download your OAuth credentials from Google Cloud Console.")
                print("See the docstring at the top of this file for setup instructions.")
                sys.exit(1)

            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the token for future runs
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
        print("Authentication successful! Token saved.")

    return build("drive", "v3", credentials=creds)


def find_latest_health_export(service):
    """Find the most recently modified Health Connect zip file on Drive."""
    results = service.files().list(
        q=SEARCH_QUERY,
        orderBy="modifiedTime desc",
        pageSize=1,
        fields="files(id, name, modifiedTime)"
    ).execute()

    files = results.get("files", [])
    if not files:
        print("No Health Connect export found on Google Drive.")
        print(f"Search query used: {SEARCH_QUERY}")
        print("Make sure the file name contains 'health_connect' and is a .zip file.")
        sys.exit(1)

    return files[0]


def download_and_extract(service, file_info):
    """Download the zip file and extract the .db file."""
    from googleapiclient.http import MediaIoBaseDownload

    file_id = file_info["id"]
    file_name = file_info["name"]
    modified = file_info["modifiedTime"]

    print(f"Found: {file_name} (modified: {modified})")
    print(f"Downloading...")

    # Download the file into memory
    request = service.files().get_media(fileId=file_id)
    buffer = io.BytesIO()
    downloader = MediaIoBaseDownload(buffer, request)

    done = False
    while not done:
        status, done = downloader.next_chunk()
        if status:
            print(f"  Download progress: {int(status.progress() * 100)}%")

    print("Download complete!")

    # Extract the .db file from the zip
    buffer.seek(0)
    with zipfile.ZipFile(buffer, "r") as zf:
        # Find the .db file inside the zip
        db_files = [f for f in zf.namelist() if f.endswith(".db")]
        if not db_files:
            print("ERROR: No .db file found in the zip archive.")
            print(f"Files in archive: {zf.namelist()}")
            sys.exit(1)

        db_file = db_files[0]
        print(f"Extracting: {db_file}")

        # Ensure output directory exists
        os.makedirs(os.path.dirname(DB_OUTPUT_PATH), exist_ok=True)

        # Extract the .db file
        with zf.open(db_file) as source, open(DB_OUTPUT_PATH, "wb") as target:
            target.write(source.read())

    print(f"Extracted to: {DB_OUTPUT_PATH}")


def main():
    print("=== Health Connect Data Downloader ===")
    print()

    service = get_drive_service()
    file_info = find_latest_health_export(service)
    download_and_extract(service, file_info)

    print()
    print("Done! Health data is ready for processing.")


if __name__ == "__main__":
    main()
