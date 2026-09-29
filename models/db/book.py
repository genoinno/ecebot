import json

from .db import Base
from models.book import Book
from sqlalchemy import Column, Integer, String, Text, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

class BookDB(Base):
    __tablename__ = 'books'
    isbn = Column(String(15), primary_key=True)

    identifiers = Column(JSONB)       # {"Openlib": "...", "ISBN_13": "..."}

    available = Column(Integer)

    url = Column(String(255))
    emoji = Column(String(10))        # stores an emoji character
    publish_date = Column(String(50))
    title = Column(String(255))
    description = Column(Text)        # PostgreSQL TEXT has no length limit
    cover = Column(JSONB)              # JSON dict of cover URLs {small, medium, large}

    # JSONB arrays
    publishers = Column(JSONB)        # ["Publisher A", "Publisher B"]
    authors = Column(JSONB)           # ["Author A", "Author B"]

    borrow_records = relationship("BorrowingRecordDB", back_populates="book")

    @staticmethod
    async def add(session, emoji, json_payload):
        book = BookDB(
            isbn=json_payload["isbns"][0],
            identifiers=json_payload["data"]["identifiers"],   # JSONB: pass dict directly
            available=1,
            url=json_payload["data"]["url"],
            emoji=emoji,
            publish_date=json_payload["publishDates"][0],
            title=json_payload["data"]["title"],
            description=json_payload["details"]["details"]["description"]["value"],
            cover=json_payload["data"]["cover"],           # JSONB: pass dict directly
            publishers=json_payload["details"]["details"]["publishers"],  # JSONB: pass list directly
            authors=json_payload["data"]["authors"]             # JSONB: pass list directly
        )
        
        session.add(book)   
        await session.commit()
    
    @staticmethod
    async def get_by_id(session, isbn, parse_to_book):
        book = (await session.execute(select(BookDB).where(BookDB.isbn == isbn))).scalar()
        if parse_to_book:
            return Book(book)
        return book
    
    @staticmethod
    async def get_allowed_books(session, parse_to_book):
        books = (await session.execute(select(BookDB).where(BookDB.available == 1))).scalars().all()
        if parse_to_book:
            return [Book(book) for book in books]
        return books
    
    @staticmethod
    async def get_all(session, parse_to_book):
        books = (await session.execute(select(BookDB))).scalars().all()
        if parse_to_book:
            return [Book(book) for book in books]
        return books

    @staticmethod
    async def borrow(session, isbn, reverse: bool = False):
        book: BookDB = await BookDB.get_by_id(session, isbn, False)

        if book:
            book.available = 0 + reverse
            await session.commit()
            return True
        return False