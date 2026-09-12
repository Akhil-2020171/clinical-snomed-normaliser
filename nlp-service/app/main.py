from fastapi import FastAPI

from app.ner.model import ClinicalNerModels
from app.ner.extractor import ClinicalEntityExtractor

from app.linker.snomed_loader import SnomedLoader
from app.linker.snomed_linker import SnomedLinker

from app.assertion.detector import AssertionDetector

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

@app.post("/extract")
def extract_entities(text: str):

    result = entity_extractor.extract(text)

    for entity in result["entities"]:

        entity["assertion"] = (
            assertion_detector.detect(
                text,
                entity["start"]
            )
        )

        matches = snomed_linker.link(
            entity["mention"],
            entity["label"]
        )

        entity["snomed"] = matches

    return result