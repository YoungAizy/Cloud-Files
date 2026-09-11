import os
import uuid
import httpx
from fastapi import FastAPI, BackgroundTasks, HTTPException, status, Depends

from dotenv import load_dotenv

from app.models import DownloadRequest
from app.services.drive_upload import upload_g_drive
from app.services.email_sender import send_completion_email
from app.security.ssrf import validate_url
from app.exceptions.custom_errors import FileTooLargeError, GoogleUploadError

from app.middleware.authentication import get_access_token

load_dotenv()

app = FastAPI()

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/downloads")
async def download(
    request: DownloadRequest,
    background_tasks: BackgroundTasks,
    access_token: str = Depends(get_access_token)
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
        request, access_token
    )

    return {
        "success": True,
        "message": "Download started, an email will be sent to you once it finishes."
    }

async def download_file_in_background(request: DownloadRequest, access_token: str):
    filename = request.filename
    
    try:
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=300
        ) as client:
            async with client.stream("GET", str(request.url), follow_redirects=False) as response:
                response.raise_for_status()

                filename = request.url.path.split("/")[-1] if not filename else filename

                if not filename:
                    filename = f"{uuid.uuid4()}"
                
                if response.status_code == 200:
                    uploaded = await upload_g_drive(
                        access_token,
                        filename,
                        response.headers.get("content-type", "application/octet-stream"), 
                        response
                    )

        send_completion_email(
            access_token, True,
            uploaded
        )

    except (RuntimeError, FileTooLargeError, GoogleUploadError) as e:
        send_completion_email(
            access_token, False,
            {
                "download_link": request.url,
                "filename": filename,
                "error": str(e)
            }
        )
    except Exception as ex:
        send_completion_email(
            access_token, False,
            {
                "download_link": request.url,
                "filename": filename,
                "error": "Something went wrong. An unexpected error occured."
            }
        )
