import torch


class ClinicalEntityExtractor:

    def __init__(self, models):
        self.models = models

    def extract(self, text: str):

        symptom_entities = self._extract_entities(
            text,
            self.models.symptom_model,
            "SYMPTOM"
        )

        disease_entities = self._extract_entities(
            text,
            self.models.disease_model,
            "DISEASE"
        )

        entities = symptom_entities + disease_entities

        entities.sort(key=lambda x: x["start"])

        return {
            "entities": entities
        }

    def _extract_entities(
        self,
        text,
        ner_model,
        entity_type
    ):

        tokenizer = ner_model.tokenizer
        model = ner_model.model
        labels = ner_model.labels

        inputs = tokenizer(
            text,
            return_tensors="pt",
            return_offsets_mapping=True,
            truncation=True
        )

        offset_mapping = inputs.pop("offset_mapping")

        with torch.no_grad():
            outputs = model(**inputs)

        predictions = torch.argmax(
            outputs.logits,
            dim=-1
        )[0]

        entities = []

        current_entity = None

        for index, token_id in enumerate(predictions):

            label = labels[token_id.item()]

            start, end = offset_mapping[0][index].tolist()

            if start == end:
                continue

            if label.startswith("B-"):

                if current_entity:
                    entities.append(current_entity)

                current_entity = {
                    "mention": text[start:end],
                    "start": start,
                    "end": end,
                    "label": entity_type
                }

            elif label.startswith("I-") and current_entity:

                current_entity["mention"] = text[
                    current_entity["start"]:end
                ]

                current_entity["end"] = end

            else:

                if current_entity:
                    entities.append(current_entity)
                    current_entity = None

        if current_entity:
            entities.append(current_entity)

        return entities