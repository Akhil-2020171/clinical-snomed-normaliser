from pydantic import BaseModel


class ClinicalEntity(BaseModel):
    mention: str
    start: int
    end: int
    concept_id: str | None = None
    fsn: str | None = None
    semantic_tag: str | None = None
    confidence: float | None = None


class ExtractionResponse(BaseModel):
    entities: list[ClinicalEntity]