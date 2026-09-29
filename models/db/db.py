import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()

database_url = os.environ.get("DATABASE_URL", "")

# Ensure the asyncpg driver is specified for SQLAlchemy
if database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
elif database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)

# Remove prisma parameter if present
database_url = database_url.replace("?pgbouncer=true", "")

engine = create_async_engine(
    database_url,
    echo=True,
    connect_args={
        "prepared_statement_cache_size": 0,
        "statement_cache_size": 0,
        "ssl": "require",
    }
)
Base = declarative_base()
AsyncSessionLocal = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)