from __future__ import annotations

import json
import re

from dataclasses import dataclass
from typing import Literal, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from models.db import BookDB

@dataclass
class Identifiers:
    isbn_13: list
    openlibrary: list

class Book:
    def __init__(self, payload: BookDB):
        self.__payload = payload
        # JSONB columns are returned as Python dict/list; Text cover as a string.
        self.__identifiers = payload.identifiers if isinstance(payload.identifiers, dict) else json.loads(payload.identifiers)
        self._publishers = payload.publishers if isinstance(payload.publishers, list) else json.loads(payload.publishers)
        self._authors = payload.authors if isinstance(payload.authors, list) else json.loads(payload.authors)
        self._cover = payload.cover if isinstance(payload.cover, dict) else json.loads(payload.cover)
        
        try:
            print(self.__identifiers)
            self.__identifiers.pop("isbn_10", None)
            self.__identifiers.pop("wikidata", None)
            self.__identifiers.pop("lccn", None)
            self.__identifiers.pop("oclc", None)
        except KeyError:
            print("error")
            pass


    def __repr__(self):
        return self.title
    
    @property
    def isbn(self):
        return self.__payload.isbn
    
    @classmethod
    def from_books(cls, isbn: str, books: list):  
        return [book for book in books if book.identifiers.isbn_13[0] == isbn][0]

    @property
    def url(self):
        return self.__payload.url
    
    @property
    def emoji(self):
        return self.__payload.emoji

    @property
    def publishers(self):
        return self._publishers

    @property
    def published(self):
        return self.__payload.publish_date

    @property
    def published_year(self):
        date = self.published.split(" ")
        return date[2] if len(date) > 1 else date[0]

    @property
    def title(self):
        return self.__payload.title

    @property
    def description(self):
        output = self.__payload.description or "*No description provided.*"
        output = output.replace("\\r\\n", "\n").replace("\\n", "\n")
        # Decode any literal \uXXXX escape sequences without corrupting existing UTF-8 characters
        output = re.sub(r'\\u([0-9a-fA-F]{4})', lambda m: chr(int(m.group(1), 16)), output)
        return output
    
    @property
    def authors(self):
        return self._authors

    @property
    def main_author(self):
        return self.authors[0]["name"] if self.authors else "*Author not provided*"

    @property
    def main_author_olid(self):
        return self.authors[0]["url"].split("/")[4] if self.authors else "OLID"
    
    @property
    def identifiers(self):
        return Identifiers(**self.__identifiers)
    
    @property
    def available(self):
        return self.__payload.available

    def get_cover_url(self, size: Literal["small", "medium", "large"]):
        cover = self._cover
        return cover if isinstance(cover, str) else cover[size]

    def get_author_image_url(self, size: Literal["small", "medium", "large"]):
        match size:
            case "small":
                size = "S"
            case "medium":
                size = "M"
            case "large":
                size = "L"
            case _:
                ...

        return f"https://covers.openlibrary.org/a/olid/{self.main_author_olid}-{size}.jpg"