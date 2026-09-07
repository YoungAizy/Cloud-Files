import os
import uuid
import httpx
import aiofiles
from fastapi import FastAPI, HTTPException, status

from dotenv import load_dotenv

from app.models import DownloadRequest
from app.drive_upload import upload_g_drive

load_dotenv()

app = FastAPI()

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/downloads")
async def download_file(request: DownloadRequest):
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

        return {
            "success": True,
            "object": uploaded
        }

    except ValueError as e:
        raise HTTPException(
            status_code= status.HTTP_413_CONTENT_TOO_LARGE,
            detail= f"Upload Failed: {e}"
        )
    except Exception as ex:
        raise HTTPException(
            status_code=500,
            detail=str(ex)
        )
