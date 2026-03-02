from typing import List, Optional, TYPE_CHECKING, Set, Dict, Any
import time
import uuid
import httpx
import json
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.console import Console

from .listing import Listing

from .output import SQLiteWriter


class ChototScraper:
    def __init__(self, url: str, writer: Optional[SQLiteWriter] = None, recursion_depth: int = 2, max_workers: int = 10):
        self.url = url
        self.writer = writer
        self.recursion_depth = recursion_depth
        self.max_workers = max_workers
        self.console = Console(highlight=False, markup=False)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        self.scraped_listing_ids: Set[str] = set()
        self._scraped_ids_lock = threading.Lock()
        self._fingerprint = str(uuid.uuid4())
        self._pending_listings: List[Listing] = []
        self._pending_lock = threading.Lock()

    def scrape(self, count: Optional[int] = 1000, checkpoint_interval: int = 100) -> List[Listing]:
        listings = []
        count = count if count else 1000
        i = count
        page_num = 1

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            while i > 0:
                time.sleep(0.1)

                page_html = self._fetch_page(page_num)

                listings_from_page = self._extract_listings(
                    page_html, page_num)
                num_listings = len(listings_from_page)

                if num_listings == 0:
                    self.console.log(
                        f"No listings found on page {page_num}. Stopping.")
                    break

                # Fetch listing details in parallel for all listings on this page
                futures: Dict[Any, Listing] = {}
                for listing in listings_from_page:
                    with self._scraped_ids_lock:
                        if listing.listing_id in self.scraped_listing_ids:
                            continue
                        self.scraped_listing_ids.add(listing.listing_id)
                    futures[executor.submit(
                        self._fetch_listing_details, listing, 0)] = listing

                for future in as_completed(futures):
                    try:
                        future.result()
                    except Exception as e:
                        failed = futures[future]
                        self.console.log(
                            f"[ERROR] Detail fetch failed for {failed.listing_id}: {e}")

                i -= num_listings
                listings.extend(listings_from_page)

                self.console.log(
                    f"({len(listings)}/{count}) Scraped {num_listings} listings from page {page_num}")

                if self.writer and len(listings) % checkpoint_interval == 0:
                    with self._pending_lock:
                        to_flush = self._pending_listings[:]
                        self._pending_listings.clear()
                    seen: Dict[str, Listing] = {}
                    for l in to_flush:
                        seen[l.listing_id] = l
                    to_flush = list(seen.values())
                    self.console.log(
                        f"[CHECKPOINT] Flushing {len(to_flush)} listings to DB...")
                    self.writer.write(to_flush)

                page_num += 1

        # Final flush of any remaining buffered listings
        if self.writer:
            with self._pending_lock:
                to_flush = self._pending_listings[:]
                self._pending_listings.clear()
            if to_flush:
                seen: Dict[str, Listing] = {}
                for l in to_flush:
                    seen[l.listing_id] = l
                to_flush = list(seen.values())
                self.console.log(
                    f"[FLUSH] Flushing {len(to_flush)} remaining listings to DB...")
                self.writer.write(to_flush)

        return listings

    def _fetch_page(self, number: int) -> str:
        page_url = f"{self.url}?page={number}"

        with httpx.Client(headers=self.headers, timeout=30.0, follow_redirects=True) as client:
            response = client.get(page_url)
            response.raise_for_status()
            return response.text

    def _extract_listings(self, page: str, page_num: int) -> List[Listing]:
        try:
            match = re.search(
                r'<script id="__NEXT_DATA__"\s+type="application/json">({.*?})</script>',
                page,
                re.DOTALL
            )

            if not match:
                self.console.log(
                    f"[WARNING] No __NEXT_DATA__ found on page {page_num}")
                return []

            json_str = match.group(1)
            data = json.loads(json_str)

            ads = (data.get('props', {})
                   .get('initialState', {})
                   .get('adlisting', {})
                   .get('data', {})
                   .get('ads', []))

            if not ads:
                self.console.log(
                    f"[WARNING] No ads found in data on page {page_num}")
                return []

            listings = []
            for ad in ads:
                listing = Listing(
                    listing_id=str(ad.get('list_id', '')),
                    title=ad.get('subject', ''),
                    price=ad.get('price'),
                    location=f"{ad.get('region_name', '')}, {ad.get('area_name', '')}",
                    description=ad.get('body', ''),
                    url=f"https://www.chotot.com/{ad.get('category_name', '').lower().replace(' ', '-')}/{ad.get('list_id', '')}.htm" if ad.get(
                        'list_id') else ""
                )
                listings.append(listing)

            return listings

        except json.JSONDecodeError as e:
            self.console.log(
                f"[ERROR] Failed to parse JSON on page {page_num}: {e}")
            return []
        except Exception as e:
            self.console.log(
                f"[ERROR] Failed to extract listings on page {page_num}: {e}")
            return []

    def _fetch_listing_page(self, url: str) -> str:
        time.sleep(0.2)  # Rate limiting
        with httpx.Client(headers=self.headers, timeout=30.0, follow_redirects=True) as client:
            response = client.get(url)
            response.raise_for_status()
            return response.text

    def _fetch_similar_ads(self, ad_id: str) -> List[Dict[str, Any]]:
        """Fetch similar ads from the recommender API (both similar_type=0 and 1 in parallel)."""
        results: Dict[str, Dict[str, Any]] = {}
        results_lock = threading.Lock()

        def _fetch_one(similar_type: int) -> None:
            try:
                url = (
                    f"https://gateway.chotot.com/v1/public/recommender/ad"
                    f"?ad_id={ad_id}&fingerprint={self._fingerprint}"
                    f"&similar_type={similar_type}&limit=20&page=1"
                )
                with httpx.Client(headers=self.headers, timeout=30.0) as client:
                    response = client.get(url)
                    response.raise_for_status()
                    ads = response.json().get('data', [])
                with results_lock:
                    for ad in ads:
                        results[str(ad.get('list_id', ad.get('ad_id', '')))] = ad
            except Exception as e:
                self.console.log(
                    f"[ERROR] Failed to fetch similar ads (type={similar_type}) for {ad_id}: {e}")

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(_fetch_one, t) for t in (0, 1)]
            for f in as_completed(futures):
                f.result()

        return list(results.values())

    def _extract_listing_details(self, page_html: str) -> Dict[str, Any]:
        try:
            match = re.search(
                r'<script id="__NEXT_DATA__"\s+type="application/json">({.*?})</script>',
                page_html,
                re.DOTALL
            )

            if not match:
                return {'features': [], 'owner_type': None}

            data = json.loads(match.group(1))
            state = data.get('props', {}).get('initialState', {})

            features = []
            adinfo = state.get('adView', {}).get('adInfo', {})
            if 'parameters' in adinfo:
                features = adinfo['parameters']

            # Detect owner type from href links in the page HTML
            owner_type = None
            if re.search(r'href=["\']https?://[^"\']*/cua-hang/', page_html):
                owner_type = 'STORE'
            elif re.search(r'href=["\']https?://[^"\']*/user/', page_html):
                owner_type = 'USER'

            return {'features': features, 'owner_type': owner_type}

        except Exception as e:
            self.console.log(f"[ERROR] Failed to extract listing details: {e}")
            return {'features': [], 'owner_type': None}

    def _fetch_listing_details(self, listing: Listing, current_depth: int):
        try:
            if not listing.url:
                return

            self.console.log(
                f"[DETAILS] Fetching listing {listing.listing_id} (depth {current_depth})")

            page_html = self._fetch_listing_page(listing.url)
            details = self._extract_listing_details(page_html)

            if details['features']:
                listing.features = json.dumps(
                    details['features'], ensure_ascii=False)

            if details.get('owner_type'):
                listing.owner_type = details['owner_type']

            if self.writer:
                with self._pending_lock:
                    self._pending_listings.append(listing)

            # Recursively fetch and process similar ads
            if current_depth < self.recursion_depth:
                similar_ads = self._fetch_similar_ads(listing.listing_id)

                if similar_ads:
                    self.console.log(
                        f"[SIMILAR] {len(similar_ads)} similar ads for {listing.listing_id} (depth {current_depth})")

                for ad in similar_ads:
                    listing_id = str(ad.get('list_id', ''))
                    if not listing_id:
                        continue

                    with self._scraped_ids_lock:
                        if listing_id in self.scraped_listing_ids:
                            continue
                        self.scraped_listing_ids.add(listing_id)

                    similar_listing = Listing(
                        listing_id=listing_id,
                        title=ad.get('subject', ''),
                        price=ad.get('price'),
                        location=f"{ad.get('region_name', '')}, {ad.get('area_name', '')}",
                        description=ad.get('body', ''),
                        url=f"https://www.chotot.com/{ad.get('category_name', '').lower().replace(' ', '-')}/{listing_id}.htm"
                    )

                    self._fetch_listing_details(
                        similar_listing, current_depth + 1)

        except Exception as e:
            self.console.log(
                f"[ERROR] Failed to fetch details for listing {listing.listing_id}: {e}")
