import os
import datetime

from .db import Base
from dotenv import load_dotenv
from sqlalchemy import BigInteger, Column, DateTime, Integer, Text, Enum, Boolean, desc, insert, select
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum

load_dotenv()

BORROWED_DAYS = int(os.environ["BORROWED_DAYS"])

class WarningType(str, PyEnum):
    VERBAL      = "VERBAL"  
    BLACKLIST   = "BLACKLIST"
    
class WarningDB(Base):
    __tablename__ = 'warnings'
    id = Column(Integer, primary_key=True, autoincrement=True)
    patron_id = Column(BigInteger, nullable=False)
    librarian_id = Column(BigInteger, nullable=False)
    status = Column(Enum(WarningType), default=WarningType.VERBAL)
    remarks = Column(Text, nullable=True)
    datetime = Column(DateTime, default=lambda: datetime.datetime.now())  # WIB local time
    expired_datetime = Column(DateTime, nullable=True, default=None)
    fine = Column(Integer, nullable=False)
    expired = Column(Boolean, default=False)  # was Integer; PostgreSQL strict bool

    @staticmethod
    async def get_by_id(session, id):
        return (await session.execute(select(WarningDB).where(WarningDB.id == id))).scalar()

    @staticmethod
    async def create(session, patron_id, librarian_id, status, remarks, fine, expired):
        warning = WarningDB(
            patron_id=patron_id,
            librarian_id=librarian_id,
            status=status,
            remarks=remarks,
            fine=fine,
            datetime=datetime.datetime.now(),
            expired=expired
        )

        session.add(warning)   
        await session.commit()

        return await WarningDB.get_latest(session)

    @staticmethod
    async def get_latest(session):
        result = await session.execute(
            select(WarningDB)
            .order_by(desc(WarningDB.datetime)).limit(1)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_active_warnings(session, patron_id):
        return (await session.execute(
            select(WarningDB)
            .where(WarningDB.patron_id == patron_id)
            .where(WarningDB.expired == False)
        )).scalars().all()
    
    @staticmethod
    async def get_total_active_warnings(session, patron_id):
        return len((await WarningDB.get_active_warnings(session, patron_id)))
    
    @staticmethod
    async def expire(session, id):
        warning = await WarningDB.get_by_id(session, id)
        warning.expired = True
        warning.expired_datetime = datetime.datetime.now()
        await session.commit()
        return True