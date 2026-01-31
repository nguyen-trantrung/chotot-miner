"""Output writers for scraped data."""

import csv
import sqlite3
from pathlib import Path
from typing import List, Dict, Any
from abc import ABC, abstractmethod


class Writer(ABC):
    """Abstract base class for output writers."""
    
    def __init__(self, output_path: Path):
        """Initialize writer with output path."""
        self.output_path = output_path
    
    @abstractmethod
    def write(self, listings: List[Dict[str, Any]]) -> None:
        """Write listings to output."""
        pass


class TSVWriter(Writer):
    """TSV (Tab-Separated Values) file writer."""
    
    def write(self, listings: List[Dict[str, Any]]) -> None:
        """Write listings to TSV file."""
        if not listings:
            return
        
        # Get all keys from all listings
        fieldnames = set()
        for listing in listings:
            fieldnames.update(listing.keys())
        
        fieldnames = sorted(fieldnames)
        
        with open(self.output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
            writer.writeheader()
            writer.writerows(listings)


class SQLiteWriter(Writer):
    """SQLite database writer."""
    
    def write(self, listings: List[Dict[str, Any]]) -> None:
        """Write listings to SQLite database."""
        if not listings:
            return
        
        # Connect to database
        conn = sqlite3.connect(self.output_path)
        cursor = conn.cursor()
        
        try:
            # Create table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS listings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    listing_id TEXT UNIQUE,
                    title TEXT,
                    price TEXT,
                    location TEXT,
                    description TEXT,
                    url TEXT,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Insert listings
            for listing in listings:
                cursor.execute("""
                    INSERT OR REPLACE INTO listings 
                    (listing_id, title, price, location, description, url)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    listing.get("listing_id", ""),
                    listing.get("title", ""),
                    listing.get("price", ""),
                    listing.get("location", ""),
                    listing.get("description", ""),
                    listing.get("url", ""),
                ))
            
            conn.commit()
            
        finally:
            conn.close()
