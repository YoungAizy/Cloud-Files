import os
import uuid
import httpx
import aiofiles
from fastapi import FastAPI, HTTPException

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

            response = await client.get(str(request.url))

            response.raise_for_status()

        filename = request.url.path.split("/")[-1]

        if not filename:
            filename = f"{uuid.uuid4()}"

        if response.status_code == 200:
            uploaded = upload_g_drive(
                request.access_token,
                filename,
                response.content, 
                response.headers.get("content-type")
            )

        return {
            "success": True,
            "object": uploaded
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


async def save_file(response,name):
    async with aiofiles.open(name, "wb") as out_file:
        async for chunk in response.aiter_bytes(chunk_size=1024 * 64): # 64KB chunks
            await out_file.write(chunk)