from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google.oauth2.credentials import Credentials

import io

def upload_g_drive(access_token, filename, file_content, file_type):
    credentials = Credentials(
        token=access_token
    )

    service = build(
        "drive",
        "v3",
        credentials=credentials
    )

    file_metadata = {
        "name": filename
    }

    media = MediaIoBaseUpload(
        io.BytesIO(file_content),
        mimetype= file_type,
        resumable=True
    )

    service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id,name,webViewLink"
    ).execute()

