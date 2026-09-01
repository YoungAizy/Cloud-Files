from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google.oauth2.credentials import Credentials

import io

def get_g_service(access_token):
    credentials = Credentials(
        token=access_token
    )

    service = build(
        "drive",
        "v3",
        credentials=credentials
    )
    return service

def upload_g_drive(access_token, filename, file_content, file_type):
    service = get_g_service(access_token)
    folder_id = get_or_create_folder(service)

    file_metadata = {
        "name": filename,
        "parents": [folder_id]
    }

    media = MediaIoBaseUpload(
        io.BytesIO(file_content),
        mimetype= file_type,
        resumable=True
    )

    created_file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id,name,webViewLink"
    ).execute()
    
    return {"uploaded_name": created_file.get("name"), 
            "webViewLink": created_file.get("webViewLink")}

def get_or_create_folder(service):
    """
    Searches for an existing folder. If not found, creates it.
    Returns the folder ID.
    """
    # 1. Build the search query ensuring we only look for active folders matching the name
    query = "name = 'Drive-Drop' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    results = service.files().list(
        q=query,
        spaces="drive", 
        fields="files(id, name)"
    ).execute()
    
    files = results.get("files", [])
    # 2. If folder exists, return its ID
    if files:
        return files[0]["id"]
    
    new_folder = service.files().create(
        body={
            "name": "Drive-Drop",
            "mimeType": "application/vnd.google-apps.folder"
        },
        fields="id"
    ).execute()
    
    return new_folder.get("id")