from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

import asyncio
import httpx
from app.httpx_stream import HTTPXStreamIterator

DRIVE_UPLOAD_URL = (
    "https://www.googleapis.com/upload/drive/v3/files"
)

CHUNK_SIZE = (8 * 1024 * 1024) * 2  # 16 MiB
QUEUE_SIZE = 3
MAX_QUEUE_SIZE = 6


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

async def create_upload_session(
    client: httpx.AsyncClient,
    access_token: str,
    filename: str,
    content_type: str,
    parent: str
)-> str:
    """
    Tell Google Drive that we're about to upload a file.

    Google responds with a temporary upload URL.
    """
    
    metadata = {
        "name": filename,
        "mimeType": content_type,
        "parents": [parent]
    }
    
    response = await client.post(
        DRIVE_UPLOAD_URL,
        params={
            "uploadType": "resumable",
            "fields":"id,name,webViewLink"
        },
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=UTF-8",
            "X-Upload-Content-Type": content_type,
        },
        json=metadata,
    )

    response.raise_for_status()

    upload_url = response.headers.get("Location")

    if not upload_url:
        raise RuntimeError(
            "Google Drive did not return an upload URL"
        )

    return upload_url

async def upload_chunk(
    client: httpx.AsyncClient,
    upload_url: str,
    access_token: str,
    chunk: bytes,
    start: int,
    total_size: str,
):
    """
    Upload one chunk to the Google Drive resumable upload session.
    """

    end = start + len(chunk) - 1
    
    response = await client.put(
        upload_url,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Length": str(len(chunk)),
            "Content-Range": (
                f"bytes {start}-{end}/{total_size}"
            ),
        },
        content=chunk,
        timeout=300,
    )
    
    if response.status_code not in (200, 201, 308):
        response.raise_for_status()

    return response

async def upload_g_drive(access_token: str, filename: str, file_type:str, response: httpx.Response):
    
    service = get_g_service(access_token)
    folder_id = get_or_create_folder(service)
    
    content_length = response.headers.get("content-length")
    content_length = content_length if content_length else  "*"
    
    queue = asyncio.Queue(maxsize=QUEUE_SIZE)
    
    async with httpx.AsyncClient(
        timeout=300
    ) as drive_client:

        upload_url = await create_upload_session(
            client=drive_client,
            access_token=access_token,
            filename=filename,
            content_type=file_type,
            parent = folder_id
        )

        # -----------------------------------------------------
        # 2. Read the source file in chunks
        # -----------------------------------------------------

        file_stream = HTTPXStreamIterator(response,queue)

        async def uploader():
            uploaded_bytes = 0

            while True:
                chunk = await queue.get()

                try:
                    if chunk is None:
                        return None

                    drive_response = await upload_chunk(
                        client=drive_client,
                        upload_url=upload_url,
                        access_token=access_token,
                        chunk=chunk,
                        start=uploaded_bytes,
                        total_size=content_length,
                    )
                    # 308 = Google received this chunk, but the upload isn't finished yet.
                    if drive_response.status_code == 308:
                        uploaded_bytes += len(chunk)

                        continue

                    # 200 / 201 = upload completed.
                    if drive_response.status_code in (
                        200,
                        201,
                    ):
                        created_file = drive_response.json()

                        return {"uploaded_name": created_file.get("name"), 
                                "webViewLink": created_file.get("webViewLink")}
                except Exception as e:    
                    raise RuntimeError("Google Drive upload failed"
                    ) from e 
                finally:
                    queue.task_done()


        downloader_task = asyncio.create_task(file_stream.downloader(CHUNK_SIZE))
        uploader_task = asyncio.create_task(uploader())

        try:
            result = await uploader_task
            await downloader_task

            return result

        except Exception:
            downloader_task.cancel()

            try:
                await downloader_task
            except asyncio.CancelledError:
                pass

            raise  

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