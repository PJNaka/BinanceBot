# backend/db_setup.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
# Import from config later for actual URL
# from .config import DATABASE_URL 

# Placeholder URL, will be replaced by config value
SQLALCHEMY_DATABASE_URL = "mysql+mysqlclient://user:password@localhost/dbname_placeholder"
# In a real app, load this from config.py:
# from .config import DATABASE_URL
# SQLALCHEMY_DATABASE_URL = DATABASE_URL

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
