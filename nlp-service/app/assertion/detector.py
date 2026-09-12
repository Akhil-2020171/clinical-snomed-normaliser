import re


class AssertionDetector:

    NEGATION_PATTERNS = [
        r"\bno\b",
        r"\bnot\b",
        r"\bdenies\b",
        r"\bdenied\b",
        r"\bwithout\b",
        r"\bnegative for\b",
    ]

    def detect(
        self,
        text: str,
        entity_start: int
    ) -> str:

        context = text[:entity_start].lower()

        # Look at the last ~60 characters before
        # the entity.
        context = context[-60:]

        for pattern in self.NEGATION_PATTERNS:

            if re.search(
                pattern + r"[\s\w]*$",
                context
            ):
                return "ABSENT"

        return "PRESENT"