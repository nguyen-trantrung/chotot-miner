"""Output writers for scraped data."""

import sqlite3
from pathlib import Path
from typing import List

from .listing import Listing


class SQLiteWriter:

    def __init__(self, output_path: Path):
        self.output_path = output_path
        conn = sqlite3.connect(self.output_path)
        cursor = conn.cursor()
        cursor.execute(Listing.sql_schema())
        conn.commit()
        conn.close()

    def write(self, listings: List[Listing]) -> None:
        if not listings:
            return

        conn = sqlite3.connect(self.output_path)
        cursor = conn.cursor()

        try:
            listing_ids = [listing.listing_id for listing in listings]
            placeholders = ','.join('?' * len(listing_ids))
            cursor.execute(
                f"SELECT listing_id FROM listings WHERE listing_id IN ({placeholders})",
                listing_ids
            )
            existing_ids = {row[0] for row in cursor.fetchall()}

            new_listings = [
                listing for listing in listings
                if listing.listing_id not in existing_ids
            ]

            if new_listings:
                # Batch insert new listings
                insert_data = [
                    (
                        listing.listing_id,
                        listing.title,
                        listing.price,
                        listing.location,
                        listing.description,
                        listing.url,
                        listing.features
                    )
                    for listing in new_listings
                ]

                cursor.executemany(
                    """INSERT OR REPLACE INTO listings 
                       (listing_id, title, price, location, description, url, features) 
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    insert_data
                )

            conn.commit()

            inserted_count = len(new_listings)
            skipped_count = len(existing_ids)

            if inserted_count > 0 or skipped_count > 0:
                print(
                    f"[DB] Inserted: {inserted_count}, Skipped (duplicates): {skipped_count}")

        finally:
            conn.close()

    def normalize_features(self) -> None:
        """Expand the features JSON column into individual columns."""
        import json

        conn = sqlite3.connect(self.output_path)
        cursor = conn.cursor()

        try:
            # Fetch all rows that have features
            cursor.execute(
                "SELECT listing_id, features FROM listings WHERE features IS NOT NULL")
            rows = cursor.fetchall()

            if not rows:
                print("[NORMALIZE] No features to normalize.")
                return

            # Discover all unique feature IDs across all rows
            all_feature_ids: set = set()
            parsed: dict = {}
            for listing_id, features_json in rows:
                try:
                    features = json.loads(features_json)
                    feature_map = {f['id']: f['value']
                                   for f in features if 'id' in f and 'value' in f}
                    parsed[listing_id] = feature_map
                    all_feature_ids.update(feature_map.keys())
                except (json.JSONDecodeError, TypeError):
                    pass

            if not all_feature_ids:
                print("[NORMALIZE] No feature fields found.")
                return

            # Get existing columns
            cursor.execute("PRAGMA table_info(listings)")
            existing_columns = {row[1] for row in cursor.fetchall()}

            # Add missing columns
            new_columns = all_feature_ids - existing_columns
            for col in new_columns:
                cursor.execute(f'ALTER TABLE listings ADD COLUMN "{col}" TEXT')

            # Update each row
            for listing_id, feature_map in parsed.items():
                for col, value in feature_map.items():
                    cursor.execute(
                        f'UPDATE listings SET "{col}" = ? WHERE listing_id = ?',
                        (value, listing_id)
                    )

            conn.commit()
            cursor.execute('ALTER TABLE listings DROP COLUMN "features"')
            conn.commit()
            print(
                f"[NORMALIZE] Expanded {len(all_feature_ids)} feature columns across {len(parsed)} listings.")

        finally:
            conn.close()
