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

    DISCONTINUATION_PATTERNS = [
        r"\bstopped\s+(?:taking|using)\b",
        r"\bdiscontinued\b",
    ]

    HISTORICAL_PATTERNS = [
        r"\bhistory of\b",
        r"\bpreviously\b",
        r"\bprior history of\b",
    ]

    CLAUSE_BOUNDARIES = [
        r"\bbut\b",
        r"\bhowever\b",
        r"\balthough\b",
        r"\bwhile\b",
        r"\byet\b",
        r"\band now\b",
        r"\band currently\b",
        r"\band is currently\b",
        r"\bnow\b",
    ]

    def detect(
        self,
        text: str,
        entity_start: int
    ) -> str:

        context = text[:entity_start].lower()

        # Keep only the current clause.
        last_boundary = -1

        for pattern in self.CLAUSE_BOUNDARIES:

            matches = list(
                re.finditer(pattern, context)
            )

            if matches:
                boundary = matches[-1].start()

                if boundary > last_boundary:
                    last_boundary = boundary

        if last_boundary >= 0:
            context = context[last_boundary:]

        # Look at the local context before the entity.
        context = context[-60:]

        # Discontinuation
        for pattern in self.DISCONTINUATION_PATTERNS:

            if re.search(
                pattern + r"[\s\w]*$",
                context
            ):
                return "DISCONTINUED"

        # Historical
        for pattern in self.HISTORICAL_PATTERNS:

            if re.search(
                pattern + r"[\s\w]*$",
                context
            ):
                return "HISTORICAL"

        # Negation
        for pattern in self.NEGATION_PATTERNS:

            if re.search(
                pattern + r"[\s\w]*$",
                context
            ):
                return "ABSENT"

        return "PRESENT"