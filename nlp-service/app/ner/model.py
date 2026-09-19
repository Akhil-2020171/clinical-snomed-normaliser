from transformers import (
    AutoTokenizer,
    AutoModelForTokenClassification
)


SYMPTOM_MODEL_NAME = (
    "DT4H/en-symptom-cardioberta-multiclass-ner"
)

DISEASE_MODEL_NAME = (
    "DT4H/en-disease-cardioberta-multiclass-ner"
)

PROCEDURE_MODEL_NAME = (
    "DT4H/cardio-ner-en-procedure-cardioberta-multiclass"
)

MEDICATION_MODEL_NAME = (
    "DT4H/cardio-ner-en-medication-cardioberta-multiclass"
)

class NERModel:
    def __init__(self, model_name: str):
        print(f"Loading NER model: {model_name}")

        self.tokenizer = AutoTokenizer.from_pretrained(model_name)

        self.model = AutoModelForTokenClassification.from_pretrained(
            model_name
        )

        self.model.eval()

        self.labels = self.model.config.id2label

        print(f"Loaded: {model_name}")
        print(f"Labels: {self.labels}")


class ClinicalNerModels:

    def __init__(self):

        self.symptom_model = NERModel(
            SYMPTOM_MODEL_NAME
        )

        self.disease_model = NERModel(
            DISEASE_MODEL_NAME
        )

        self.procedure_model = NERModel(
            PROCEDURE_MODEL_NAME
        )
    
        self.medication_model = NERModel(
            MEDICATION_MODEL_NAME
        )