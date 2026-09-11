from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

security = HTTPBearer()


async def get_access_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    return credentials.credentials