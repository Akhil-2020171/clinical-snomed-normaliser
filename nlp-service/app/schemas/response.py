from pydantic import BaseModel

class ClinicalEntity(BaseModel):
    mention: str
    start: int
    end: int
    label: str

class ExtractionResponse(BaseModel):
    entities: list[ClinicalEntity]