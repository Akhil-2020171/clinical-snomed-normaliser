import re
from app.linker.lexical_normalizer import LexicalNormalizer

CLINICAL_FINDING = "404684003"
DISEASE = "64572001"
QUALIFIER_VALUE = "362981000"
BODY_STRUCTURE = "123037004"
PROCEDURE = "71388002"
SUBSTANCE = "105590001"

CONTAINED_MATCH_STOPWORDS = {
    "a",
    "an",
    "and",
    "at",
    "for",
    "in",
    "of",
    "on",
    "or",
    "the",
    "to",
    "with"
}

class SnomedLinker:

    def __init__(self, snomed_data):
        self.term_to_concepts = (
            snomed_data["term_to_concepts"]
        )

        self.concept_to_fsn = (
            snomed_data["concept_to_fsn"]
        )

        self.concept_to_descriptions = (
            snomed_data["concept_to_descriptions"]
        )

        self.parents = snomed_data["parents"]

        self.lexical_normalizer = LexicalNormalizer()

    def normalize_term(self, term: str) -> str:
        """
        Normalize text before SNOMED lookup.

        Examples:

            "Chest Pain"
                -> "chest pain"

            " chest pain "
                -> "chest pain"

            "chest   pain"
                -> "chest pain"
        """

        term = term.lower().strip()

        # Collapse multiple whitespace characters.
        term = re.sub(r"\s+", " ", term)

        return term

    def get_semantic_tag(
        self,
        fsn: str
    ) -> str | None:

        """
        Extract semantic tag from SNOMED FSN.

        Example:

            Diabetes mellitus (disorder)
                -> disorder

            Chest pain (finding)
                -> finding
        """

        match = re.search(
            r"\(([^()]*)\)$",
            fsn
        )

        if match:
            return match.group(1).lower()

        return None

    def find_candidates(
        self,
        mention: str
    ):

        normalized = self.normalize_term(
            mention
        )

        concept_ids = self.term_to_concepts.get(
            normalized,
            set()
        )

        candidates = []

        for concept_id in concept_ids:

            fsn = self.concept_to_fsn.get(
                concept_id
            )

            if not fsn:
                continue

            match_type = None

            descriptions = (
                self.concept_to_descriptions.get(
                    concept_id,
                    []
                )
            )

            for description in descriptions:
                description_term = (
                    self.normalize_term(
                        description["term"]
                    )
                )

                if description_term == normalized:
                    match_type = (
                        description["matchType"]
                    )
                    break

            if match_type is None:
                continue

            candidates.append({
                "conceptId": concept_id,
                "fsn": fsn,
                "semanticTag": self.get_semantic_tag(
                    fsn
                ),
                "matchType": match_type
            })

        return candidates

    def classify_concept(
        self,
        concept_id: str
    ):
        return {
            "clinicalFinding": self.is_descendant_of(
                concept_id,
                CLINICAL_FINDING
            ),
            "disease": self.is_descendant_of(
                concept_id,
                DISEASE
            ),
            "qualifierValue": self.is_descendant_of(
                concept_id,
                QUALIFIER_VALUE
            ),
            "bodyStructure": self.is_descendant_of(
                concept_id,
                BODY_STRUCTURE
            ),
            "procedure": self.is_descendant_of(
                concept_id,
                PROCEDURE
            ),
            "substance": self.is_descendant_of(
                concept_id,
                SUBSTANCE
            )
        }

    def rank_candidates(
        self,
        candidates,
        entity_label: str
    ):
        for candidate in candidates:

            score = 0.0

            # --------------------------------
            # 1. Base lexical match
            # --------------------------------

            if candidate["matchType"] == "fsn":
                score += 1.00

            elif candidate["matchType"] == "synonym":
                score += 0.95

            elif candidate["matchType"] == "lexical_normalization":
                score += 0.90

            else:
                score += 0.50

            concept_id = candidate["conceptId"]

            # --------------------------------
            # 2. Hierarchy signals
            # --------------------------------

            hierarchy = self.classify_concept(
                concept_id
            )

            is_clinical_finding = hierarchy["clinicalFinding"]
            is_disease = hierarchy["disease"]
            is_qualifier = hierarchy["qualifierValue"]
            is_body_structure = hierarchy["bodyStructure"]

            # --------------------------------
            # 3. Entity-aware ranking
            # --------------------------------

            if entity_label == "SYMPTOM":

                if is_clinical_finding:
                    score += 0.40

                if is_disease:
                    score += 0.25

                if is_qualifier:
                    score -= 0.80

                if is_body_structure:
                    score -= 0.70

            elif entity_label == "DISEASE":

                if is_disease:
                    score += 0.40

                if is_clinical_finding:
                    score += 0.20

                if is_qualifier:
                    score -= 0.80

                if is_body_structure:
                    score -= 0.70

            elif entity_label == "PROCEDURE":

                if hierarchy["procedure"]:
                    score += 0.40

                if hierarchy["clinicalFinding"]:
                    score += 0.10

                if hierarchy["qualifierValue"]:
                    score -= 0.80

                if hierarchy["bodyStructure"]:
                    score -= 0.70

            elif entity_label == "MEDICATION":

                if hierarchy["substance"]:
                    score += 0.40

                if hierarchy["qualifierValue"]:
                    score -= 0.80

                if hierarchy["bodyStructure"]:
                    score -= 0.70

            candidate["score"] = round(
                score,
                2
            )

            candidate["hierarchy"] = hierarchy

        candidates.sort(
            key=lambda candidate: candidate["score"],
            reverse=True
        )

        return candidates

    def rank_contained_candidates(
        self,
        contained_terms,
        entity_label: str
    ):
        ranked = []

        for item in contained_terms:

            term = item["term"]

            for concept_id in item["conceptIds"]:

                fsn = self.concept_to_fsn.get(
                    concept_id
                )

                if not fsn:
                    continue

                hierarchy = self.classify_concept(
                    concept_id
                )

                candidate = {
                    "term": term,
                    "conceptId": concept_id,
                    "fsn": fsn,
                    "semanticTag": self.get_semantic_tag(
                        fsn
                    ),
                    "hierarchy": hierarchy
                }

                score = 0.0

                # -----------------------------
                # Entity compatibility
                # -----------------------------

                if entity_label == "SYMPTOM":

                    if hierarchy["clinicalFinding"]:
                        score += 1.00

                    if hierarchy["disease"]:
                        score += 0.60

                    if hierarchy["qualifierValue"]:
                        score -= 1.00

                    if hierarchy["bodyStructure"]:
                        score -= 0.80

                elif entity_label == "DISEASE":

                    if hierarchy["disease"]:
                        score += 1.00

                    if hierarchy["clinicalFinding"]:
                        score += 0.50

                    if hierarchy["qualifierValue"]:
                        score -= 1.00

                    if hierarchy["bodyStructure"]:
                        score -= 0.80

                elif entity_label == "PROCEDURE":

                    if hierarchy["procedure"]:
                        score += 1.00

                    if hierarchy["clinicalFinding"]:
                        score += 0.10

                    if hierarchy["qualifierValue"]:
                        score -= 1.00

                    if hierarchy["bodyStructure"]:
                        score -= 0.80

                elif entity_label == "MEDICATION":

                    if hierarchy["substance"]:
                        score += 1.00

                    if hierarchy["qualifierValue"]:
                        score -= 1.00

                    if hierarchy["bodyStructure"]:
                        score -= 0.80

                candidate["score"] = round(
                    score,
                    2
                )

                ranked.append(candidate)

        ranked.sort(
            key=lambda candidate: candidate["score"],
            reverse=True
        )

        return ranked

    def select_clinical_candidate(
        self,
        candidates,
        entity_label: str
    ):
        if entity_label == "PROCEDURE":

            procedure_candidates = [
                candidate
                for candidate in candidates
                if candidate["hierarchy"]["procedure"]
            ]

            if not procedure_candidates:
                return None

            return procedure_candidates[0]

        if entity_label == "MEDICATION":

            medication_candidates = [
                candidate
                for candidate in candidates
                if candidate["hierarchy"]["substance"]
            ]

            if not medication_candidates:
                return None

            return medication_candidates[0]

        clinical_candidates = [
            candidate
            for candidate in candidates
            if candidate["hierarchy"]["clinicalFinding"]
        ]

        if not clinical_candidates:
            return None

        return clinical_candidates[0]

    def link(
        self,
        mention: str,
        entity_label: str
    ):
        # --------------------------------------------------
        # 1. Try the original SNOMED terminology.
        # --------------------------------------------------
        candidates = self.find_candidates(
            mention
        )

        if candidates:

            ranked = self.rank_candidates(
                candidates,
                entity_label
            )

            selected = self.select_clinical_candidate(
                ranked,
                entity_label
            )

            if selected:
                return [selected]

        # --------------------------------------------------
        # 2. Try controlled lexical normalization.
        # --------------------------------------------------
        normalized_term = (
            self.lexical_normalizer.normalize(
                mention
            )
        )

        if normalized_term:

            candidates = self.find_candidates(
                normalized_term
            )

            if candidates:

                for candidate in candidates:
                    candidate["matchType"] = (
                        "lexical_normalization"
                    )

                ranked = self.rank_candidates(
                    candidates,
                    entity_label
                )

                selected = self.select_clinical_candidate(
                    ranked,
                    entity_label
                )

                if selected:
                    return [selected]

        # --------------------------------
        # Contained-term fallback
        # --------------------------------

        contained_terms = self.find_contained_terms(
            mention
        )

        if contained_terms:

            ranked = self.rank_contained_candidates(
                contained_terms,
                entity_label
            )

            selected = self.select_clinical_candidate(
                ranked,
                entity_label
            )

            if selected:
                selected["matchType"] = "contained_term"

                return [selected]

        return []

    def find_contained_terms(self, mention: str):

        normalized_mention = self.normalize_term(
            mention
        )

        tokens = normalized_mention.split()

        matches = []

        # Generate every contiguous phrase.
        for start in range(len(tokens)):

            for end in range(
                start + 1,
                len(tokens) + 1
            ):

                phrase = " ".join(
                    tokens[start:end]
                )

                concept_ids = (
                    self.term_to_concepts.get(
                        phrase
                    )
                )

                if concept_ids:

                    matches.append({
                        "term": phrase,
                        "conceptIds": concept_ids
                    })

        # Prefer longer terms first.
        matches.sort(
            key=lambda item: len(item["term"]),
            reverse=True
        )

        # Remove terms completely contained
        # in a longer matched term.
        filtered = []

        for candidate in matches:

            candidate_term = candidate["term"]

            is_contained = False

            for selected in filtered:

                selected_term = selected["term"]

                if re.search(
                    r"\b"
                    + re.escape(candidate_term)
                    + r"\b",
                    selected_term
                ):
                    is_contained = True
                    break

            if not is_contained:
                filtered.append(candidate)

        return filtered

    def is_descendant_of(
        self,
        concept_id: str,
        ancestor_id: str,
        max_depth: int = 20
    ) -> bool:

        current = {concept_id}
        visited = {concept_id}

        for _ in range(max_depth):

            next_level = set()

            for concept in current:

                for parent in self.parents.get(
                    concept,
                    set()
                ):

                    if parent == ancestor_id:
                        return True

                    if parent in visited:
                        continue

                    visited.add(parent)
                    next_level.add(parent)

            if not next_level:
                break

            current = next_level

        return False