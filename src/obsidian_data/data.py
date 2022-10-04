"""Parses data in different formats from gmail emails."""
import re

from .base import Base


class DataParser(Base):
    """Parse data from Gmail."""

    URL_PATTERN = "https?:\\/\\/(?:www\\.)?[-a-zA-Z0-9@:%._\\+~#=]{1,256}\\.[a-zA-Z0-9()]{1,6}\\b(?:[-a-zA-Z0-9()@:%_\\+.~#?&\\/=]*)"

    def get_url(self, text: str) -> str:
        return re.findall(self.URL_PATTERN, text)
