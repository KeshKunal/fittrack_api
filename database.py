from sqlmodel import create_engine
from sqlmodel import Session

# The database file will be named "database.db" in the same directory
sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

# This is an argument needed only for SQLite
connect_args = {"check_same_thread": False}

# The engine is the main point of communication with the database
engine = create_engine(sqlite_url, echo=True, connect_args=connect_args)

def get_session():
    with Session(engine) as session:
        yield session
