"""Main CLI entry point."""

import click
from pathlib import Path

from chotot_miner_cli.scraper import ChototScraper
from chotot_miner_cli.output import TSVWriter, SQLiteWriter


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Chotot Miner - Web scraping tool for Chotot.vn"""
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
    """Scrape listings from Chotot.vn and save to file."""
    
    click.echo(f"Starting Chotot Miner...")
    click.echo(f"URL: {url}")
    click.echo(f"Count: {count}")
    click.echo(f"Output format: {output}")
    
    # Set default output file if not provided
    if not output_file:
        output_file = f"output.{output}" if output == "tsv" else "output.db"
    
    output_path = Path(output_file)
    
    try:
        # Initialize scraper
        scraper = ChototScraper(url)
        
        # Scrape listings
        click.echo(f"\nScraping {count} listings...")
        listings = scraper.scrape(count)
        
        click.echo(f"Successfully scraped {len(listings)} listings")
        
        # Write output
        click.echo(f"Writing to {output_path}...")
        
        if output == "tsv":
            writer = TSVWriter(output_path)
        else:
            writer = SQLiteWriter(output_path)
        
        writer.write(listings)
        
        click.echo(f"✓ Data saved to {output_path}")
        
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        raise click.Abort()


if __name__ == "__main__":
    cli()
