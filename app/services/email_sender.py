import base64
import httpx
from email.message import EmailMessage

GMAIL_SEND_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"

sub = "Drive-Drop Upload"

async def get_user_email(access_token: str) -> str:
    headers = {
        "Authorization": f"Bearer {access_token}",
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers=headers,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        return data["email"]

def get_body_and_subject(is_successful: bool, payload_data) -> tuple[str, str]:
    if is_successful:
        subject = f"{sub} Successful"
        body = (
            f"Your file has been successfully downloaded to Google Drive.\n\n"
            f"File Name: {payload_data['uploaded_name']}\n"
            f"View Link: {payload_data['webViewLink']}\n\n"
            "Thank you for using Drive-Drop!"
        )
    else:
        subject = f"{sub} Failed"
        body = (
            f"Oops! We ran into an error while downloading your file `{payload_data['filename']}` to Google Drive.\n\n"
            f"Download Link: {payload_data['download_link']}\n"
            f"Error: {payload_data['error']}\n\n"
            "Please try again or contact support."
        )

    return subject, body

async def send_completion_email(access_token: str, is_successful: bool, payload_data):
    user_email = get_user_email(access_token)
    subject, body = get_body_and_subject(is_successful, payload_data)
    
    message = EmailMessage()
    message["To"] = user_email
    # message["From"] = user_email
    message["Subject"] = subject
    message.set_content(body)
    
    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    
    payload = {"raw": encoded_message}

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            GMAIL_SEND_URL,
            headers=headers,
            json=payload,
            timeout=10
        )

        response.raise_for_status()
        
        return response.json()