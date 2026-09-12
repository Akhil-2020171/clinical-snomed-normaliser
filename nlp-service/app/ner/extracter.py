class ClinicalEntityExtractor:

    def __init__(self, ner_model):
        self.ner_model = ner_model

    def extract(self, text: str):
        ...