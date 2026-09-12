class LexicalNormalizer:

    NORMALIZATIONS = {
        "diabetes": "diabetes mellitus"
    }

    def normalize(self, term: str) -> str | None:
        normalized = term.lower().strip()

        return self.NORMALIZATIONS.get(
            normalized
        )