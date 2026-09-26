"""Query shape checks and controls that do not depend on matching sensitive text."""


class SecurityService:
    MAX_QUERY_CHARS = 2000

    def normalise_query(self, value: object) -> str | None:
        if not isinstance(value, str):
            return None
        question = value.strip()
        return question if question and len(question) <= self.MAX_QUERY_CHARS else None

    def controls_for_query(self) -> list[str]:
        # The audit event never receives query text, regardless of its contents.
        return ["audit-metadata-only"]
