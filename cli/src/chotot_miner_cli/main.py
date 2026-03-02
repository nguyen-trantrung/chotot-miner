"""Main CLI entry point."""

import click
from pathlib import Path
from prettytable import PrettyTable

from chotot_miner_cli.scraper import ChototScraper
from chotot_miner_cli.output import SQLiteWriter


@click.group()
@click.version_option(version="0.1.0")
def cli():
    pass


@cli.command()
@click.option(
    "--url",
    required=True,
    help="URL to scrape (e.g., https://www.chotot.com/mua-ban-dien-thoai)",
)
@click.option(
    "--count",
    type=int,
    default=100,
    help="Number of listings to scrape (default: 100)",
)
@click.option(
    "--output-file",
    type=click.Path(),
    help="Output file path (default: output.db)",
)
@click.option(
    "--recursion-depth",
    type=int,
    default=2,
    help="Recursion depth for similar products (default: 2)",
)
@click.option(
    "--workers",
    type=int,
    default=10,
    help="Number of parallel workers for fetching listing details (default: 10)",
)
def run(url: str, count: int, output_file: str, recursion_depth: int, workers: int):

    if not output_file:
        output_file = "output.db"

    table = PrettyTable()
    table.field_names = ["Setting", "Value"]
    table.header = False
    table.align["Setting"] = "l"
    table.align["Value"] = "l"
    table.add_row(["URL", url])
    table.add_row(["Count", count])
    table.add_row(["Recursion depth", recursion_depth])
    table.add_row(["Workers", workers])
    click.echo(table)
    click.echo()
    try:
        writer = SQLiteWriter(Path(output_file))

        scraper = ChototScraper(
            url, writer=writer, recursion_depth=recursion_depth, max_workers=workers)

        listings = scraper.scrape(count)

        click.echo()
        click.echo(f"Successfully scraped {len(listings)} listings")
        click.echo("Normalizing features into columns...")
        writer.normalize_features()

        click.echo(f"Data saved to {output_file}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.argument("db_file", type=click.Path(exists=True, path_type=Path))
def normalize(db_file: Path):
    """Normalize the features column of a scraped SQLite DB into flat columns."""
    try:
        writer = SQLiteWriter(db_file)
        click.echo(f"Normalizing features in {db_file}...")
        writer.normalize_features()
        click.echo("Done.")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


if __name__ == "__main__":
    cli()
