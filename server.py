import os
import uvicorn
from dotenv import load_dotenv

load_dotenv()

HOST = os.getenv('HOST',"127.0.0.1")
PORT = int(os.getenv('PORT',8000))
ENV = os.getenv("STAGE", "DEV")

reload_enabled = False if ENV == "PROD" else True

def start_server():
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=reload_enabled)
    
if __name__ == '__main__':
    start_server()