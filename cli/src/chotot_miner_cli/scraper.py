from typing import List, Optional, TYPE_CHECKING
import time
from rich.console import Console

from .listing import Listing

if TYPE_CHECKING:
    from .output import Writer


class ChototScraper:
    def __init__(self, url: str, writer: Optional['Writer'] = None):
        self.url = url
        self.writer = writer
        self.console = Console(highlight=False, markup=False)

    def scrape(self, count: Optional[int] = 1000, checkpoint_interval: int = 100) -> List[Listing]:
        listings = []
        count = count if count else 1000

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

            self.console.log(
                f"({len(listings)}/{count}) Scraped: {listing.listing_id} - {listing.title}")

            if self.writer and len(listings) % checkpoint_interval == 0:
                self.console.log(
                    f"[CHECKPOINT] Saving {len(listings)} listings...")
                self.writer.write(listings)

        return listings
