from typing import List, Optional
import time
from rich.progress import Progress, SpinnerColumn, TextColumn

from .listing import Listing


class ChototScraper:
    def __init__(self, url: str):
        self.url = url

    def scrape(self, count: Optional[int] = 1000) -> List[Listing]:
        listings = []
        count = count if count else 1000

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            task = progress.add_task("Scraping...", total=count)

            for i in range(count):
                time.sleep(0.1)

                listing = Listing(
                    listing_id=f"listing_{i+1}",
                    title=f"Sample Title {i+1}",
                    price=f"{(i+1) * 1000000} đ",
                    location="Ho Chi Minh City",
                    description=f"Sample description for listing {i+1}",
                    url=f"{self.url}/listing_{i+1}",
                )

                listings.append(listing)
                progress.update(task, completed=len(listings))

        return listings
