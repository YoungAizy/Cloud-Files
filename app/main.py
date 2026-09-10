import os
import uuid
import httpx
from fastapi import FastAPI, BackgroundTasks, HTTPException, status

from dotenv import load_dotenv

from app.models import DownloadRequest
from app.services.drive_upload import upload_g_drive
from app.services.email_sender import send_completion_email
from app.security.ssrf import validate_url
from app.exceptions.custom_errors import FileTooLargeError, GoogleUploadError

load_dotenv()

app = FastAPI()

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/downloads")
async def download(
    request: DownloadRequest,
    background_tasks: BackgroundTasks
):
    try:
        await validate_url(str(request.url))

    except Exception as e:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = str(e)
        )
        
    background_tasks.add_task(
        download_file_in_background,
        request
    )

    return {
        "success": True,
        "message": "Download started, an email will be sent to you once it finishes."
    }

async def download_file_in_background(request: DownloadRequest):
    try:
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=300
        ) as client:
            async with client.stream("GET", str(request.url), follow_redirects=True) as response:
                response.raise_for_status()

                filename = request.url.path.split("/")[-1]

                if not filename:
                    filename = f"{uuid.uuid4()}"
                
                if response.status_code == 200:
                    uploaded = await upload_g_drive(
                        request.access_token,
                        filename,
                        response.headers.get("content-type", "application/octet-stream"), 
                        response
                    )

        send_completion_email(
            request.access_token, True,
            uploaded
        )

    except (RuntimeError, FileTooLargeError, GoogleUploadError) as e:
        send_completion_email(
            request.access_token, False,
            {
                "download_link": request.url, 
                "error": str(e)
            }
        )
    except Exception as ex:
        send_completion_email(
            request.access_token, False,
            {
                "download_link": request.url, 
                "error": "Something went wrong. An unexpected error occured."
            }
        )
