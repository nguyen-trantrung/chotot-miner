from dataclasses import dataclass
from typing import Optional
import json as json_module
from pypika import Table
from pypika.dialects import SQLLiteQuery


@dataclass
class Listing:
    listing_id: str
    title: str
    price: Optional[int]
    location: str
    description: str
    url: str
    features: Optional[str] = None  # JSON string

    @staticmethod
    def sql_schema() -> str:
        listings_table = Table('listings')

        columns = [
            "id INTEGER PRIMARY KEY AUTOINCREMENT",
            "listing_id TEXT UNIQUE",
            "title TEXT",
            "price INTEGER",
            "location TEXT",
            "description TEXT",
            "url TEXT",
            "features TEXT",
            "scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
        ]

        return f"CREATE TABLE IF NOT EXISTS {listings_table.get_sql()} (\n    {',\n    '.join(columns)}\n)"

    def sql_insert(self) -> str:
        listings_table = Table('listings')

        query = SQLLiteQuery \
            .into(listings_table) \
            .columns(
                'listing_id', 'title', 'price', 'location', 'description', 'url', 'features'
            ).insert(
                self.listing_id,
                self.title,
                self.price,
                self.location,
                self.description,
                self.url,
                self.features
            )

        query_str = str(query)
        query_str = query_str.replace('INSERT INTO', 'INSERT OR REPLACE INTO')

        return query_str
