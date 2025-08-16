from sqlmodel import create_engine
from sqlmodel import Session, create_engine
import os

DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    print("DATABASE_URL not found, using local SQLite database.")
    sqlite_file_name = "database.db"
    sqlite_url = f"sqlite:///{sqlite_file_name}"
    connect_args = {"check_same_thread": False}
    engine = create_engine(sqlite_url, echo=True, connect_args=connect_args)
else:
    print("Connecting to PostgreSQL database.")
    engine = create_engine(DATABASE_URL)

def get_session():
    with Session(engine) as session:
        yield session