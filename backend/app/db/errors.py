"""Database-layer exceptions mapped to HTTP responses in API routes."""


class DuplicateOrganizationError(Exception):
    """Raised when an organization name already exists (case-insensitive)."""

    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(f"Organization with name '{name}' already exists")
