"""Main CLI entry point."""

import click
from pathlib import Path
from prettytable import PrettyTable

from chotot_miner_cli.scraper import ChototScraper
from chotot_miner_cli.output import TSVWriter, SQLiteWriter


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
    "--output",
    type=click.Choice(["tsv", "sqlite"], case_sensitive=False),
    default="tsv",
    help="Output format (default: tsv)",
)
@click.option(
    "--output-file",
    type=click.Path(),
    help="Output file path (default: output.tsv or output.db)",
)
def run(url: str, count: int, output: str, output_file: str):

    if not output_file:
        output_file = f"output.{output}" if output == "tsv" else "output.db"

    table = PrettyTable()
    table.field_names = ["Setting", "Value"]
    table.header = False
    table.align["Setting"] = "l"
    table.align["Value"] = "l"
    table.add_row(["URL", url])
    table.add_row(["Count", count])
    table.add_row(["Output format", output])
    click.echo(table)
    click.echo()
    try:
        if output == "tsv":
            writer = TSVWriter(Path(output_file))
        else:
            writer = SQLiteWriter(Path(output_file))

        scraper = ChototScraper(url, writer=writer)

        listings = scraper.scrape(count)

        click.echo()
        click.echo(f"Successfully scraped {len(listings)} listings")

        click.echo(f"Writing final data to {output_file}...")
        writer.write(listings)

        click.echo(f"Data saved to {output_file}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


if __name__ == "__main__":
    cli()
