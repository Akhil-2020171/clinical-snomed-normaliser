from pydantic import BaseModel


class SnomedHierarchy(BaseModel):
    clinicalFinding: bool
    disease: bool
    qualifierValue: bool
    bodyStructure: bool
    procedure: bool
    substance: bool

class SnomedMatch(BaseModel):
    conceptId: str
    fsn: str
    semanticTag: str | None
    matchType: str
    score: float
    hierarchy: SnomedHierarchy


class ClinicalEntity(BaseModel):
    mention: str
    start: int
    end: int
    label: str
    assertion: str
    snomed: list[SnomedMatch]


class ExtractionResponse(BaseModel):
    entities: list[ClinicalEntity]
    transformedText: str