from pydantic import BaseModel

class ExtractionRequest(BaseModel):
    text: str