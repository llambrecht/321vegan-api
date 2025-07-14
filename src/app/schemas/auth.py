from typing import Optional

from pydantic import BaseModel


class Token(BaseModel):
    """Bearer Access Token"""

    access_token: str
    token_type: str


class TokenPayload(BaseModel):
    """Payload for Bearer Access Token"""

    sub: Optional[int] = None

class ApiKeyPayload(BaseModel):
    """Payload for Api Access Key"""

    api_key: Optional[str] = None
