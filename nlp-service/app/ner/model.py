from transformers import (
    AutoTokenizer,
    AutoModelForTokenClassification
)


MODEL_NAME = "your-clinical-ner-model"


class NerModel:

    def __init__(self):
        self.tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

        self.model = AutoModelForTokenClassification.from_pretrained(
            MODEL_NAME
        )