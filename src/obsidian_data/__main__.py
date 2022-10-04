"""Command-line interface."""
import click


@click.command()
@click.version_option()
def main() -> None:
    """Obsidian Data."""


if __name__ == "__main__":
    main(prog_name="obsidian-data")  # pragma: no cover
