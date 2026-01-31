"""Web scraper for Chotot.vn."""

import httpx
from bs4 import BeautifulSoup
from typing import List, Dict, Any
import time
from rich.progress import Progress, SpinnerColumn, TextColumn


class ChototScraper:
    """Scraper for Chotot.vn listings."""
    
    def __init__(self, url: str):
        """Initialize scraper with base URL."""
        self.url = url
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
    
    def scrape(self, count: int) -> List[Dict[str, Any]]:
        """
        Scrape listings from Chotot.vn.
        
        Args:
            count: Number of listings to scrape
            
        Returns:
            List of listing dictionaries
        """
        listings = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            task = progress.add_task("Scraping...", total=count)
            
            with httpx.Client(headers=self.headers, timeout=30.0) as client:
                page = 1
                
                while len(listings) < count:
                    # Construct pagination URL
                    page_url = f"{self.url}?page={page}"
                    
                    try:
                        response = client.get(page_url)
                        response.raise_for_status()
                        
                        # Parse HTML
                        soup = BeautifulSoup(response.text, "lxml")
                        
                        # Extract listings (this is a placeholder - actual selectors depend on Chotot's HTML structure)
                        # You'll need to inspect the actual website and update these selectors
                        items = soup.select(".AdItem_wrapperAdItem__FpU1x")  # Example selector
                        
                        if not items:
                            # No more items found
                            break
                        
                        for item in items:
                            if len(listings) >= count:
                                break
                            
                            listing = self._parse_listing(item)
                            if listing:
                                listings.append(listing)
                                progress.update(task, completed=len(listings))
                        
                        page += 1
                        
                        # Be nice to the server
                        time.sleep(1)
                        
                    except Exception as e:
                        print(f"Error scraping page {page}: {e}")
                        break
        
        return listings[:count]
    
    def _parse_listing(self, item) -> Dict[str, Any]:
        """
        Parse a single listing item.
        
        Note: These selectors are placeholders. You need to inspect
        the actual Chotot.vn website and update them accordingly.
        """
        try:
            # Example parsing - update with actual selectors
            listing_id = item.get("data-id", "")
            
            title_elem = item.select_one(".AdItem_adTitle__d6naj")
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            price_elem = item.select_one(".AdItem_price__d4YvZ")
            price_text = price_elem.get_text(strip=True) if price_elem else ""
            
            location_elem = item.select_one(".AdItem_adLocation__Bv7WL")
            location = location_elem.get_text(strip=True) if location_elem else ""
            
            description_elem = item.select_one(".AdItem_adDescription__qhzjq")
            description = description_elem.get_text(strip=True) if description_elem else ""
            
            # Extract URL
            link_elem = item.select_one("a[href]")
            url = link_elem.get("href", "") if link_elem else ""
            if url and not url.startswith("http"):
                url = f"https://www.chotot.com{url}"
            
            return {
                "listing_id": listing_id,
                "title": title,
                "price": price_text,
                "location": location,
                "description": description,
                "url": url,
            }
        except Exception as e:
            print(f"Error parsing listing: {e}")
            return None
