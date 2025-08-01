from pydantic import BaseModel


class MessageResponse(BaseModel):
    message: str

    def __init__(self, message: str):
        super().__init__(message=message)
