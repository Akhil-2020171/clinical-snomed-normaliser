import csv
import sys
import os
from pathlib import Path

csv.field_size_limit(sys.maxsize)

SNOMED_BASE = Path(
    os.getenv("SNOMED_BASE")
)

DESCRIPTION_FILE = (
    SNOMED_BASE /
    "sct2_Description_Snapshot-en_INT_20260901.txt"
)

CONCEPT_FILE = (
    SNOMED_BASE /
    "sct2_Concept_Snapshot_INT_20260901.txt"
)

RELATIONSHIP_FILE = (
    SNOMED_BASE /
    "sct2_Relationship_Snapshot_INT_20260901.txt"
)

FSN_TYPE_ID = "900000000000003001"
SYNONYM_TYPE_ID = "900000000000013009"

IS_A_TYPE_ID = "116680003"

class SnomedLoader:

    def load_active_concepts(self):
        active_concepts = set()

        print("Loading active SNOMED concepts...")
        print(f"File: {CONCEPT_FILE}")

        with CONCEPT_FILE.open(
            "r",
            encoding="utf-8"
        ) as file:

            reader = csv.DictReader(
                file,
                delimiter="\t"
            )

            for row in reader:

                if row["active"] == "1":
                    active_concepts.add(row["id"])

        print(
            f"Loaded active concepts: "
            f"{len(active_concepts)}"
        )

        return active_concepts

    def load_hierarchy(self):
        parents = {}

        print("Loading SNOMED CT hierarchy...")
        print(f"File: {RELATIONSHIP_FILE}")

        with RELATIONSHIP_FILE.open(
            "r",
            encoding="utf-8"
        ) as file:

            reader = csv.DictReader(
                file,
                delimiter="\t"
            )

            for row in reader:

                if row["active"] != "1":
                    continue

                if row["typeId"] != IS_A_TYPE_ID:
                    continue

                source_id = row["sourceId"]
                destination_id = row["destinationId"]

                parents.setdefault(
                    source_id,
                    set()
                ).add(destination_id)

        print(
            f"Loaded concepts with parents: "
            f"{len(parents)}"
        )

        return parents

    def load(self):
        active_concepts = self.load_active_concepts()
        parents = self.load_hierarchy()

        term_to_concepts = {}
        concept_to_terms = {}
        concept_to_fsn = {}
        concept_to_descriptions = {}

        print("Loading SNOMED CT descriptions...")
        print(f"File: {DESCRIPTION_FILE}")

        with DESCRIPTION_FILE.open(
            "r",
            encoding="utf-8"
        ) as file:

            reader = csv.DictReader(
                file,
                delimiter="\t"
            )

            for row in reader:
                if row["active"] != "1":
                    continue

                concept_id = row["conceptId"]

                if concept_id not in active_concepts:
                    continue

                term = row["term"]
                normalized_term = term.lower().strip()
                type_id = row["typeId"]

                # --------------------------------------------------
                # Fully Specified Name (FSN)
                # --------------------------------------------------
                if type_id == FSN_TYPE_ID:

                    concept_to_fsn[concept_id] = term

                    term_to_concepts.setdefault(
                        normalized_term,
                        set()
                    ).add(concept_id)

                    concept_to_descriptions.setdefault(
                        concept_id,
                        []
                    ).append({
                        "term": term,
                        "matchType": "fsn"
                    })

                # --------------------------------------------------
                # Synonym
                # --------------------------------------------------
                elif type_id == SYNONYM_TYPE_ID:

                    concept_to_terms.setdefault(
                        concept_id,
                        []
                    ).append(term)

                    term_to_concepts.setdefault(
                        normalized_term,
                        set()
                    ).add(concept_id)

                    concept_to_descriptions.setdefault(
                        concept_id,
                        []
                    ).append({
                        "term": term,
                        "matchType": "synonym"
                    })

        print(
            f"Loaded FSNs: "
            f"{len(concept_to_fsn)}"
        )

        print(
            f"Loaded concepts with synonyms: "
            f"{len(concept_to_terms)}"
        )

        print(
            f"Unique searchable terms: "
            f"{len(term_to_concepts)}"
        )

        return {
            "term_to_concepts": term_to_concepts,
            "concept_to_terms": concept_to_terms,
            "concept_to_fsn": concept_to_fsn,
            "concept_to_descriptions": concept_to_descriptions,
            "active_concepts": active_concepts,
            "parents": parents
        }