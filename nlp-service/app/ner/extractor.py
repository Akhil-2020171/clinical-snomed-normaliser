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

        procedure_entities = self._extract_entities(
            text,
            self.models.procedure_model,
            "PROCEDURE"
        )

        medication_entities = self._extract_entities(
            text,
            self.models.medication_model,
            "MEDICATION"
        )

        entities = (
            symptom_entities
            + disease_entities
            + procedure_entities
            + medication_entities
        )

        entities = self.get_non_overlapping_entities(
            entities
        )

        return {
            "entities": entities
        }

    def transform_text(self, text: str, entities: list[dict]) -> str:

        replacements = []

        for entity in entities:

            snomed_matches = entity.get("snomed", [])

            if not snomed_matches:
                continue

            best_match = snomed_matches[0]

            replacement = (
                f'{best_match["conceptId"]}|{best_match["fsn"]}'
            )

            replacements.append({
                "start": entity["start"],
                "end": entity["end"],
                "replacement": replacement
            })

        replacements.sort(
            key=lambda x: x["start"],
            reverse=True
        )

        transformed = text

        for replacement in replacements:
            transformed = (
                transformed[:replacement["start"]]
                + replacement["replacement"]
                + transformed[replacement["end"]:]
            )

        return transformed

    def _extract_entities(
        self,
        text,
        ner_model,
        entity_type,
        allowed_label=None
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

            if allowed_label and label not in {
                f"B-{allowed_label}",
                f"I-{allowed_label}"
            }:
                label = "O"

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

    def get_non_overlapping_entities(self, entities: list[dict]) -> list[dict]:

        selected = []

        # Prefer longer entities when spans overlap.
        entities = sorted(
            entities,
            key=lambda x: (
                x["end"] - x["start"],
                -x["start"]
            ),
            reverse=True
        )

        for entity in entities:

            overlaps = False

            for existing in selected:

                if (
                    entity["start"] < existing["end"]
                    and entity["end"] > existing["start"]
                ):
                    overlaps = True
                    break

            if not overlaps:
                selected.append(entity)

        return sorted(
            selected,
            key=lambda x: x["start"]
        )