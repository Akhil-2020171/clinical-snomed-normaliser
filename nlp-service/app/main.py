from fastapi import FastAPI

from app.ner.model import ClinicalNerModels
from app.ner.extractor import ClinicalEntityExtractor

from app.linker.snomed_loader import SnomedLoader
from app.linker.snomed_linker import SnomedLinker

from app.assertion.detector import AssertionDetector

from app.schemas.request import ExtractionRequest
from app.schemas.response import ExtractionResponse

app = FastAPI()

assertion_detector = AssertionDetector()

ner_models = ClinicalNerModels()

entity_extractor = ClinicalEntityExtractor(
    ner_models
)


snomed_loader = SnomedLoader()

snomed_data = snomed_loader.load()

snomed_linker = SnomedLinker(
    snomed_data
)

@app.post("/extract", response_model=ExtractionResponse)
def extract_entities(request: ExtractionRequest):
    result = entity_extractor.extract(request.text)

    for entity in result["entities"]:

        entity["assertion"] = (
            assertion_detector.detect(
                request.text,
                entity["start"]
            )
        )

        entity["snomed"] = (
            snomed_linker.link(
                entity["mention"],
                entity["label"]
            )
        )

    result["transformedText"] = entity_extractor.transform_text(
        request.text,
        result["entities"]
    )

    return result