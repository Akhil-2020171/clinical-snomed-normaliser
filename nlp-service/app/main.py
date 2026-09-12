from fastapi import FastAPI

from app.schemas.request import ExtractionRequest
from app.schemas.response import ExtractionResponse

from app.ner.model import NerModel
from app.ner.extractor import ClinicalEntityExtractor


app = FastAPI()


ner_model = NerModel()

entity_extractor = ClinicalEntityExtractor(
    ner_model
)


@app.post("/extract")
def extract(request: ExtractionRequest):

    entities = entity_extractor.extract(
        request.text
    )

    return {
        "entities": entities
    }