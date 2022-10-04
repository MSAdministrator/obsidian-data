"""Used to build and parse obsidian data."""
from .base import Base
from .gmail import Gmail
from .data import DataParser


class Obsidian(Base):
    """Main entry point."""

    def generate_markdown_file(self) -> str:
        """Generates markdown file of links from gmail emails."""
        text_file = ""
        gmail = Gmail()
        data_parser = DataParser()
        for email in gmail.get_messages(query="label:_links", include_attachments=False):
            if email and email.get("body") and email["body"]:
                data = data_parser.get_url(email["body"])
                if data:
                    for item in data:
                        if email.get("subject") and email["subject"]:
                            text_file += f"* [{email['subject']}]({item})\n"
        return text_file
