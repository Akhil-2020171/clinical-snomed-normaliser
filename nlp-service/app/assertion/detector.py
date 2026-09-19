import re


class AssertionDetector:

    # ==================================================
    # Assertion states
    # ==================================================

    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    HISTORICAL = "HISTORICAL"
    DISCONTINUED = "DISCONTINUED"
    UNCERTAIN = "UNCERTAIN"

    # ==================================================
    # Scope boundaries
    # ==================================================

    SENTENCE_BOUNDARIES = re.compile(
        r"[.!?;\n]"
    )

    CLAUSE_BOUNDARIES = re.compile(
        r"\b(?:"
        r"but|however|although|though|"
        r"while|whereas|yet|"
        r"and now|and currently|"
        r"now|currently"
        r")\b",
        re.IGNORECASE
    )

    # ==================================================
    # Discontinuation
    # ==================================================

    DISCONTINUATION_PATTERNS = [
        r"\bstopped\s+(?:taking|using)\b",
        r"\bdiscontinued\b",
        r"\bno\s+longer\s+(?:takes|taking|uses|using)\b",
        r"\bceased\s+(?:taking|using)\b",
        r"\bwithdrawn\b",
    ]

    RIGHT_DISCONTINUATION_PATTERNS = [
        r"\bstopped\s+(?:taking|using)\s+it\b",
        r"\bdiscontinued\s+it\b",
        r"\bno\s+longer\s+(?:taking|using)\s+it\b",
        r"\bceased\s+(?:taking|using)\s+it\b",
    ]

    # ==================================================
    # Historical
    # ==================================================

    HISTORICAL_PATTERNS = [
        r"\bhistory\s+of\b",
        r"\bhistory\s+with\b",
        r"\bpreviously\b",
        r"\bprior\s+history\s+of\b",
        r"\bpast\s+history\s+of\b",
        r"\bprevious\s+(?:episode|diagnosis|history)\s+of\b",
        r"\bremote\s+history\s+of\b",
    ]

    # Explicit temporal expressions
    NUMBER_WORDS = (
        r"(?:a|an|one|two|three|four|five|six|seven|eight|nine|ten|"
        r"eleven|twelve|\d+)"
    )

    PAST_TIME_PATTERN = (
        r"(?:"
        + NUMBER_WORDS +
        r"\s+(?:year|years|month|months|week|weeks|day|days)"
        r"|"
        r"yesterday"
        r"|"
        r"last\s+(?:year|month|week|day)"
        r"|"
        r"previous\s+(?:year|month|week|day)"
        r")"
        r"(?:\s+ago)?"
    )

    # ==================================================
    # Negation
    # ==================================================

    NEGATION_PATTERNS = [
        r"\bno\b",
        r"\bnot\b",
        r"\bdenies\b",
        r"\bdenied\b",
        r"\bwithout\b",
        r"\bnegative\s+for\b",
        r"\bnever\b",
        r"\bdoes\s+not\b",
        r"\bdo\s+not\b",
        r"\bdid\s+not\b",
        r"\bhas\s+not\b",
        r"\bhave\s+not\b",
        r"\bhad\s+not\b",
        r"\bdenies\s+any\b",
    ]

    # ==================================================
    # Uncertainty
    # ==================================================

    UNCERTAINTY_PATTERNS = [
        r"\bpossible\b",
        r"\bpossibly\b",
        r"\bprobable\b",
        r"\bprobably\b",
        r"\bsuspected\b",
        r"\bsuspicious\s+for\b",
        r"\bquestion\s+of\b",
        r"\brule\s+out\b",
        r"\br/o\b",
        r"\bmay\s+have\b",
        r"\bmight\s+have\b",
        r"\bcould\s+have\b",
        r"\bconsider\b",
        r"\bconcern\s+for\b",
        r"\bconcerned\s+about\b",
    ]

    # ==================================================
    # Questions
    # ==================================================

    QUESTION_PATTERNS = [
        r"\bdo\s+you\s+have\b",
        r"\bdoes\s+the\s+patient\s+have\b",
        r"\bdoes\s+she\s+have\b",
        r"\bdoes\s+he\s+have\b",
        r"\bare\s+you\s+experiencing\b",
        r"\bis\s+there\b",
        r"\bany\s+history\s+of\b",
        r"\bany\s+signs\s+of\b",
        r"\bany\s+symptoms\s+of\b",
    ]

    # ==================================================
    # Main detector
    # ==================================================

    def detect(
        self,
        text: str,
        entity_start: int,
        entity_end: int | None = None
    ) -> str:

        if entity_end is None:
            raise ValueError(
                "entity_end is required for assertion detection"
            )

        if entity_start < 0 or entity_end < entity_start:
            raise ValueError(
                "Invalid entity offsets"
            )

        if entity_end > len(text):
            raise ValueError(
                "entity_end is outside text"
            )

        # --------------------------------------------------
        # Build sentence-level context
        # --------------------------------------------------

        sentence_start = self._find_sentence_start(
            text,
            entity_start
        )

        sentence_end = self._find_sentence_end(
            text,
            entity_end
        )

        sentence_text = text[
            sentence_start:sentence_end
        ]

        local_start = entity_start - sentence_start
        local_end = entity_end - sentence_start

        before_entity = sentence_text[:local_start]
        after_entity = sentence_text[local_end:]

        entity = sentence_text[
            local_start:local_end
        ]

        # --------------------------------------------------
        # Build clause-level context
        # --------------------------------------------------

        clause_start = self._find_clause_start(
            before_entity
        )

        clause_end = self._find_clause_end(
            after_entity
        )

        left_clause = before_entity[
            clause_start:
        ]

        right_clause = after_entity[
            :clause_end
        ]

        # --------------------------------------------------
        # Entity-centered representation
        #
        # Example:
        #
        # He had [myocardial infarction] five years ago
        #
        # becomes:
        #
        # He had <ENTITY> five years ago
        #
        # This allows patterns spanning both sides
        # of the entity to be detected.
        # --------------------------------------------------

        entity_context = (
            left_clause
            + " <ENTITY> "
            + right_clause
        )

        # ==================================================
        # Priority 1: DISCONTINUED
        # ==================================================

        # Direct discontinuation before entity.
        if self._matches_any(
            left_clause,
            self.DISCONTINUATION_PATTERNS
        ):
            return self.DISCONTINUED

        # Coreference discontinuation after entity.
        #
        # Example:
        # aspirin was prescribed but stopped taking it
        #
        if self._matches_any(
            after_entity[:150],
            self.RIGHT_DISCONTINUATION_PATTERNS
        ):
            return self.DISCONTINUED

        # ==================================================
        # Priority 2: ABSENT
        # ==================================================

        if self._matches_negation(
            left_clause
        ):
            return self.ABSENT

        # ==================================================
        # Priority 3: QUESTION
        # ==================================================

        if self._is_question(
            sentence_text
        ):
            return self.UNCERTAIN

        # ==================================================
        # Priority 4: HISTORICAL
        # ==================================================

        # Standard historical terminology:
        #
        # history of diabetes
        # previously had pneumonia
        # prior history of hypertension
        #
        if self._matches_any(
            left_clause,
            self.HISTORICAL_PATTERNS
        ):
            return self.HISTORICAL

        # Explicit past event:
        #
        # He had <ENTITY> five years ago.
        #
        if self._is_historical_past_event(
            entity_context
        ):
            return self.HISTORICAL

        # ==================================================
        # Priority 5: UNCERTAIN
        # ==================================================

        if self._matches_any(
            left_clause,
            self.UNCERTAINTY_PATTERNS
        ):
            return self.UNCERTAIN

        if self._matches_any(
            right_clause,
            self.UNCERTAINTY_PATTERNS
        ):
            return self.UNCERTAIN

        # ==================================================
        # Default
        # ==================================================

        return self.PRESENT

    # ==================================================
    # Sentence helpers
    # ==================================================

    def _find_sentence_start(
        self,
        text: str,
        position: int
    ) -> int:

        previous_boundaries = [
            match.end()
            for match in self.SENTENCE_BOUNDARIES.finditer(
                text[:position]
            )
        ]

        if not previous_boundaries:
            return 0

        return previous_boundaries[-1]

    def _find_sentence_end(
        self,
        text: str,
        position: int
    ) -> int:

        match = self.SENTENCE_BOUNDARIES.search(
            text,
            position
        )

        if not match:
            return len(text)

        return match.start()

    # ==================================================
    # Clause helpers
    # ==================================================

    def _find_clause_start(
        self,
        text: str
    ) -> int:

        matches = list(
            self.CLAUSE_BOUNDARIES.finditer(text)
        )

        if not matches:
            return max(0, len(text) - 150)

        return matches[-1].end()

    def _find_clause_end(
        self,
        text: str
    ) -> int:

        match = self.CLAUSE_BOUNDARIES.search(
            text
        )

        if not match:
            return min(len(text), 150)

        return match.start()

    # ==================================================
    # Pattern helpers
    # ==================================================

    def _matches_any(
        self,
        text: str,
        patterns
    ) -> bool:

        for pattern in patterns:
            if re.search(
                pattern,
                text,
                re.IGNORECASE
            ):
                return True

        return False

    # ==================================================
    # Negation
    # ==================================================

    def _matches_negation(
        self,
        text: str
    ) -> bool:

        for pattern in self.NEGATION_PATTERNS:

            if re.search(
                pattern,
                text,
                re.IGNORECASE
            ):
                return True

        return False

    # ==================================================
    # Questions
    # ==================================================

    def _is_question(
        self,
        sentence_text: str
    ) -> bool:

        # Explicit question mark.
        if "?" in sentence_text:
            return True

        # Clinical question phrases.
        return self._matches_any(
            sentence_text,
            self.QUESTION_PATTERNS
        )

    # ==================================================
    # Historical temporal events
    # ==================================================

    def _is_historical_past_event(
        self,
        entity_context: str
    ) -> bool:

        # ----------------------------------------------
        # Pattern:
        #
        # had <ENTITY> five years ago
        # had <ENTITY> two months ago
        # had <ENTITY> yesterday
        # had <ENTITY> last year
        # ----------------------------------------------

        pattern = (
            r"\bhad\s+"
            r"<ENTITY>"
            r"\s+"
            + self.PAST_TIME_PATTERN
            + r"\b"
        )

        if re.search(
            pattern,
            entity_context,
            re.IGNORECASE
        ):
            return True

        # ----------------------------------------------
        # Pattern:
        #
        # previously had <ENTITY>
        # previously experienced <ENTITY>
        # ----------------------------------------------

        previous_pattern = (
            r"\bpreviously\s+"
            r"(?:had|experienced|suffered\s+from)"
            r"\s+"
            r"<ENTITY>"
            r"\b"
        )

        if re.search(
            previous_pattern,
            entity_context,
            re.IGNORECASE
        ):
            return True

        return False