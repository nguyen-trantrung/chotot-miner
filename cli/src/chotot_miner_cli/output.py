"""Output writers for scraped data."""

import csv
import sqlite3
from pathlib import Path
from typing import List
from abc import ABC, abstractmethod
from dataclasses import fields

from .listing import Listing


class Writer(ABC):
    def __init__(self, output_path: Path):
        self.output_path = output_path

    @abstractmethod
    def write(self, listings: List[Listing]) -> None:
        pass


class TSVWriter(Writer):

    def write(self, listings: List[Listing]) -> None:
        if not listings:
            return

        fieldnames = [field.name for field in fields(Listing)]

        with open(self.output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
            writer.writeheader()
            rows = [{k: getattr(listing, k) for k in fieldnames}
                    for listing in listings]
            writer.writerows(rows)


class SQLiteWriter(Writer):

    def write(self, listings: List[Listing]) -> None:
        if not listings:
            return

        conn = sqlite3.connect(self.output_path)
        cursor = conn.cursor()

        try:
            cursor.execute(Listing.sql_schema())

            for listing in listings:
                cursor.execute(listing.sql_insert())

            conn.commit()

        finally:
            conn.close()
